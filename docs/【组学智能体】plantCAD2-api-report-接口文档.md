# PlantCAD2 推理报告接口文档

## 接口概述

**POST** `/report`

推理报告接口是 PlantCAD2 推理服务的**统一入口**，将四种推理类型（嵌入提取、变异打分、掩码预测、下游任务预测）整合为一个端点。除返回原始推理结果外，还会自动生成格式化的 **Markdown 推理报告**，方便前端直接渲染展示。

### 与专用端点的区别

| 特性 | 专用端点（如 `/variant-score`） | `/report` 统一端点 |
|------|-------------------------------|-------------------|
| 返回格式 | 仅 JSON 结果 | JSON 结果 + Markdown 报告 |
| Markdown 报告 | ❌ 无 | ✅ 自动生成 |
| 用户输入回显 | ❌ 不包含 | ✅ 请求参数填入报告模板 |
| 适用场景 | 后端程序调用 | 前端展示 / 人机交互 |

---

## 请求格式

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | ✅ | 推理类型：`embedding`, `variant_score`, `masked_predict`, `predict` |
| sequence | string | ✅ | DNA/RNA 序列（IUPAC 碱基，最长 8192 bp）。**RNA 碱基 U 会被自动转换为 T**，详见下方 RNA 支持说明 |
| normalize | bool | ❌ | 嵌入提取时使用，是否 L2 归一化，默认 `true` |
| position | int | ❌* | 变异打分时使用，变异位点的 **1-based** 位置 |
| ref_allele | string | ❌* | 变异打分时使用，参考碱基（A/C/G/T） |
| alt_alleles | string[] | ❌* | 变异打分时使用，变异碱基列表（最多 3 个） |
| positions | int[] | ❌* | 掩码预测时使用，要预测的 **1-based** 位置列表（最多 100 个） |
| task | string | ❌* | 下游任务预测时使用，任务名称（见下方可用任务） |

> *`*` 表示该字段仅当 `type` 为对应类型时必填。
>
> **🔬 RNA 支持说明**：`embedding`、`masked_predict`、`predict`（仅翻译效率任务）支持传入含 U 的 RNA 序列，服务会自动将 U 转换为 T 后交由模型计算。生物学上 U 和 T 完全等价（均与 A 配对），转换不影响结果。`variant_score` 不支持 RNA 输入。

### type 与必填字段对应关系

| type | 必填字段 |
|------|---------|
| `embedding` | `sequence` |
| `variant_score` | `sequence`, `position`, `ref_allele`, `alt_alleles` |
| `masked_predict` | `sequence`, `positions` |
| `predict` | `sequence`, `task` |

### 可用任务（type=predict）

| 任务 | 说明 | 输出类型 |
|------|------|----------|
| acr_arabidopsis | 拟南芥 ACR 预测 | 二分类 |
| acr_nine_species | 九物种 ACR 预测 | 二分类 |
| acr_cell_type | 细胞类型 ACR 预测 | 多标签分类（92 类） |
| expression_on_off | 表达量开/关预测 | 二分类 |
| expression_absolute | 表达量绝对值预测 | 回归 |
| translation_on_off | 翻译效率开/关预测 | 二分类 |
| translation_absolute | 翻译效率绝对值预测 | 回归 |

---

## 响应格式

```json
{
  "type": "variant_score",
  "result": {
    "scores": {"C": -0.76, "T": 0.77, "A": -0.80},
    "ref_prob": 0.246,
    "alt_probs": {"C": 0.115, "T": 0.529, "A": 0.110}
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**..."
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 推理类型，与请求中的 type 一致 |
| result | object | 原始推理结果，结构与对应专用端点一致 |
| markdown | string | 格式化的 Markdown 推理报告，可直接在前端渲染 |

---

## 使用示例

以下共 10 个示例，涵盖 `embedding`、`variant_score`、`masked_predict` 三个基础类型，以及 `predict` 下的全部 7 个 LoRA 任务。

### 1. 嵌入提取（Embedding）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "embedding",
    "sequence": "ACGTACGTACGTACGTACGT",
    "normalize": true
  }'
```

**响应示例**：

