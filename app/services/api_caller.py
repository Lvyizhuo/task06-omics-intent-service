"""
PlantCAD2 和 EVO2 接口调用层

负责调用下游推理服务的各个接口，处理参数映射和错误处理。

PlantCAD2 已统一使用 /report 接口（POST /report），支持 type 字段区分：
  - type=embedding      → 嵌入提取       (201)
  - type=variant_score  → 变异打分       (202)
  - type=masked_predict → 掩码预测       (203)
  - type=predict        → LoRA 任务预测  (204-210)
"""

import httpx
from typing import Optional, Dict, Any
from loguru import logger

from app.config import settings
from app.prompts.task_prompts import TASK_NAME_MAP

# 任务ID到接口路径和参数的映射
# PlantCAD2 统一使用 /report 端点，通过 type 字段区分推理类型
TASK_API_MAP = {
    101: {"endpoint": "/api/v1/generate", "service": "evo2"},
    201: {"endpoint": "/report", "type": "embedding", "service": "plantcad2"},
    202: {"endpoint": "/report", "type": "variant_score", "service": "plantcad2"},
    203: {"endpoint": "/report", "type": "masked_predict", "service": "plantcad2"},
    204: {"endpoint": "/report", "type": "predict", "task_param": "acr_arabidopsis", "service": "plantcad2"},
    205: {"endpoint": "/report", "type": "predict", "task_param": "acr_nine_species", "service": "plantcad2"},
    206: {"endpoint": "/report", "type": "predict", "task_param": "acr_cell_type", "service": "plantcad2"},
    207: {"endpoint": "/report", "type": "predict", "task_param": "expression_on_off", "service": "plantcad2"},
    208: {"endpoint": "/report", "type": "predict", "task_param": "expression_absolute", "service": "plantcad2"},
    209: {"endpoint": "/report", "type": "predict", "task_param": "translation_on_off", "service": "plantcad2"},
    210: {"endpoint": "/report", "type": "predict", "task_param": "translation_absolute", "service": "plantcad2"},
}


def get_service_base_url(service: str) -> str:
    """获取服务基础URL"""
    if service == "evo2":
        return settings.evo2_base_url
    elif service == "plantcad2":
        return settings.plantcad2_base_url
    else:
        raise ValueError(f"未知服务: {service}")


def build_request_body(task_id: int, params: Dict[str, Any],
                       task_param: Optional[str] = None,
                       api_type: Optional[str] = None) -> Dict[str, Any]:
    """
    根据任务ID构建请求体

    Args:
        task_id: 任务ID
        params: LLM提取的参数
        task_param: LoRA任务的task参数值
        api_type: 推理类型（仅 PlantCAD2 /report 接口使用）

    Returns:
        请求体字典
    """
    request_body = {}

    # ── EVO2 基因序列预测生成 ──
    if task_id == 101:
        request_body["prompt"] = params.get("prompt") or params.get("sequence", "")
        # EVO2 默认参数（客户要求），所有参数必须是 string 类型
        request_body["numTokens"] = str(params.get("numTokens", "200"))
        request_body["temperature"] = str(params.get("temperature", "0.6"))
        request_body["topK"] = str(params.get("topK", "4"))
        request_body["topP"] = str(params.get("topP", "0.6"))
        request_body["showLogits"] = str(params.get("showLogits", "0"))

    # ── PlantCAD2 统一 /report 接口 ──
    else:
        request_body["type"] = api_type
        # U→T 转换：兼容 mRNA 序列（翻译任务中用户可能输入 U）
        request_body["sequence"] = params.get("sequence", "").replace('U', 'T')

        if api_type == "embedding":               # 201 嵌入提取
            if "normalize" in params:
                request_body["normalize"] = params["normalize"]

        elif api_type == "variant_score":         # 202 变异打分
            # 注意：/report 接口使用 1-based 位置，与用户习惯一致，直接使用
            position = params.get("position")
            if position is not None:
                request_body["position"] = int(position)
            request_body["ref_allele"] = params.get("ref_allele")
            request_body["alt_alleles"] = params.get("alt_alleles")

        elif api_type == "masked_predict":        # 203 掩码预测
            # 同样 1-based 位置，直接使用
            positions = params.get("positions")
            if positions is not None:
                request_body["positions"] = [int(p) for p in positions]

        elif api_type == "predict":               # 204-210 LoRA 任务
            request_body["task"] = task_param

    return request_body


