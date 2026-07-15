# AlphaFold3 推理报告接口文档

## 接口概述

**POST** `/api/v1/report`

DNA 结构预测的统一报告入口。接收 DNA 序列，自动生成反向互补链执行双链预测，返回原始推理结果 + 格式化 Markdown 报告。

### 与 DNA 推理端点的区别

| 特性 | `/predict/dna/sync` | `/report` 统一端点 |
|------|---------------------|-------------------|
| 返回格式 | 仅 `TaskDetail` JSON 结果 | JSON 结果 + Markdown 报告 |
| Markdown 报告 | ❌ 无 | ✅ 自动生成 |
| 用户输入回显 | ❌ 不包含 | ✅ 序列信息填入报告模板 |
| 推理失败处理 | 仅返回 status=failed | Markdown 报告中展示错误信息 |
| 适用场景 | 后端程序调用 | 前端展示 / 组学智能体交互 |

> 此接口仅支持 **DNA 序列**。蛋白质、RNA、配体等非 DNA 分子的预测请使用 `POST /api/v1/predict` 上传 JSON 文件。

---

## 请求格式

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sequence | string | ✅ | DNA 正向链序列（5'→3'），仅含 A/T/C/G，最长 10000 bp。反向互补链自动生成 |
| name | string | ❌ | 任务名称，不填则自动生成 |
| modelSeeds | int[] | ❌ | 随机种子列表，默认 `[42]` |

### 请求示例

```bash
curl -X POST http://localhost:8015/api/v1/report \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG",
    "name": "test_dna_40bp",
    "modelSeeds": [42]
  }'
```

---

## 响应格式