```json
{
  "type": "embedding",
  "result": {
    "embeddings": [[0.0123, -0.0345, 0.0567, -0.0789, 0.0901, ...], ...],
    "shape": [20, 1536],
    "sequence_length": 20
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：序列嵌入提取\n\n---\n\n> **输入信息**：\n> - **序列**：`ACGTACGTACGTACGTACGT`\n> - **序列长度**：20 bp\n> - **归一化**：是\n\n**推理结果**：\n- **嵌入维度**：20 × 1536\n- **有效序列长度**：20 bp\n- **首个位置嵌入（前5维）**：`[0.0123, -0.0345, 0.0567, -0.0789, 0.0901, ...]`\n\n> 对您输入的序列进行嵌入提取，共获得 20 个位置的 1536 维嵌入向量。"
}
```

---

### 2. 变异效应分析（Variant Score）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "variant_score",
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGATAGGCAAT",
    "position": 100,
    "ref_allele": "G",
    "alt_alleles": ["C", "T", "A"]
  }'
```

**响应示例**：

```json
{
  "type": "variant_score",
  "result": {
    "scores": {"C": -0.76, "T": 0.77, "A": -0.80},
    "ref_prob": 0.246,
    "alt_probs": {"C": 0.115, "T": 0.529, "A": 0.110}
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：变异效应分析\n\n---\n\n> **输入信息**：\n> - **序列**：`CTTAATTAATATTGCCTTTGTAATAACGCGCGA...`\n> - **变异位置**：第 100 位（1-based）\n> - **参考等位基因**：G\n> - **替代等位基因**：C, T, A\n\n**推理结果**：\n\n| 替代等位基因 | 效应分数 (LLR) | 概率 |\n|:----------:|:-------------:|:---:|\n| C | -0.7600 | 0.1150 |\n| T | 0.7700 | 0.5290 |\n| A | -0.8000 | 0.1100 |\n\n- **参考等位基因概率**：0.2460\n\n> 对您输入的序列在第 100 位的变异效应进行分析，替代等位基因 **T** 效应分数最高（+0.7700）。"
}
```

---

### 3. 掩码位置预测（Masked Predict）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "masked_predict",
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGATAGGCAAT",
    "positions": [100, 200, 255]
  }'
```

**响应示例**：

```json
{
  "type": "masked_predict",
  "result": {
    "predictions": {
      "100": {"A": 0.246, "C": 0.115, "G": 0.110, "T": 0.529},
      "200": {"A": 0.261, "C": 0.197, "G": 0.060, "T": 0.481},
      "255": {"A": 0.967, "C": 0.006, "G": 0.013, "T": 0.013}
    }
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：掩码位置预测\n\n---\n\n> **输入信息**：\n> - **序列**：`CTTAATTAATATTGCCTTTGTAATAACGCGCGA...`\n> - **序列长度**：50 bp\n> - **预测位置数**：3 个\n\n**推理结果**：\n\n#### 位置 100\n\n| 碱基 | 概率 |\n|:---:|:----:|\n| T | 0.5290 |\n| A | 0.2460 |\n| C | 0.1150 |\n| G | 0.1100 |\n\n#### 位置 200\n\n| 碱基 | 概率 |\n|:---:|:----:|\n| T | 0.4810 |\n| A | 0.2610 |\n| C | 0.1970 |\n| G | 0.0600 |\n\n#### 位置 255\n\n| 碱基 | 概率 |\n|:---:|:----:|\n| A | 0.9670 |\n| C | 0.0060 |\n| G | 0.0130 |\n| T | 0.0130 |\n\n> 对您输入的序列在 3 个掩码位置进行碱基概率预测，各位置结果如上表所示。"
}
```

---

### 4. 下游任务预测 — acr_arabidopsis（二分类）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "predict",
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGATAGGCAAT",
    "task": "acr_arabidopsis"
  }'
