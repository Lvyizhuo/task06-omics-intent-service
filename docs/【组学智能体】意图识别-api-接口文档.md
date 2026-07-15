# 组学智能体意图识别服务 - 接口文档

## 基础信息

| 项目           | 值                     |
| ------------ | --------------------- |
| Base URL     | `http://<服务器IP>:8010` |
| Content-Type | `application/json`    |

---

## 0. 系统架构与服务调用流程

### 整体架构

```
用户 → 第一次意图识别（路由到组学智能体） → 组学意图识别[本服务 :8010] →
                                         → PlantCAD2 推理服务 :8005（统一 /report 接口）
                                         → EVO2 转发接口 :8666
```

### 调用流程说明

| 步骤     | 说明                            |
| ------ | ----------------------------- |
| ① 意图识别 | 调用本地 Qwen3 模型，识别用户意图并匹配任务     |
| ② 参数提取 | 从用户输入中提取任务所需的参数（如 DNA 序列、位置等） |
| ③ 下游调用 | **高置信度时**，自动调用对应下游服务的 HTTP 接口 |
| ④ 结果返回 | 将下游服务的返回结果包装后返回给用户            |

### 高置信度自动调用逻辑

当识别置信度为 **high** 时，服务会自动执行以下流程：

1. 验证 `task_id` 是否合法
2. 检查参数完整性（是否包含 `sequence` 或 `prompt`）
3. 调用对应的下游接口（PlantCAD2 或 EVO2）
4. 返回下游服务的计算结果

**若下游调用失败**，自动降级为 **medium** 置信度，返回错误信息和推荐任务。

---

## 1. 意图识别

**POST** `/intent/recognize`

### 请求参数

| 字段         | 类型     | 必填  | 说明                |
| ---------- | ------ | --- | ----------------- |
| user_input | string | 是   | 用户输入文本（1-10000字符） |
| session_id | string | 否   | 会话ID              |

### 请求示例

```json
{
  "user_input": "帮我分析这个基因序列的嵌入向量: ATGCGATCGATCGATCG",
  "session_id": "session_001"
}
```

### 响应参数

| 字段              | 类型     | 说明                            |
| --------------- | ------ | ----------------------------- |
| confidence      | string | 置信度：`high` / `medium` / `low` |
| task_id         | int    | 任务ID（high时返回）                 |
| task_name       | string | 任务名称（high时返回）                 |
| model           | string | 使用的模型（high时返回）                |
| params          | object | 提取的参数（high/medium/low时返回，包含所有可能的参数字段，未提取到的为null） |
| result          | object | 计算结果（high时返回，PlantCAD2任务含内层result和markdown） |
| markdown        | string | PlantCAD2自动生成的Markdown推理报告（high时返回，前端可直接渲染；EVO2任务为null） |
| suggested_tasks | array  | 推荐任务列表（medium时返回，每项含required_fields） |
| available_tasks | array  | 全部任务列表（low时返回，每项含required_fields） |
| guide_message   | string | 引导消息                          |
| error           | object | 错误信息                          |

---

### 响应示例 - 高置信度

