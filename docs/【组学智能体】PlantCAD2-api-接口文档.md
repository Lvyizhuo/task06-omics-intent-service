# PlantCAD2 推理服务 API 参考文档

## 1. 健康检查

**GET** `/health`

### 请求示例

```bash
curl http://localhost:8005/health
```

### 请求格式

无

### 响应示例

```json
{"status":"ok","model_loaded":true,"device":"cuda:0"}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 服务状态 |
| model_loaded | bool | 模型是否加载完成 |
| device | string | 推理设备 |

---

## 2. 嵌入提取

**POST** `/embeddings`

支持 RNA 输入（U 自动转换为 T）。

### 请求示例

```bash
curl -X POST http://localhost:8005/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGAAACACAAATCTTCTCTGCCTAATGCAGTAGTCATGTGTTGACTCCTTCAAAATTTCCAAGAAGTTAGTGGCTGGTGTGTCATTGTCTTCATCTTTTTTTTTTTTTTTTTAAAAATTGAATGCGACATGTACTCCTCAACGTATAAGCTCAATGCTTGTTACTGAAACATCTCTTGTCTGATTTTTTCAGGCTAAGTCTTACAGAAAGTGATTGGGCACTTCAATGGCTTTCACAAATGAAAAAGATGGATCTAAGGGATTTGTGAAGAGAGTGGCTTCATCTTTCTCCATGAGGAAGAAGAAGAATGCAACAAGTGAACCCAAGTTGCTTCCAAGATCGAAATCAACAGGTTCTGCTAACTTTGAATCCATGAGGCTACCTGCAACGAAGAAGATTTCAGATGTCACAAACAAAACAAGGATCAAACCATTAGGTGGTGTAGCACCAGCACAACCAAGAAGGGAAAAGATCGATGATCG",
    "normalize": true
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | DNA/RNA 序列（最长 8192 bp），RNA 碱基 U 自动转换为 T |
| normalize | bool | ❌ | 是否 L2 归一化，默认 true |

### 响应示例

```json
{
  "embeddings": [[0.012, -0.034, ...], ...],
  "shape": [512, 1536],
  "sequence_length": 512
}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| embeddings | float[][] | 每个位置的 1536 维向量 |
| shape | int[] | 形状，如 [512, 1536] |
| sequence_length | int | token 化后的序列长度 |

---

## 3. 变异打分

**POST** `/variant-score`

零样本评估单核苷酸变异（SNV）。不支持 RNA 输入。

### 请求示例

```bash
curl -X POST http://localhost:8005/variant-score \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGAAACACAAATCTTCTCTGCCTAATGCAGTAGTCATGTGTTGACTCCTTCAAAATTTCCAAGAAGTTAGTGGCTGGTGTGTCATTGTCTTCATCTTTTTTTTTTTTTTTTTAAAAATTGAATGCGACATGTACTCCTCAACGTATAAGCTCAATGCTTGTTACTGAAACATCTCTTGTCTGATTTTTTCAGGCTAAGTCTTACAGAAAGTGATTGGGCACTTCAATGGCTTTCACAAATGAAAAAGATGGATCTAAGGGATTTGTGAAGAGAGTGGCTTCATCTTTCTCCATGAGGAAGAAGAAGAATGCAACAAGTGAACCCAAGTTGCTTCCAAGATCGAAATCAACAGGTTCTGCTAACTTTGAATCCATGAGGCTACCTGCAACGAAGAAGATTTCAGATGTCACAAACAAAACAAGGATCAAACCATTAGGTGGTGTAGCACCAGCACAACCAAGAAGGGAAAAGATCGATGATCG",
    "position": 100,
    "ref_allele": "G",
    "alt_alleles": ["C", "T", "A"]
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | 包含变异位点的上下文 DNA 序列 |
| position | int | ✅ | 变异位点的 1-based 位置 |
| ref_allele | string | ✅ | 参考碱基（A/C/G/T） |
| alt_alleles | string[] | ✅ | 变异碱基列表（最多 3 个） |

### 响应示例

