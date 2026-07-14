"""
意图识别路由

处理意图识别请求，根据置信度执行不同的处理逻辑。
"""

from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import Dict, Any

from app.schemas.requests import IntentRequest, IntentResponse, SuggestedTask, AvailableTask, ErrorInfo
from app.services.intent_recognizer import recognize_intent
from app.services.param_extractor import extract_params
from app.services.api_caller import call_downstream_api, format_result_for_user, TASK_API_MAP
from app.prompts.task_prompts import TASK_NAME_MAP, TASK_MODEL_MAP, TASK_DETAILS

router = APIRouter(prefix="/intent", tags=["意图识别"])

# 所有可能的参数字段（完整列表）
ALL_PARAM_FIELDS = [
    "sequence",      # DNA序列（PlantCAD2）
    "prompt",        # DNA序列（EVO2）
    "position",      # 变异位置
    "ref_allele",    # 参考碱基
    "alt_alleles",   # 变异碱基列表
    "positions",     # 预测位置列表
    "numTokens",     # 生成长度（EVO2）
    "temperature",   # 温度（EVO2）
    "topK",          # topK参数（EVO2）
    "topP",          # topP参数（EVO2）
    "showLogits",    # 显示logits（EVO2）
    "normalize",     # 是否归一化
]


def fill_all_params(extracted_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    用所有可能的字段填充params，未提取到的字段设为None

    Args:
        extracted_params: 已提取的参数

    Returns:
        包含所有字段的参数字典
    """
    full_params = {}
    for field in ALL_PARAM_FIELDS:
        full_params[field] = extracted_params.get(field, None)
    return full_params


def generate_dynamic_guide(task_id: int, extracted_params: Dict[str, Any]) -> str:
    """
    根据任务需要的参数和用户已提供的参数，动态生成引导提示

    Args:
        task_id: 任务ID
        extracted_params: 已提取的参数

    Returns:
        动态生成的引导提示
    """
    task_detail = TASK_DETAILS.get(task_id, {})
    required_fields = task_detail.get("data_fields", [])
    task_name = task_detail.get("name", "未知任务")

    if not required_fields:
        return task_detail.get("guide_message", "请提供必要的参数")

    # 参数中文名映射
    param_names = {
        "prompt": "DNA序列",
        "sequence": "DNA序列",
        "numTokens": "生成长度(numTokens)",
        "temperature": "温度(temperature)",
        "topK": "topK参数",
        "topP": "topP参数",
        "showLogits": "显示logits(showLogits)",
        "normalize": "是否归一化(normalize)",
        "position": "变异位置(position)",
        "ref_allele": "参考碱基(ref_allele)",
        "alt_alleles": "变异碱基(alt_alleles)",
        "positions": "预测位置列表(positions)",
    }

    # 检查哪些参数已提供，哪些缺少
    provided = []
    missing = []

    for field in required_fields:
        if field in extracted_params and extracted_params[field] is not None:
            provided.append(param_names.get(field, field))
        else:
            # 可选参数不算缺少
            if field not in ["numTokens", "temperature", "topK", "topP", "showLogits", "normalize"]:
                missing.append(param_names.get(field, field))

    # 生成提示
    if not missing:
        return f"已识别到您需要进行{task_name}，参数完整。"

    if provided:
        return f"已识别到您需要进行{task_name}，已提取：{'、'.join(provided)}。请补充：{'、'.join(missing)}"
    else:
        return f"已识别到您需要进行{task_name}，请提供：{'、'.join(missing)}"


@router.post("/recognize", response_model=IntentResponse)
async def recognize_user_intent(request: IntentRequest):
    """
    意图识别接口

    接收用户输入，通过大模型进行意图识别，返回三种置信度场景的结果：

    - **高置信度 (high)**: 直接提取参数并调用下游接口，返回计算结果
    - **中置信度 (medium)**: 返回推荐任务列表和引导消息
    - **低置信度 (low)**: 返回兜底引导和所有可用任务列表
    """
    logger.info(f"收到意图识别请求 | session_id={request.session_id}")
    logger.info(f"用户输入: {request.user_input[:200]}...")

    try:
        # 1. 调用LLM进行意图识别
        intent_result = await recognize_intent(request.user_input)
        confidence = intent_result.get("confidence", "low")

        # 2. 根据置信度处理
        if confidence == "high":
            return await handle_high_confidence(intent_result)
        elif confidence == "medium":
            return await handle_medium_confidence(intent_result, request.user_input)
        else:
            return await handle_low_confidence(intent_result, request.user_input)

    except Exception as e:
        logger.error(f"意图识别处理异常: {str(e)}", exc_info=True)
        return IntentResponse(
            confidence="low",
            guide_message="抱歉，处理过程中出现错误，请稍后重试。您可以直接选择需要的任务。",
            available_tasks=[
                AvailableTask(task_id=tid, task_name=details["name"], model=details["model"], required_fields=details.get("data_fields", []))
                for tid, details in TASK_DETAILS.items()
            ],
            error=ErrorInfo(code=1001, message="意图识别失败", detail=str(e)),
        )


async def handle_high_confidence(intent_result: dict) -> IntentResponse:
    """
    处理高置信度场景

    Args:
        intent_result: 意图识别结果

    Returns:
        包含计算结果的响应
    """
    task_id = intent_result.get("task_id")
    task_name = intent_result.get("task_name", TASK_NAME_MAP.get(task_id, "未知任务"))
    model = intent_result.get("model", TASK_MODEL_MAP.get(task_id, "未知模型"))
    params = intent_result.get("params", {})

    logger.info(f"高置信度场景 | task_id={task_id} task_name={task_name}")

    # 验证任务ID
    if task_id not in TASK_API_MAP:
        logger.warning(f"无效的任务ID: {task_id}")
        return IntentResponse(
            confidence="low",
            guide_message=f"识别到的任务ID({task_id})无效，请重新选择任务。",
            available_tasks=[
                AvailableTask(task_id=tid, task_name=details["name"], model=details["model"], required_fields=details.get("data_fields", []))
                for tid, details in TASK_DETAILS.items()
            ],
            error=ErrorInfo(code=1001, message="任务ID无效", detail=f"task_id={task_id}不在支持范围内"),
        )

    # 检查参数是否完整
    if not params or not (params.get("sequence") or params.get("prompt")):
        logger.info("参数不完整，降级为中置信度推荐")
        # 生成动态提示
        dynamic_guide = generate_dynamic_guide(task_id, params or {})
        # 填充完整的字段结构
        full_params = fill_all_params(params or {})
        # 降级为中置信度
        return IntentResponse(
            confidence="medium",
            suggested_tasks=[
                SuggestedTask(
                    task_id=task_id,
                    task_name=task_name,
                    model=model,
                    description=TASK_DETAILS.get(task_id, {}).get("description", ""),
                    guide_message=dynamic_guide,
                    required_fields=TASK_DETAILS.get(task_id, {}).get("data_fields", []),
                )
            ],
            guide_message=f"已识别到您需要进行{task_name}，但缺少必要的数据。{dynamic_guide}",
            params=full_params,
        )

    # 调用下游接口
    try:
        result = await call_downstream_api(task_id, params)
        guide_message = format_result_for_user(task_id, result)

        # EVO2 任务提示信息
        evo2_tip = ""
        if task_id == 101:
            evo2_tip = " 当前结果基于默认参数计算（numTokens=200, temperature=0.6, topK=4, topP=0.6, showLogits=0），如需自定义参数，请手动选择EVO2任务并指定参数。"

        # 提取 PlantCAD2 /report 接口返回的 markdown 报告
        markdown_report = result.get("markdown") if task_id != 101 else None

        # 填充完整的字段结构
        full_params = fill_all_params(params)

        return IntentResponse(
            confidence="high",
            task_id=task_id,
            task_name=task_name,
            model=model,
            params=full_params,
            result=result,
            markdown=markdown_report,
            guide_message=f"已为您完成{task_name}。{guide_message}{evo2_tip}",
        )

    except Exception as e:
        logger.error(f"下游接口调用失败 | task_id={task_id} error={str(e)}")

        # 提取错误详情
        error_detail = str(e)
        error_message = "下游接口调用失败"

        # 如果是 HTTP 400 错误，提取具体原因
        if hasattr(e, 'response') and e.response.status_code == 400:
            try:
                error_body = e.response.json()
                if 'detail' in error_body:
                    error_detail = error_body['detail']
                    error_message = "参数验证失败"
            except Exception:
                pass

        # 调用失败，降级为推荐任务
        # 填充完整的字段结构
        full_params = fill_all_params(params)

        return IntentResponse(
            confidence="medium",
            suggested_tasks=[
                SuggestedTask(
                    task_id=task_id,
                    task_name=task_name,
                    model=model,
                    description=TASK_DETAILS.get(task_id, {}).get("description", ""),
                    guide_message=TASK_DETAILS.get(task_id, {}).get("guide_message", "请提供DNA序列"),
                    required_fields=TASK_DETAILS.get(task_id, {}).get("data_fields", []),
                )
            ],
            guide_message=f"已识别到您需要进行{task_name}，但参数有误：{error_detail}",
            params=full_params,
            error=ErrorInfo(code=1003, message=error_message, detail=error_detail),
        )


async def handle_medium_confidence(intent_result: dict, user_input: str) -> IntentResponse:
    """
    处理中置信度场景

    Args:
        intent_result: 意图识别结果
        user_input: 用户原始输入

    Returns:
        包含推荐任务的响应
    """
    suggested_tasks_raw = intent_result.get("suggested_tasks", [])
    guide_message = intent_result.get("guide_message", "您想进行哪种分析？")

    # 只提取一次参数（使用第一个推荐任务的ID）
    extracted_params = {}
    if suggested_tasks_raw:
        first_task = suggested_tasks_raw[0]
        if isinstance(first_task, dict):
            first_task_id = first_task.get("task_id", 201)  # 默认使用201
            try:
                extracted_params = await extract_params(user_input, first_task_id)
                if extracted_params:
                    logger.info(f"中置信度提取参数 | task_id={first_task_id} params={list(extracted_params.keys())}")
            except Exception as e:
                logger.warning(f"中置信度参数提取失败 | task_id={first_task_id} error={str(e)}")

    # 转换为SuggestedTask模型
    suggested_tasks = []
    for task in suggested_tasks_raw:
        if isinstance(task, dict):
            task_id = task.get("task_id", 0)
            task_name = task.get("task_name", "")
            model = task.get("model", "")

            # 用已提取的参数生成动态提示
            if extracted_params:
                dynamic_guide = generate_dynamic_guide(task_id, extracted_params)
                task["guide_message"] = dynamic_guide

            suggested_tasks.append(SuggestedTask(
                task_id=task_id,
                task_name=task_name,
                model=model,
                description=task.get("description", ""),
                guide_message=task.get("guide_message", ""),
                required_fields=task.get("required_fields", []),
            ))

    logger.info(f"中置信度场景 | 推荐任务数={len(suggested_tasks)}")

    # 填充完整的字段结构
    full_params = fill_all_params(extracted_params)

    return IntentResponse(
        confidence="medium",
        suggested_tasks=suggested_tasks,
        guide_message=guide_message,
        params=full_params,
    )


async def handle_low_confidence(intent_result: dict, user_input: str) -> IntentResponse:
    """
    处理低置信度场景

    Args:
        intent_result: 意图识别结果
        user_input: 用户原始输入

    Returns:
        包含所有可用任务的响应
    """
    guide_message = intent_result.get("guide_message", "")
    available_tasks_raw = intent_result.get("available_tasks", [])

    # 尝试从用户输入中提取通用数据（如DNA序列）
    extracted_params = {}
    try:
        from app.services.param_extractor import extract_params_by_regex
        generic_params = extract_params_by_regex(user_input, 0)  # task_id=0 表示通用提取
        if generic_params:
            extracted_params = generic_params
            logger.info(f"低置信度提取通用参数 | params={list(generic_params.keys())}")
    except Exception as e:
        logger.warning(f"低置信度参数提取失败 | error={str(e)}")

    # 转换为AvailableTask模型
    available_tasks = []
    for task in available_tasks_raw:
        if isinstance(task, dict):
            available_tasks.append(AvailableTask(
                task_id=task.get("task_id", 0),
                task_name=task.get("task_name", ""),
                model=task.get("model", ""),
                required_fields=task.get("required_fields", []),
            ))

    logger.info(f"低置信度场景 | 可用任务数={len(available_tasks)}")

    # 如果提取到了序列，在引导消息中提示
    if extracted_params.get("sequence") or extracted_params.get("prompt"):
        sequence = extracted_params.get("sequence") or extracted_params.get("prompt", "")
        guide_message += f"\n\n已从您的输入中识别到DNA序列（长度{len(sequence)}bp），选择任务后可直接使用。"

    # 填充完整的字段结构
    full_params = fill_all_params(extracted_params)

    return IntentResponse(
        confidence="low",
        guide_message=guide_message,
        available_tasks=available_tasks,
        params=full_params,
    )