```json
{
  "confidence": "high",
  "task_id": 202,
  "task_name": "变异打分",
  "model": "PlantCAD2",
  "params": {
    "sequence": "ACGTACGTACGT",
    "position": 5,
    "ref_allele": "A",
    "alt_alleles": ["G"],
    "normalize": null,
    "prompt": null,
    "positions": null,
    "numTokens": null,
    "temperature": null,
    "topK": null,
    "topP": null,
    "showLogits": null
  },
  "result": {
    "type": "variant_score",
    "result": {
      "scores": {"G": -0.80, "C": -0.76, "T": 0.77},
      "ref_prob": 0.246,
      "alt_probs": {"G": 0.110, "C": 0.115, "T": 0.529}
    },
    "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n..."
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n...",
  "guide_message": "已为您完成变异打分。变异打分结果：G: -0.80, C: -0.76, T: 0.77",
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
  "params": {
    "sequence": "ACGTACGTACGT",
    "normalize": null,
    "position": null,
    "positions": null,
    "prompt": null,
    "numTokens": null,
    "temperature": null,
    "topK": null,
    "topP": null,
    "showLogits": null
  },
  "result": null,
  "suggested_tasks": [
    {
      "task_id": 207,
      "task_name": "表达量预测-开/关",
      "model": "PlantCAD2",
      "description": "预测基因在叶片中是否表达",
      "guide_message": "请提供DNA序列，我将预测其在叶片中是否表达",
      "required_fields": ["sequence"]
    },
    {
      "task_id": 208,
      "task_name": "表达量预测-绝对值",
      "model": "PlantCAD2",
      "description": "预测基因在叶片中的表达水平",
      "guide_message": "请提供DNA序列，我将预测其在叶片中的表达水平",
      "required_fields": ["sequence"]
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
  "markdown": null,
  "suggested_tasks": null,
  "guide_message": "您好！请选择您需要的任务，并提供DNA序列。",
  "available_tasks": [
    {"task_id": 101, "task_name": "基因序列预测生成", "model": "EVO2", "required_fields": ["prompt", "numTokens", "temperature", "topK", "topP", "showLogits"]},
    {"task_id": 201, "task_name": "嵌入提取", "model": "PlantCAD2", "required_fields": ["sequence", "normalize"]},
    {"task_id": 202, "task_name": "变异打分", "model": "PlantCAD2", "required_fields": ["sequence", "position", "ref_allele", "alt_alleles"]},
    {"task_id": 203, "task_name": "掩码预测", "model": "PlantCAD2", "required_fields": ["sequence", "positions"]},
    {"task_id": 204, "task_name": "ACR预测-拟南芥", "model": "PlantCAD2", "required_fields": ["sequence"]},
    {"task_id": 205, "task_name": "ACR预测-九物种", "model": "PlantCAD2", "required_fields": ["sequence"]},
    {"task_id": 206, "task_name": "ACR预测-细胞类型", "model": "PlantCAD2", "required_fields": ["sequence"]},
    {"task_id": 207, "task_name": "表达量预测-开/关", "model": "PlantCAD2", "required_fields": ["sequence"]},
    {"task_id": 208, "task_name": "表达量预测-绝对值", "model": "PlantCAD2", "required_fields": ["sequence"]},
    {"task_id": 209, "task_name": "翻译效率预测-开/关", "model": "PlantCAD2", "required_fields": ["sequence"]},
    {"task_id": 210, "task_name": "翻译效率预测-绝对值", "model": "PlantCAD2", "required_fields": ["sequence"]}
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
  "params": {
    "sequence": "ACGTACGTACGT",
    "normalize": null,
    "position": null,
    ...
  },
  "result": null,
  "markdown": null,
  "suggested_tasks": [
    {
      "task_id": 201,
      "task_name": "嵌入提取",
      "model": "PlantCAD2",
      "description": "提取DNA序列每个位置的1536维向量表示",
      "guide_message": "请提供DNA序列（IUPAC碱基，最长8192bp），我将为您提取嵌入向量",
      "required_fields": ["sequence", "normalize"]
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

| 错误码  | 说明        | 触发场景                     |
| ---- | --------- | ------------------------ |
| 1001 | LLM服务调用失败 | Qwen3 模型不可用或超时           |
| 1002 | 参数提取失败    | LLM 未能从用户输入中提取到有效参数      |
| 1003 | 下游接口调用失败  | PlantCAD2/EVO2 接口返回错误或超时 |
| 1004 | 参数验证失败    | 参数格式不合法（如下游接口返回 400）     |

> **注意**：1003 和 1004 错误出现在 high 降级的 medium 置信度响应中，此时 `confidence` 为 `medium`，同时携带 `suggested_tasks` 和 `error` 字段。

---

## 4. 任务ID对照表

| ID  | 任务名称      | 模型        |
| --- | --------- | --------- |
| 101 | 基因序列预测生成  | EVO2      |
| 201 | 嵌入提取      | PlantCAD2 |
| 202 | 变异打分      | PlantCAD2 |
| 203 | 掩码预测      | PlantCAD2 |
| 204 | ACR预测-拟南芥 | PlantCAD2 |
| 205 | ACR预测-九物种 | PlantCAD2 |
| 206 | ACR预测-细胞类型 | PlantCAD2 |
| 207 | 表达量预测-开/关 | PlantCAD2 |
| 208 | 表达量预测-绝对值 | PlantCAD2 |
| 209 | 翻译效率预测-开/关 | PlantCAD2 |
| 210 | 翻译效率预测-绝对值 | PlantCAD2 |

---

## 5. 下游接口调用映射

> **说明**：高置信度场景下，本服务会自动将请求转发到下游推理服务的对应接口。以下是各任务 ID 对应的下游接口详情。

### 5.1 EVO2 接口（task_id=101）

| 项目   | 值                                                        |
| ---- | -------------------------------------------------------- |
| 下游地址 | `POST {EVO2_BASE_URL}/api/v1/generate`                   |
| 下游服务 | EVO2（环境变量 `EVO2_BASE_URL`，默认 http://36.137.205.153:8666） |

**请求参数映射**（本服务参数 → 下游接口参数）：

| 参数          | 类型     | 默认值   | 说明                                               |
| ----------- | ------ | ----- | ------------------------------------------------ |
| prompt      | string | 必填    | DNA 起始序列（支持 `params.prompt` 或 `params.sequence`） |
| numTokens   | string | "200" | 生成长度                                             |
| temperature | string | "0.6" | 采样温度                                             |
| topK        | string | "4"   | Top-K 采样参数                                       |
| topP        | string | "0.6" | Top-P 采样参数                                       |
| showLogits  | string | "0"   | 是否返回 logits                                      |

**结果结构**：

```json
{
  "generated_sequence": "ATCG...（后续生成的完整序列）"
}
```

### 5.2 PlantCAD2 统一 /report 接口（task_id=201~210）

PlantCAD2 所有任务统一使用 **POST /report** 端点，通过 `type` 字段区分推理类型。

下游服务地址：环境变量 `PLANTCAD2_BASE_URL`，默认 `http://localhost:8005`

#### 通用请求结构