```json
{
  "scores": {"C": -0.76, "T": 0.77, "A": -0.80},
  "ref_prob": 0.246,
  "alt_probs": {"C": 0.115, "T": 0.529, "A": 0.110}
}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| scores | object | 每个变异碱基的 LLR 分数 |
| ref_prob | float | 参考碱基的预测概率 |
| alt_probs | object | 每个变异碱基的预测概率 |

---

## 4. 掩码预测

**POST** `/masked-predict`

支持 RNA 输入（U 自动转换为 T），输出碱基空间为 A/C/G/T。

### 请求示例

```bash
curl -X POST http://localhost:8005/masked-predict \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGAAACACAAATCTTCTCTGCCTAATGCAGTAGTCATGTGTTGACTCCTTCAAAATTTCCAAGAAGTTAGTGGCTGGTGTGTCATTGTCTTCATCTTTTTTTTTTTTTTTTTAAAAATTGAATGCGACATGTACTCCTCAACGTATAAGCTCAATGCTTGTTACTGAAACATCTCTTGTCTGATTTTTTCAGGCTAAGTCTTACAGAAAGTGATTGGGCACTTCAATGGCTTTCACAAATGAAAAAGATGGATCTAAGGGATTTGTGAAGAGAGTGGCTTCATCTTTCTCCATGAGGAAGAAGAAGAATGCAACAAGTGAACCCAAGTTGCTTCCAAGATCGAAATCAACAGGTTCTGCTAACTTTGAATCCATGAGGCTACCTGCAACGAAGAAGATTTCAGATGTCACAAACAAAACAAGGATCAAACCATTAGGTGGTGTAGCACCAGCACAACCAAGAAGGGAAAAGATCGATGATCG",
    "positions": [100, 200, 255]
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | DNA/RNA 序列，RNA 碱基 U 自动转换为 T |
| positions | int[] | ✅ | 1-based 位置列表（最多 100 个） |

### 响应示例

```json
{
  "predictions": {
    "100": {"A": 0.246, "C": 0.115, "G": 0.110, "T": 0.529},
    "200": {"A": 0.261, "C": 0.197, "G": 0.060, "T": 0.481},
    "255": {"A": 0.967, "C": 0.006, "G": 0.013, "T": 0.013}
  }
}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| predictions | object | key 为位置，value 为 {A/C/G/T: 概率} 的字典 |

---

## 5. ACR 预测 — 拟南芥

**POST** `/predict`

二分类任务，使用拟南芥数据训练。

### 请求示例

```bash
curl -X POST http://localhost:8005/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGAAACACAAATCTTCTCTGCCTAATGCAGTAGTCATGTGTTGACTCCTTCAAAATTTCCAAGAAGTTAGTGGCTGGTGTGTCATTGTCTTCATCTTTTTTTTTTTTTTTTTAAAAATTGAATGCGACATGTACTCCTCAACGTATAAGCTCAATGCTTGTTACTGAAACATCTCTTGTCTGATTTTTTCAGGCTAAGTCTTACAGAAAGTGATTGGGCACTTCAATGGCTTTCACAAATGAAAAAGATGGATCTAAGGGATTTGTGAAGAGAGTGGCTTCATCTTTCTCCATGAGGAAGAAGAAGAATGCAACAAGTGAACCCAAGTTGCTTCCAAGATCGAAATCAACAGGTTCTGCTAACTTTGAATCCATGAGGCTACCTGCAACGAAGAAGATTTCAGATGTCACAAACAAAACAAGGATCAAACCATTAGGTGGTGTAGCACCAGCACAACCAAGAAGGGAAAAGATCGATGATCG",
    "task": "acr_arabidopsis"
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | DNA 序列（IUPAC 碱基，建议 ≥ 600 bp），不接受 RNA |
| task | string | ✅ | `acr_arabidopsis` |

### 响应示例

