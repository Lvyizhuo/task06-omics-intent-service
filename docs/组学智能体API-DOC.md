# 组学智能体意图识别服务 - 接口文档

## 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://<服务器IP>:8010` |
| Content-Type | `application/json` |

---

## 1. 意图识别

**POST** `/intent/recognize`

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_input | string | 是 | 用户输入文本（1-10000字符）|
| session_id | string | 否 | 会话ID |

### 请求示例

```json
{
  "user_input": "帮我分析这个基因序列的嵌入向量: ATGCGATCGATCGATCG",
  "session_id": "session_001"
}
```

### 响应参数

| 字段 | 类型 | 说明 |
|------|------|------|
| confidence | string | 置信度：`high` / `medium` / `low` |
| task_id | int | 任务ID（high时返回）|
| task_name | string | 任务名称（high时返回）|
| model | string | 使用的模型（high时返回）|
| params | object | 提取的参数（high时返回）|
| result | object | 计算结果（high时返回）|
| suggested_tasks | array | 推荐任务列表（medium时返回）|
| available_tasks | array | 全部任务列表（low时返回）|
| guide_message | string | 引导消息 |
| error | object | 错误信息 |

---

### 响应示例 - 高置信度

```json
{
  "confidence": "high",
  "task_id": 201,
  "task_name": "嵌入提取",
  "model": "PlantCAD2",
  "params": {
    "sequence": "ATGCGATCGATCGATCG"
  },
  "result": {
    "embeddings": [[0.123, 0.456, 0.789]]
  },
  "guide_message": "已完成嵌入提取任务",
  "suggested_tasks": null,
  "available_tasks": null,
  "error": null
}
```

### 响应示例 - 中置信度

```json
{
  "confidence": "medium",
  "task_id": null,
  "task_name": null,
  "model": null,
  "params": null,
  "result": null,
  "suggested_tasks": [
    {
      "task_id": 207,
      "task_name": "表达量预测-开/关",
      "model": "PlantCAD2",
      "description": "预测基因是否表达",
      "guide_message": "请提供DNA序列"
    },
    {
      "task_id": 208,
      "task_name": "表达量预测-绝对值",
      "model": "PlantCAD2",
      "description": "预测基因表达水平",
      "guide_message": "请提供DNA序列"
    }
  ],
  "guide_message": "您想预测基因是否表达（开/关），还是预测具体的表达水平？请提供DNA序列。",
  "available_tasks": null,
  "error": null
}
```

### 响应示例 - 低置信度

```json
{
  "confidence": "low",
  "task_id": null,
  "task_name": null,
  "model": null,
  "params": null,
  "result": null,
  "suggested_tasks": null,
  "guide_message": "您好！请选择您需要的任务，并提供DNA序列。",
  "available_tasks": [
    {"task_id": 101, "task_name": "基因序列预测生成", "model": "EVO2"},
    {"task_id": 201, "task_name": "嵌入提取", "model": "PlantCAD2"},
    {"task_id": 202, "task_name": "变异打分", "model": "PlantCAD2"},
    {"task_id": 203, "task_name": "掩码预测", "model": "PlantCAD2"},
    {"task_id": 204, "task_name": "ACR预测-拟南芥", "model": "PlantCAD2"},
    {"task_id": 205, "task_name": "ACR预测-水稻", "model": "PlantCAD2"},
    {"task_id": 206, "task_name": "ACR预测-大豆", "model": "PlantCAD2"},
    {"task_id": 207, "task_name": "表达量预测-开/关", "model": "PlantCAD2"},
    {"task_id": 208, "task_name": "表达量预测-绝对值", "model": "PlantCAD2"},
    {"task_id": 209, "task_name": "翻译效率预测-玉米", "model": "PlantCAD2"},
    {"task_id": 210, "task_name": "翻译效率预测-水稻", "model": "PlantCAD2"}
  ],
  "error": null
}
```

### 响应示例 - 错误

```json
{
  "confidence": "medium",
  "task_id": null,
  "task_name": null,
  "model": null,
  "params": null,
  "result": null,
  "suggested_tasks": [
    {
      "task_id": 201,
      "task_name": "嵌入提取",
      "model": "PlantCAD2",
      "description": "提取DNA序列的嵌入向量",
      "guide_message": "请提供DNA序列"
    }
  ],
  "guide_message": "已识别到您需要进行嵌入提取，但接口调用暂时失败。请稍后重试。",
  "available_tasks": null,
  "error": {
    "code": 1003,
    "message": "下游接口调用失败",
    "detail": "Connection timeout"
  }
}
```

---

## 2. 健康检查

**GET** `/health`

### 响应示例

```json
{
  "status": "ok",
  "service": "omics-intent-service"
}
```

---

## 3. 错误码

| 错误码 | 说明 |
|--------|------|
| 1001 | LLM服务调用失败 |
| 1002 | 参数提取失败 |
| 1003 | 下游接口调用失败 |
| 1004 | 参数验证失败 |

---

## 4. 任务ID对照表

| ID | 任务名称 | 模型 |
|----|----------|------|
| 101 | 基因序列预测生成 | EVO2 |
| 201 | 嵌入提取 | PlantCAD2 |
| 202 | 变异打分 | PlantCAD2 |
| 203 | 掩码预测 | PlantCAD2 |
| 204 | ACR预测-拟南芥 | PlantCAD2 |
| 205 | ACR预测-水稻 | PlantCAD2 |
| 206 | ACR预测-大豆 | PlantCAD2 |
| 207 | 表达量预测-开/关 | PlantCAD2 |
| 208 | 表达量预测-绝对值 | PlantCAD2 |
| 209 | 翻译效率预测-玉米 | PlantCAD2 |
| 210 | 翻译效率预测-水稻 | PlantCAD2 |