```

**响应示例**：

```json
{
  "type": "predict",
  "result": {
    "task": "acr_arabidopsis",
    "prediction": "POSITIVE",
    "probability": 0.87
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：下游任务预测 — 拟南芥ACR预测\n\n---\n\n> **输入信息**：\n> - **任务**：acr_arabidopsis（拟南芥ACR预测）\n> - **序列**：`CTTAATTAATATTGCCTTTGTAATAACGCGCGA...`\n> - **序列长度**：50 bp\n\n**推理结果**：\n\n- **预测结果**：**POSITIVE**\n- **置信度**：0.8700\n\n> 对您输入的序列进行 **拟南芥ACR预测** 预测，结果为上述所示。"
}
```

---

### 5. 下游任务预测 — acr_nine_species（二分类）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "predict",
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGATAGGCAAT",
    "task": "acr_nine_species"
  }'
```

**响应示例**：

```json
{
  "type": "predict",
  "result": {
    "task": "acr_nine_species",
    "prediction": "POSITIVE",
    "probability": 0.93
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：下游任务预测 — 九物种ACR预测\n\n---\n\n> **输入信息**：\n> - **任务**：acr_nine_species（九物种ACR预测）\n> - **序列**：`CTTAATTAATATTGCCTTTGTAATAACGCGCGA...`\n> - **序列长度**：50 bp\n\n**推理结果**：\n\n- **预测结果**：**POSITIVE**\n- **置信度**：0.9300\n\n> 对您输入的序列进行 **九物种ACR预测** 预测，结果为上述所示。"
}
```

---

### 6. 下游任务预测 — acr_cell_type（多标签分类，92 类）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "predict",
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGATAGGCAAT",
    "task": "acr_cell_type"
  }'
```

**响应示例**：

```json
{
  "type": "predict",
  "result": {
    "task": "acr_cell_type",
    "prediction": "MULTI_LABEL",
    "probabilities": [0.12, 0.03, 0.78, 0.01, 0.45, 0.22, 0.67, 0.09, 0.34, 0.55, 0.02, 0.88, 0.15, 0.04, 0.71, 0.33, 0.06, 0.91, 0.27, 0.54, 0.08, 0.63, ...],
    "num_labels": 92
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：下游任务预测 — 细胞类型特异ACR预测\n\n---\n\n> **输入信息**：\n> - **任务**：acr_cell_type（细胞类型特异ACR预测）\n> - **序列**：`CTTAATTAATATTGCCTTTGTAATAACGCGCGA...`\n> - **序列长度**：50 bp\n\n**推理结果**：\n\n- **预测结果**：**MULTI_LABEL**\n- **置信度**：0.8700\n\n**标签概率分布**（共 92 个标签）：\n\n| 标签 | 概率 |\n|:---:|:----:|\n| 0 | 0.1200 |\n| 1 | 0.0300 |\n| 2 | 0.7800 |\n| 3 | 0.0100 |\n| 4 | 0.4500 |\n| 5 | 0.2200 |\n| 6 | 0.6700 |\n| 7 | 0.0900 |\n| 8 | 0.3400 |\n| 9 | 0.5500 |\n| 10 | 0.0200 |\n| 11 | 0.8800 |\n| 12 | 0.1500 |\n| 13 | 0.0400 |\n| 14 | 0.7100 |\n| 15 | 0.3300 |\n| 16 | 0.0600 |\n| 17 | 0.9100 |\n| 18 | 0.2700 |\n| 19 | 0.5400 |\n| ... | ...（剩余 72 个标签）|\n\n> 对您输入的序列进行 **细胞类型特异ACR预测** 预测，结果为上述所示。"
}
```

---

### 7. 下游任务预测 — expression_on_off（二分类）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "predict",
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGATAGGCAAT",
    "task": "expression_on_off"
  }'
```

**响应示例**：

```json
{
  "type": "predict",
  "result": {
    "task": "expression_on_off",
    "prediction": "POSITIVE",
    "probability": 0.62
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：下游任务预测 — 基因表达开关预测\n\n---\n\n> **输入信息**：\n> - **任务**：expression_on_off（基因表达开关预测）\n> - **序列**：`CTTAATTAATATTGCCTTTGTAATAACGCGCGA...`\n> - **序列长度**：50 bp\n\n**推理结果**：\n\n- **预测结果**：**POSITIVE**\n- **置信度**：0.6200\n\n> 对您输入的序列进行 **基因表达开关预测** 预测，结果为上述所示。"
}
```

---

### 8. 下游任务预测 — expression_absolute（回归）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "predict",
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGATAGGCAAT",
    "task": "expression_absolute"
  }'