```json
{
  "type": "embedding | variant_score | masked_predict | predict",
  "sequence": "DNA序列（IUPAC碱基），自动进行 U→T 转换兼容 mRNA",
  // 不同 type 附加不同参数...
}
```

#### 通用响应结构

```json
{
  "type": "embedding | variant_score | masked_predict | predict",
  "result": { ... },          // 推理数据（与旧接口一致）
  "markdown": "# 模型推理报告..."  // Markdown 格式报告，前端可直接渲染
}
```

> **注意**：
> - 所有位置参数使用 **1-based** 索引，与用户习惯一致，无需转换
> - 序列中的 `U`（尿嘧啶，mRNA 特征碱基）会自动转换为 `T`（胸腺嘧啶），兼容 mRNA 输入
> - 响应中的 `markdown` 字段会透传到本服务响应的顶级 `markdown` 字段

---

#### 201 - 嵌入提取（type=embedding）

| type 值       | 请求方法 |
| ------------- | ---- |
| `embedding`   | POST |

**附加请求参数**：

| 参数        | 类型      | 说明                      |
| --------- | -------- | ----------------------- |
| sequence  | string   | DNA 序列（IUPAC，最长 8192bp） |
| normalize | bool(可选)| 是否归一化（默认 true）          |

**结果结构**（内层 `result`）：

```json
{
  "embeddings": [[浮点数数组]],
  "shape": [序列长度, 1536]
}
```

---

#### 202 - 变异打分（type=variant_score）

| type 值           | 请求方法 |
| ----------------- | ---- |
| `variant_score`   | POST |

**附加请求参数**：

| 参数          | 类型       | 说明                          |
| ----------- | -------- | --------------------------- |
| sequence    | string   | DNA 序列                      |
| position    | int      | 变异位置（**1-based**，与用户输入一致） |
| ref_allele  | string   | 参考碱基（A/C/G/T）               |
| alt_alleles | string[] | 变异碱基列表                      |

**结果结构**（内层 `result`）：

```json
{
  "scores": {"A": -0.05, "C": -2.10, "G": -1.33, "T": -0.87}
}
```

---

#### 203 - 掩码预测（type=masked_predict）

| type 值           | 请求方法 |
| ----------------- | ---- |
| `masked_predict`  | POST |

**附加请求参数**：

| 参数        | 类型     | 说明                          |
| --------- | ------ | --------------------------- |
| sequence  | string | DNA 序列                      |
| positions | int[]  | 预测位置列表（**1-based**，与用户输入一致） |

**结果结构**（内层 `result`）：

```json
{
  "predictions": {
    "1": {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25},
    "3": {"A": 0.80, "C": 0.05, "G": 0.10, "T": 0.05}
  }
}
```

---

#### 204~210 - LoRA 任务预测（type=predict）

所有 LoRA 任务共用 `type=predict`，通过 `task` 参数区分具体任务：

| task_id | type 值     | task 参数值               | 预测类型         |
| ------- | ---------- | ---------------------- | ------------ |
| 204     | `predict`  | `acr_arabidopsis`      | 二分类          |
| 205     | `predict`  | `acr_nine_species`     | 二分类          |
| 206     | `predict`  | `acr_cell_type`        | 多标签分类（92种细胞类型） |
| 207     | `predict`  | `expression_on_off`    | 二分类          |
| 208     | `predict`  | `expression_absolute`  | 回归           |
| 209     | `predict`  | `translation_on_off`   | 二分类          |
| 210     | `predict`  | `translation_absolute` | 回归           |

**附加请求参数**：

| 参数       | 类型     | 说明                      |
| -------- | ------ | ----------------------- |
| sequence | string | DNA 序列                  |
| task     | string | LoRA 任务标识（由本服务自动填充） |

**结果结构**（内层 `result`）：

- **二分类任务（204/205/207/209）**：
  ```json
  {
    "prediction": "active/inactive",
    "probability": 0.95
  }
  ```

- **多标签分类任务（206）**：
  ```json
  {
    "num_labels": 92,
    "probabilities": [0.1, 0.05, ...]
  }
  ```

- **回归任务（208/210）**：
  ```json
  {
    "prediction": 3.45
  }
  ```

---

### 5.3 U→T 转换说明

由于 PlantCAD2 的 DNA 模型使用 IUPAC 核苷酸编码（A/C/G/T/N/R/Y/M/K/S/W/H/B/V/D），不包含 `U`（尿嘧啶），本服务在以下两处自动进行 U→T 转换：

1. **参数提取层**（中置信度/低置信度路径）：在 `param_extractor.py` 的 `validate_params` 中，对用户输入的序列做 `replace('U', 'T')`
2. **接口调用层**（高置信度路径）：在 `api_caller.py` 的 `build_request_body` 中，对发送到 PlantCAD2 的序列做 `replace('U', 'T')`

> 从生物学角度：mRNA 中的 U（尿嘧啶）在 DNA 序列中对应 T（胸腺嘧啶），这一转换是标准的 RNA→DNA 预处理，不影响模型推理的生物学意义。对于翻译效率预测（209/210）等涉及 mRNA 序列的任务，此转换确保兼容性。