```json
{"task":"acr_arabidopsis","prediction":"POSITIVE","probability":0.87}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| task | string | 任务名称 |
| prediction | string | `POSITIVE` 或 `NEGATIVE` |
| probability | float | POSITIVE 的概率（0~1） |

---

## 6. ACR 预测 — 九物种

**POST** `/predict`

二分类任务，使用 9 种植物的数据联合训练，泛化能力更强。

### 请求示例

```bash
curl -X POST http://localhost:8005/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGAAACACAAATCTTCTCTGCCTAATGCAGTAGTCATGTGTTGACTCCTTCAAAATTTCCAAGAAGTTAGTGGCTGGTGTGTCATTGTCTTCATCTTTTTTTTTTTTTTTTTAAAAATTGAATGCGACATGTACTCCTCAACGTATAAGCTCAATGCTTGTTACTGAAACATCTCTTGTCTGATTTTTTCAGGCTAAGTCTTACAGAAAGTGATTGGGCACTTCAATGGCTTTCACAAATGAAAAAGATGGATCTAAGGGATTTGTGAAGAGAGTGGCTTCATCTTTCTCCATGAGGAAGAAGAAGAATGCAACAAGTGAACCCAAGTTGCTTCCAAGATCGAAATCAACAGGTTCTGCTAACTTTGAATCCATGAGGCTACCTGCAACGAAGAAGATTTCAGATGTCACAAACAAAACAAGGATCAAACCATTAGGTGGTGTAGCACCAGCACAACCAAGAAGGGAAAAGATCGATGATCG",
    "task": "acr_nine_species"
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | DNA 序列（IUPAC 碱基），不接受 RNA |
| task | string | ✅ | `acr_nine_species` |

### 响应示例

```json
{"task":"acr_nine_species","prediction":"POSITIVE","probability":0.94}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| task | string | 任务名称 |
| prediction | string | `POSITIVE` 或 `NEGATIVE` |
| probability | float | POSITIVE 的概率（0~1） |

---

## 7. ACR 预测 — 细胞类型特异性

**POST** `/predict`

多标签分类任务（92 类）。

### 请求示例

```bash
curl -X POST http://localhost:8005/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGAAACACAAATCTTCTCTGCCTAATGCAGTAGTCATGTGTTGACTCCTTCAAAATTTCCAAGAAGTTAGTGGCTGGTGTGTCATTGTCTTCATCTTTTTTTTTTTTTTTTTAAAAATTGAATGCGACATGTACTCCTCAACGTATAAGCTCAATGCTTGTTACTGAAACATCTCTTGTCTGATTTTTTCAGGCTAAGTCTTACAGAAAGTGATTGGGCACTTCAATGGCTTTCACAAATGAAAAAGATGGATCTAAGGGATTTGTGAAGAGAGTGGCTTCATCTTTCTCCATGAGGAAGAAGAAGAATGCAACAAGTGAACCCAAGTTGCTTCCAAGATCGAAATCAACAGGTTCTGCTAACTTTGAATCCATGAGGCTACCTGCAACGAAGAAGATTTCAGATGTCACAAACAAAACAAGGATCAAACCATTAGGTGGTGTAGCACCAGCACAACCAAGAAGGGAAAAGATCGATGATCG",
    "task": "acr_cell_type"
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | DNA 序列（IUPAC 碱基），不接受 RNA |
| task | string | ✅ | `acr_cell_type` |

### 响应示例

```json
{"task":"acr_cell_type","prediction":"MULTI_LABEL","probabilities":[0.12,0.03,...],"num_labels":92}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| task | string | 任务名称 |
| prediction | string | 固定为 `MULTI_LABEL` |
| probabilities | float[] | 92 个细胞类型的概率（sigmoid） |
| num_labels | int | 标签数量（92） |

---

## 8. 表达量预测 — 开/关

**POST** `/predict`

预测基因在叶片中是否表达。不接受 RNA 输入。

### 请求示例

```bash
curl -X POST http://localhost:8005/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGAAACACAAATCTTCTCTGCCTAATGCAGTAGTCATGTGTTGACTCCTTCAAAATTTCCAAGAAGTTAGTGGCTGGTGTGTCATTGTCTTCATCTTTTTTTTTTTTTTTTTAAAAATTGAATGCGACATGTACTCCTCAACGTATAAGCTCAATGCTTGTTACTGAAACATCTCTTGTCTGATTTTTTCAGGCTAAGTCTTACAGAAAGTGATTGGGCACTTCAATGGCTTTCACAAATGAAAAAGATGGATCTAAGGGATTTGTGAAGAGAGTGGCTTCATCTTTCTCCATGAGGAAGAAGAAGAATGCAACAAGTGAACCCAAGTTGCTTCCAAGATCGAAATCAACAGGTTCTGCTAACTTTGAATCCATGAGGCTACCTGCAACGAAGAAGATTTCAGATGTCACAAACAAAACAAGGATCAAACCATTAGGTGGTGTAGCACCAGCACAACCAAGAAGGGAAAAGATCGATGATCG",
    "task": "expression_on_off"
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | DNA 序列（IUPAC 碱基），不接受 RNA |
| task | string | ✅ | `expression_on_off` |

