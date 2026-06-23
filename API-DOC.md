# 组学智能体意图识别服务 - 前端接口文档

## 1. 服务概述

本服务为组学智能体提供意图识别能力，将用户的自然语言输入解析为具体的任务指令，并根据置信度返回不同粒度的响应结果。

## 2. 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://<服务器IP>:8010` |
| 协议 | HTTP/1.1 |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |

### 请求头

```
Content-Type: application/json
```

---

## 3. 接口列表

### 3.1 意图识别接口

#### 基本信息

| 项目 | 值 |
|------|-----|
| 接口路径 | `POST /intent/recognize` |
| 接口说明 | 接收用户自然语言输入，返回意图识别结果 |

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_input | string | ✅ | 用户输入的问题文本（1-10000字符）|
| session_id | string | ❌ | 会话ID，用于上下文关联（可选）|

#### 请求示例

```json
{
  "user_input": "帮我分析这个基因序列的嵌入向量: ATGCGATCGATCGATCG",
  "session_id": "user_123_session_456"
}
```

#### 响应结构

服务根据置信度返回三种不同的响应结构：

---

#### 场景一：高置信度 (confidence = "high")

**触发条件**：用户意图明确，能直接匹配到单一任务

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| confidence | string | 固定值 `"high"` |
| task_id | int | 任务ID（见附录任务列表）|
| task_name | string | 任务名称 |
| model | string | 使用的模型名称 |
| params | object | 从用户输入中提取的参数 |
| result | object | 下游接口返回的计算结果 |
| guide_message | string | 引导消息 |
| error | object | 错误信息（仅在调用失败时出现）|

**响应示例（成功）**：

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
    "embeddings": [[0.123, 0.456, ...], ...]
  },
  "guide_message": "已完成嵌入提取任务",
  "suggested_tasks": null,
  "available_tasks": null,
  "error": null
}
```

**响应示例（调用失败，降级为中置信度）**：

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
      "description": "提取DNA序列的嵌入向量表示",
      "guide_message": "请提供完整的DNA序列"
    }
  ],
  "guide_message": "已识别到您需要进行嵌入提取，但接口调用暂时失败。请稍后重试或手动调用接口。",
  "available_tasks": null,
  "error": {
    "code": 1003,
    "message": "下游接口调用失败",
    "detail": "Connection timeout"
  }
}
```

---

#### 场景二：中置信度 (confidence = "medium")

**触发条件**：用户意图部分明确，需要进一步确认或补充信息

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| confidence | string | 固定值 `"medium"` |
| suggested_tasks | array | 推荐任务列表（3-5个）|
| guide_message | string | 引导用户下一步操作的消息 |

**suggested_tasks 数组元素**：

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | int | 任务ID |
| task_name | string | 任务名称 |
| model | string | 使用的模型 |
| description | string | 任务描述 |
| guide_message | string | 执行该任务需要的提示信息 |

**响应示例**：

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
      "description": "预测基因是否表达（开/关）",
      "guide_message": "请提供需要分析的DNA序列"
    },
    {
      "task_id": 208,
      "task_name": "表达量预测-绝对值",
      "model": "PlantCAD2",
      "description": "预测基因表达的具体水平值",
      "guide_message": "请提供需要分析的DNA序列"
    }
  ],
  "guide_message": "您想预测基因是否表达（开/关），还是预测具体的表达水平（绝对值）？请提供需要分析的DNA序列。",
  "available_tasks": null,
  "error": null
}
```

---

#### 场景三：低置信度 (confidence = "low")

**触发条件**：用户意图模糊或超出服务范围

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| confidence | string | 固定值 `"low"` |
| available_tasks | array | 所有可用任务列表（11个）|
| guide_message | string | 引导消息 |

**available_tasks 数组元素**：

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | int | 任务ID |
| task_name | string | 任务名称 |
| model | string | 使用的模型 |

**响应示例**：

```json
{
  "confidence": "low",
  "task_id": null,
  "task_name": null,
  "model": null,
  "params": null,
  "result": null,
  "suggested_tasks": null,
  "guide_message": "您好！我是组学智能体助手。请选择您需要执行的任务（如基因序列生成、变异打分、表达量预测等），并提供相应的DNA序列或参数数据。",
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

---

### 3.2 健康检查接口

#### 基本信息

| 项目 | 值 |
|------|-----|
| 接口路径 | `GET /health` |
| 接口说明 | 检查服务是否正常运行 |

#### 请求参数

无

#### 响应示例

```json
{
  "status": "ok",
  "service": "omics-intent-service"
}
```

---

## 4. 错误码说明

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 1001 | LLM 服务调用失败 | 检查 LLM 服务配置，稍后重试 |
| 1002 | 参数提取失败 | 用户输入可能不完整，引导用户补充信息 |
| 1003 | 下游接口调用失败 | PlantCAD2/EVO2 服务异常，稍后重试 |
| 1004 | 参数验证失败 | 检查参数格式（如DNA序列是否合法）|

---

## 5. 前端集成建议

### 5.1 响应处理流程

```javascript
async function handleUserInput(userInput) {
  const response = await fetch('/intent/recognize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput })
  });

  const data = await response.json();

  switch (data.confidence) {
    case 'high':
      // 直接展示计算结果
      showResult(data.result);
      break;

    case 'medium':
      // 展示推荐任务列表，让用户选择
      showTaskSuggestions(data.suggested_tasks, data.guide_message);
      break;

    case 'low':
      // 展示所有可用任务，引导用户选择
      showAllTasks(data.available_tasks, data.guide_message);
      break;
  }
}
```

### 5.2 UI 展示建议

| 置信度 | UI 行为 |
|--------|---------|
| high | 直接展示结果或进度条 |
| medium | 展示推荐任务卡片列表，用户点击选择 |
| low | 展示引导文案 + 全部任务列表供选择 |

### 5.3 错误处理

```javascript
if (data.error) {
  // 展示错误信息
  showError(data.error.message);

  // 如果有推荐任务，仍然展示
  if (data.suggested_tasks) {
    showTaskSuggestions(data.suggested_tasks);
  }
}
```

---

## 6. 附录：任务列表

| 任务ID | 任务名称 | 模型 | 所需参数 |
|--------|----------|------|----------|
| 101 | 基因序列预测生成 | EVO2 | prompt（初始序列）, length（生成长度）|
| 201 | 嵌入提取 | PlantCAD2 | sequence（DNA序列）|
| 202 | 变异打分 | PlantCAD2 | sequence, position, ref_allele, alt_allele |
| 203 | 掩码预测 | PlantCAD2 | sequence, position |
| 204 | ACR预测-拟南芥 | PlantCAD2 | sequence |
| 205 | ACR预测-水稻 | PlantCAD2 | sequence |
| 206 | ACR预测-大豆 | PlantCAD2 | sequence |
| 207 | 表达量预测-开/关 | PlantCAD2 | sequence |
| 208 | 表达量预测-绝对值 | PlantCAD2 | sequence |
| 209 | 翻译效率预测-玉米 | PlantCAD2 | sequence |
| 210 | 翻译效率预测-水稻 | PlantCAD2 | sequence |

---

## 7. 联系方式

如有问题，请联系后端开发团队。

---

*文档版本：v1.0*
*更新日期：2026-06-23*
