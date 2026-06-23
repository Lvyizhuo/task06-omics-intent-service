# 组学智能体意图识别服务

## 项目简介

本项目是"农业大模型"组学智能体的二次意图识别服务，负责将用户请求路由到正确的下游任务接口。

## 与 PlantCaduceus 的关系

本项目是 PlantCaduceus 的**上游调度服务**：

```
用户 → 主智能体 → [本服务:8010] → PlantCAD2推理服务:8005
                                 → EVO2转发接口:8666
```

- **PlantCaduceus** (`/Users/lvyizhuo/project/i/PlantCaduceus`)：DNA 模型推理服务，提供 `/embeddings`、`/variant-score`、`/masked-predict`、`/predict` 等接口
- **本服务** (`/Users/lvyizhuo/project/i/task06-omics-intent-service`)：意图识别 + 参数提取 + 调度转发

两个项目**无代码耦合**，仅通过 HTTP 通信。

## 技术栈

- FastAPI + Uvicorn
- OpenAI SDK（兼容阿里云百炼 qwen-plus-latest）
- httpx（异步 HTTP 客户端）
- loguru（日志）

## 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| 路由层 | `app/routers/intent.py` | 接收请求，按置信度分发 |
| 意图识别 | `app/services/intent_recognizer.py` | 调用 LLM 识别用户意图 |
| 参数提取 | `app/services/param_extractor.py` | 从用户输入提取 API 参数 |
| 接口调用 | `app/services/api_caller.py` | 调用 PlantCAD2/EVO2 下游接口 |
| 提示词 | `app/prompts/` | 系统提示词 + 任务过滤提示词 |
| 配置 | `app/config.py` | 环境变量配置 |

## 启动方式

```bash
export LLM_API_KEY="your-api-key"
uvicorn app.main:app --host 0.0.0.0 --port 8010
```

## 下游服务依赖

| 服务 | 地址 | 说明 |
|------|------|------|
| PlantCAD2 | http://localhost:8005 | DNA 模型推理（7个LoRA任务 + 3个基础功能） |
| EVO2 | http://36.137.205.153:8666 | 基因序列预测生成 |
| 阿里云百炼 | https://dashscope.aliyuncs.com/compatible-mode/v1 | LLM 服务 |

## 支持的任务（11个）

- **EVO2 (101)**：基因序列预测生成
- **PlantCAD2 (201-210)**：嵌入提取、变异打分、掩码预测、ACR预测(3种)、表达量预测(2种)、翻译效率预测(2种)