```

**响应示例**：

```json
{
  "type": "predict",
  "result": {
    "task": "expression_absolute",
    "prediction": 3.45
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：下游任务预测 — 基因表达水平预测\n\n---\n\n> **输入信息**：\n> - **任务**：expression_absolute（基因表达水平预测）\n> - **序列**：`CTTAATTAATATTGCCTTTGTAATAACGCGCGA...`\n> - **序列长度**：50 bp\n\n**推理结果**：\n\n- **预测值**：3.4500\n\n> 对您输入的序列进行 **基因表达水平预测** 预测，结果为上述所示。"
}
```

---

### 9. 下游任务预测 — translation_on_off（二分类）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "predict",
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGATAGGCAAT",
    "task": "translation_on_off"
  }'
```

**响应示例**：

```json
{
  "type": "predict",
  "result": {
    "task": "translation_on_off",
    "prediction": "NEGATIVE",
    "probability": 0.41
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：下游任务预测 — 翻译效率开关预测\n\n---\n\n> **输入信息**：\n> - **任务**：translation_on_off（翻译效率开关预测）\n> - **序列**：`CTTAATTAATATTGCCTTTGTAATAACGCGCGA...`\n> - **序列长度**：50 bp\n\n**推理结果**：\n\n- **预测结果**：**NEGATIVE**\n- **置信度**：0.4100\n\n> 对您输入的序列进行 **翻译效率开关预测** 预测，结果为上述所示。"
}
```

---

### 10. 下游任务预测 — translation_absolute（回归）

**请求示例**：

```bash
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "predict",
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGATAGGCAAT",
    "task": "translation_absolute"
  }'
```

**响应示例**：

```json
{
  "type": "predict",
  "result": {
    "task": "translation_absolute",
    "prediction": 2.18
  },
  "markdown": "# PlantCAD2 模型推理报告\n\n**来源**：组学智能体 — PlantCAD 模型推理服务\n**推理类型**：下游任务预测 — 翻译效率水平预测\n\n---\n\n> **输入信息**：\n> - **任务**：translation_absolute（翻译效率水平预测）\n> - **序列**：`CTTAATTAATATTGCCTTTGTAATAACGCGCGA...`\n> - **序列长度**：50 bp\n\n**推理结果**：\n\n- **预测值**：2.1800\n\n> 对您输入的序列进行 **翻译效率水平预测** 预测，结果为上述所示。"
}
```

---

## Markdown 报告模板说明

报告统一包含以下内容：

1. **标题**：`PlantCAD2 模型推理报告`
2. **来源说明**：`组学智能体 — PlantCAD 模型推理服务`
3. **推理类型**：标明具体是哪种推理
4. **输入信息**：以引用块形式展示用户请求参数（序列、位置、任务等）
5. **推理结果**：以表格或列表形式展示业务数据指标
6. **结论/说明**：一行总结性的说明

各推理类型的 markdown 报告风格保持一致，信息简洁，重点突出结果数据。

---

## 错误处理

### 参数校验错误（422）

```json
{
  "detail": "请求参数校验失败",
  "errors": [
    "body -> type: Unknown type 'invalid_type'..."
  ]
}
```

### 业务错误（400）

```json
{
  "detail": "Position 100 is out of range for sequence of length 50 (1-based indexing)"
}
```

### 服务器错误（500）

```json
{
  "detail": "服务器内部错误"
}
```

---

## RNA 支持说明

本服务在部分端点支持 RNA 序列输入（含 U 碱基），详细规则如下：

| 报告类型 | 是否支持 RNA | 说明 |
|---------|-------------|------|
| `embedding` | ✅ 支持 | U → T 自动转换，嵌入提取不受影响 |
| `masked_predict` | ✅ 支持 | U → T 自动转换，输出碱基空间为 A/C/G/T |
| `predict`（翻译效率任务） | ✅ 支持 | mRNA 是翻译效率预测的自然输入格式 |
| `predict`（ACR/表达量任务） | ❌ 不支持 | 这些任务使用基因组 DNA 训练，不接受 RNA |
| `variant_score` | ❌ 不支持 | 变异打分评估 DNA 变异，无 RNA 对应概念 |

> **生物学原理**：RNA 的尿嘧啶（U）和 DNA 的胸腺嘧啶（T）功能完全等价（均与腺嘌呤 A 配对）。将 U 转换为 T 后，DNA 语言模型处理的信号与原始 RNA 序列完全一致。ACR 预测和变异打分等任务在生物学概念上与 RNA 无关，因此不支持 RNA 输入。