async def call_downstream_api(task_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    调用下游接口

    Args:
        task_id: 任务ID (101, 201-210)
        params: LLM提取的参数

    Returns:
        接口响应结果

    Raises:
        ValueError: 任务ID无效
        httpx.HTTPStatusError: 接口返回错误状态码
        httpx.TimeoutException: 请求超时
    """
    if task_id not in TASK_API_MAP:
        raise ValueError(f"无效的任务ID: {task_id}")

    api_config = TASK_API_MAP[task_id]
    endpoint = api_config["endpoint"]
    task_param = api_config.get("task_param")
    api_type = api_config.get("type")  # PlantCAD2 /report 接口的 type 字段
    service = api_config["service"]

    # 构建请求体（传入 api_type 用于 /report 接口）
    request_body = build_request_body(task_id, params, task_param, api_type)

    # 获取服务URL
    base_url = get_service_base_url(service)
    url = f"{base_url}{endpoint}"

    logger.info(f"调用下游接口 | task_id={task_id} service={service} endpoint={endpoint}")
    logger.debug(f"请求URL: {url}")
    logger.debug(f"请求参数: {request_body}")

    # 带重试的请求
    last_error = None
    for attempt in range(settings.max_retries):
        try:
            async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
                response = await client.post(url, json=request_body)
                response.raise_for_status()

                result = response.json()
                logger.info(f"接口调用成功 | task_id={task_id} attempt={attempt + 1}")
                logger.debug(f"响应结果: {result}")
                return result

        except httpx.TimeoutException as e:
            last_error = e
            logger.warning(f"接口调用超时 | task_id={task_id} attempt={attempt + 1}/{settings.max_retries}")
        except httpx.HTTPStatusError as e:
            last_error = e
            logger.warning(f"接口调用错误 | task_id={task_id} status={e.response.status_code} attempt={attempt + 1}/{settings.max_retries}")
            # 4xx错误不重试
            if 400 <= e.response.status_code < 500:
                raise
        except Exception as e:
            last_error = e
            logger.warning(f"接口调用异常 | task_id={task_id} error={str(e)} attempt={attempt + 1}/{settings.max_retries}")

    # 所有重试都失败
    logger.error(f"接口调用最终失败 | task_id={task_id}")
    raise last_error


def format_result_for_user(task_id: int, result: Dict[str, Any]) -> str:
    """
    将接口返回结果格式化为用户可读的消息

    PlantCAD2 新 /report 接口返回格式为 {type, result, markdown}，
    内层 result 字段才是原始推理数据，此处自动提取。

    Args:
        task_id: 任务ID
        result: 接口返回结果

    Returns:
        格式化后的消息
    """
    task_name = TASK_NAME_MAP.get(task_id, "未知任务")

    # PlantCAD2 /report 接口的内层 result 包含原始推理数据
    # EVO2 直接返回 flat dict，用 .get("result", result) 透明兼容
    inner = result.get("result", result) if task_id != 101 else result

    # EVO2 基因序列预测生成
    if task_id == 101:
        generated = result.get("generated_sequence", "")
        if generated:
            preview = generated[:50] + "..." if len(generated) > 50 else generated
            return f"已生成后续序列（长度：{len(generated)}bp）：{preview}"
        return "基因序列预测生成完成"

    # 嵌入提取
    elif task_id == 201:
        shape = inner.get("shape", [])
        if shape:
            return f"已成功提取嵌入向量，形状为 {shape[0]}×{shape[1]}"
        return "嵌入提取完成"

    # 变异打分
    elif task_id == 202:
        scores = inner.get("scores", {})
        if scores:
            score_str = ", ".join([f"{k}: {v:.2f}" for k, v in scores.items()])
            return f"变异打分结果：{score_str}"
        return "变异打分完成"

    # 掩码预测
    elif task_id == 203:
        predictions = inner.get("predictions", {})
        if predictions:
            return f"已完成 {len(predictions)} 个位置的碱基概率预测"
        return "掩码预测完成"

    # 二分类任务 (204, 205, 207, 209)
    elif task_id in [204, 205, 207, 209]:
        prediction = inner.get("prediction", "")
        probability = inner.get("probability", 0)
        if prediction:
            return f"{task_name}结果：{prediction}（概率：{probability:.1%}）"
        return f"{task_name}完成"

    # 多标签分类任务 (206)
    elif task_id == 206:
        num_labels = inner.get("num_labels", 0)
        return f"细胞类型ACR预测完成，共 {num_labels} 个细胞类型的概率"

    # 回归任务 (208, 210)
    elif task_id in [208, 210]:
        prediction = inner.get("prediction", 0)
        if prediction is not None:
            return f"{task_name}结果：{prediction:.4f}"
        return f"{task_name}完成"

    return f"{task_name}已完成"