### 响应示例

```json
{"task":"expression_on_off","prediction":"POSITIVE","probability":0.56}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| task | string | 任务名称 |
| prediction | string | `POSITIVE` 或 `NEGATIVE` |
| probability | float | POSITIVE 的概率（0~1） |

---

## 9. 表达量预测 — 绝对值

**POST** `/predict`

预测基因在叶片中的表达水平。不接受 RNA 输入。

### 请求示例

```bash
curl -X POST http://localhost:8005/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "CTTAATTAATATTGCCTTTGTAATAACGCGCGAAACACAAATCTTCTCTGCCTAATGCAGTAGTCATGTGTTGACTCCTTCAAAATTTCCAAGAAGTTAGTGGCTGGTGTGTCATTGTCTTCATCTTTTTTTTTTTTTTTTTAAAAATTGAATGCGACATGTACTCCTCAACGTATAAGCTCAATGCTTGTTACTGAAACATCTCTTGTCTGATTTTTTCAGGCTAAGTCTTACAGAAAGTGATTGGGCACTTCAATGGCTTTCACAAATGAAAAAGATGGATCTAAGGGATTTGTGAAGAGAGTGGCTTCATCTTTCTCCATGAGGAAGAAGAAGAATGCAACAAGTGAACCCAAGTTGCTTCCAAGATCGAAATCAACAGGTTCTGCTAACTTTGAATCCATGAGGCTACCTGCAACGAAGAAGATTTCAGATGTCACAAACAAAACAAGGATCAAACCATTAGGTGGTGTAGCACCAGCACAACCAAGAAGGGAAAAGATCGATGATCG",
    "task": "expression_absolute"
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | DNA 序列（IUPAC 碱基），不接受 RNA |
| task | string | ✅ | `expression_absolute` |

### 响应示例

```json
{"task":"expression_absolute","prediction":3.45}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| task | string | 任务名称 |
| prediction | float | 预测的连续值 |

---

## 10. 翻译效率预测 — 开/关

**POST** `/predict`

预测 mRNA 在叶片中是否会被翻译。支持 RNA 输入（U 自动转换为 T）。

### 请求示例

```bash
curl -X POST http://localhost:8005/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "AUGCAUGCACGU",
    "task": "translation_on_off"
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | mRNA 序列，支持 RNA 碱基 U（自动转换为 T） |
| task | string | ✅ | `translation_on_off` |

### 响应示例

```json
{"task":"translation_on_off","prediction":"POSITIVE","probability":0.72}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| task | string | 任务名称 |
| prediction | string | `POSITIVE` 或 `NEGATIVE` |
| probability | float | POSITIVE 的概率（0~1） |

---

## 11. 翻译效率预测 — 绝对值

**POST** `/predict`

预测 mRNA 在叶片中的翻译效率数值。支持 RNA 输入（U 自动转换为 T）。

### 请求示例

```bash
curl -X POST http://localhost:8005/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "AUGCAUGCACGU",
    "task": "translation_absolute"
  }'
```

### 请求格式

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | mRNA 序列，支持 RNA 碱基 U（自动转换为 T） |
| task | string | ✅ | `translation_absolute` |

### 响应示例

```json
{"task":"translation_absolute","prediction":2.78}
```

### 响应格式

| 字段 | 类型 | 说明 |
|------|------|------|
| task | string | 任务名称 |
| prediction | float | 预测的连续值 |

---

## 推理报告接口

**POST** `/report`

推理报告是 PlantCAD2 推理服务的统一入口，接收 `embedding` / `variant_score` / `masked_predict` / `predict` 四种推理类型，返回原始结果 + 自动生成的 Markdown 报告。支持 RNA 输入（U→T 自动转换）。

详细文档见：[【组学智能体】plantCAD2-api-report.md](【组学智能体】plantCAD2-api-report.md)