```json
{
  "type": "alphafold3_predict",
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "test_dna_40bp",
    "status": "completed",
    "created_at": "2026-07-14T12:00:00Z",
    "completed_at": "2026-07-14T12:02:30Z",
    "best_ptm": 0.8546,
    "best_iptm": 0.7123,
    "ranking_score": 0.8921,
    "error_message": null,
    "predictions": [
      {
        "id": 1,
        "seed": 42,
        "sample_idx": 0,
        "cif_url": "/app/storage/tasks/.../test_dna_40bp_model.cif",
        "confidences_url": "/app/storage/tasks/.../test_dna_40bp_confidences.json",
        "summary_url": "/app/storage/tasks/.../test_dna_40bp_summary_confidences.json",
        "ranking_score": 0.8921,
        "ptm": 0.8546,
        "iptm": 0.7123
      }
    ]
  },
  "markdown": "# AlphaFold3 模型推理报告\n\n**来源**：组学智能体 — AlphaFold3 模型推理服务..."
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 推理类型标识，固定为 `alphafold3_predict` |
| result | object | 原始推理结果的 TaskDetail 对象，结构与 `/predict/dna/sync` 一致 |
| markdown | string | 格式化的 Markdown 推理报告，可直接在前端渲染 |

### result 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 任务 UUID |
| name | string | 任务名称 |
| status | string | `completed` / `failed` |
| created_at | datetime | 创建时间 |
| completed_at | datetime \| null | 完成时间 |
| best_ptm | float \| null | 最佳预测 pTM（全局结构置信度，0-1） |
| best_iptm | float \| null | 最佳预测 ipTM（界面置信度，0-1） |
| ranking_score | float \| null | 最佳预测排名分数（越高越好） |
| error_message | string \| null | 失败时的错误信息 |
| predictions | array | 所有预测结果列表（默认 5 个） |

### predictions[i] 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 预测记录 ID |
| seed | int \| null | 随机种子 |
| sample_idx | int | 样本索引（0-4） |
| ranking_score | float \| null | 该预测的排名分数 |
| ptm | float \| null | 该预测的 pTM |
| iptm | float \| null | 该预测的 ipTM |
| cif_url | string \| null | CIF 结构文件路径 |
| confidences_url | string \| null | 置信度 JSON 路径 |
| summary_url | string \| null | 置信度摘要 JSON 路径 |

---

## 完整响应示例

```json
{
  "type": "alphafold3_predict",
  "result": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "test_dna_40bp",
    "status": "completed",
    "created_at": "2026-07-14T12:00:00.000000Z",
    "completed_at": "2026-07-14T12:02:30.000000Z",
    "best_ptm": 0.8546,
    "best_iptm": 0.7123,
    "ranking_score": 0.8921,
    "error_message": null,
    "predictions": [
      {"id": 1, "seed": 42, "sample_idx": 0, "cif_url": "/app/storage/tasks/.../test_dna_40bp_model.cif", "confidences_url": "/app/storage/tasks/.../test_dna_40bp_confidences.json", "summary_url": "/app/storage/tasks/.../test_dna_40bp_summary_confidences.json", "ranking_score": 0.8921, "ptm": 0.8546, "iptm": 0.7123},
      {"id": 2, "seed": 42, "sample_idx": 1, "cif_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-1_model.cif", "confidences_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-1_confidences.json", "summary_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-1_summary_confidences.json", "ranking_score": 0.8800, "ptm": 0.8400, "iptm": 0.7000},
      {"id": 3, "seed": 42, "sample_idx": 2, "cif_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-2_model.cif", "confidences_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-2_confidences.json", "summary_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-2_summary_confidences.json", "ranking_score": 0.8700, "ptm": 0.8300, "iptm": 0.6900},
      {"id": 4, "seed": 42, "sample_idx": 3, "cif_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-3_model.cif", "confidences_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-3_confidences.json", "summary_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-3_summary_confidences.json", "ranking_score": 0.8600, "ptm": 0.8200, "iptm": 0.6800},
      {"id": 5, "seed": 42, "sample_idx": 4, "cif_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-4_model.cif", "confidences_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-4_confidences.json", "summary_url": "/app/storage/tasks/.../test_dna_40bp_seed-42_sample-4_summary_confidences.json", "ranking_score": 0.8500, "ptm": 0.8100, "iptm": 0.6700}
    ]
  },
  "markdown": "# AlphaFold3 模型推理报告\n\n**来源**：组学智能体 — AlphaFold3 模型推理服务\n\n> **输入信息**：\n> - **任务名称**：test_dna_40bp\n> - **序列（5'→3' 正向链）**：`ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG`\n> - **序列长度**：40 bp\n> - **链型**：DNA 双链（自动生成反向互补链）\n> - **推理耗时**：152.3 秒\n\n---\n\n> 来自组学智能体 — AlphaFold3 模型推理服务，对刚刚输入的 **40 bp** DNA 序列进行结构预测的结果如下。\n\n## 全局置信度\n\n| 指标 | 数值 | 说明 |\n| :- | :- | :- |\n| Ranking Score | 0.8921 | 综合排名分数（越高越好） |\n| pTM | 0.8546 | 全局结构置信度（>0.5 可信） |\n| ipTM | 0.7123 | 界面预测置信度（>0.8 高置信） |\n| 平均 pLDDT | 72.34 | 局部结构置信度（>70 高置信） |\n| 平均 PAE | 2.34 Å | 预测对齐误差（越低越好） |\n| 无序比例 | 5.0% | 预测为无序结构的残基比例 |\n| 空间冲突 | 无 | 原子间非键合距离异常 |\n\n## 最佳结果来源\n\n> 以下报告内容基于 **seed-42** 的第 **0** 次采样，在全部 5 个样本中排名第 1。\n\n## 逐链置信度\n\n| 链 | pTM | ipTM |\n| :- | :- | :- |\n| A | 0.8546 | 0.7123 |\n| B | 0.8500 | 0.7100 |\n\n## 链间 PAE\n\n| 链对 | 最小 PAE (Å) |\n| :- | :- |\n| A-A | 0.50 |\n| A-B | 4.20 |\n| B-A | 4.20 |\n| B-B | 0.50 |\n\n## 链间 ipTM\n\n| 链对 | ipTM |\n| :- | :- |\n| A-A | 0.8500 |\n| A-B | 0.7200 |\n| B-A | 0.7200 |\n| B-B | 0.8500 |\n\n## 所有预测排名\n\n| 排名 | 种子 | 样本 | Ranking Score | pTM | ipTM |\n| :- | :- | :- | :- | :- | :- |\n| 1 | 42 | 0 | 0.8921 | 0.8546 | 0.7123 |\n| 2 | 42 | 1 | 0.8800 | 0.8400 | 0.7000 |\n| 3 | 42 | 2 | 0.8700 | 0.8300 | 0.6900 |\n| 4 | 42 | 3 | 0.8600 | 0.8200 | 0.6800 |\n| 5 | 42 | 4 | 0.8500 | 0.8100 | 0.6700 |\n\n## 结果文件\n\n- [预测结构 (CIF)](http://36.137.166.174:8015/api/v1/tasks/xxx/download/test_dna_40bp_model.cif) — 最佳预测结构的原子坐标文件\n- [置信度数据 (JSON)](http://36.137.166.174:8015/api/v1/tasks/xxx/download/test_dna_40bp_confidences.json) — 包含 pLDDT、PAE、接触概率等逐残基置信度\n- [置信度摘要 (JSON)](http://36.137.166.174:8015/api/v1/tasks/xxx/download/test_dna_40bp_summary_confidences.json) — 包含 pTM、ipTM、逐链置信度等聚合指标\n- [排名分数 (CSV)](http://36.137.166.174:8015/api/v1/tasks/xxx/download/test_dna_40bp_ranking_scores.csv) — 所有 5 个样本的排名分数\n\n---\n\n> 对您输入的 40 bp DNA 序列完成结构预测，pTM = 0.8546（较高），ipTM = 0.7123（一般），平均 pLDDT = 72.34（高），无空间冲突。"
}
```

---

## Markdown 报告模板说明

报告统一包含以下内容：

1. **标题**：`AlphaFold3 模型推理报告`（失败时附加 ⚠️ 推理失败）
2. **来源说明**：`组学智能体 — AlphaFold3 模型推理服务`
3. **输入信息**：以引用块展示任务名称、序列、长度、链型、耗时
4. **结果概述**：一句总结性描述
5. **全局置信度表**：Ranking Score、pTM、ipTM、平均 pLDDT、平均 PAE、无序比例、空间冲突
6. **最佳结果来源**：说明最佳预测来自哪个 seed / sample
7. **逐链置信度表**：A/B 链的 pTM / ipTM
8. **链间 PAE / ipTM 矩阵**（多链时展示）
9. **所有预测排名**：排名、种子、样本、Ranking Score、pTM、ipTM
10. **结果文件下载**：最佳 CIF、Confidences JSON、Summary JSON、排名 CSV 的下载链接
11. **总结**：基于置信度指标的解读

---

## 错误处理

### 参数校验错误（422）

```json
{
  "detail": [{
    "loc": ["body", "sequence"],
    "msg": "DNA 序列包含非法字符: {'N'}。仅允许 A/T/C/G。",
    "type": "value_error"
  }]
}
```

### 业务错误（400）

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "构建 AlphaFold 3 输入失败",
    "details": "sequences 字段不能为空"
  }
}
```

### 服务器错误（500）

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "任务创建成功但无法读取结果"
  }
}
```
