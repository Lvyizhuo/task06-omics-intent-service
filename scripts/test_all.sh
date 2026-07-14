#!/usr/bin/env bash
#=============================================================================
# 组学智能体意图识别服务 - 批量测试脚本
# 涵盖所有 11 个任务 + 中/低置信度场景
#
# 新 /report 接口验证要点：
#   - PlantCAD2 任务走 POST /report（type 字段区分）
#   - 响应含 markdown 字段（前端渲染用）
#   - 位置参数为 1-based
#   - suggested_tasks / available_tasks 含 required_fields
#
# 用法:
#   chmod +x test_all.sh
#   ./test_all.sh                            # 默认 localhost:8010
#   BASE_URL=http://10.0.0.5:8010 ./test_all.sh  # 自定义地址
#=============================================================================

set -euo pipefail

# ── 配置 ──────────────────────────────────────────────────────────────────
BASE_URL="${BASE_URL:-http://localhost:8010}"
ENDPOINT="${BASE_URL}/intent/recognize"
HEALTH_URL="${BASE_URL}/health"

FAIL_COUNT=0
PASS_COUNT=0
TEST_COUNT=0

# ── 颜色 ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'  # No Color

# ── 辅助函数 ──────────────────────────────────────────────────────────────

print_header() {
    echo ""
    echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
    echo ""
}

run_test() {
    local name="$1"
    local user_input="$2"
    local expect_confidence="$3"
    local expect_task_id="$4"   # 可空
    local extra_check="$5"      # 额外的 jq 检查表达式，空则跳过

    TEST_COUNT=$((TEST_COUNT + 1))
    echo -e "${YELLOW}[TEST ${TEST_COUNT}]${NC} ${BOLD}${name}${NC}"
    echo -e "  输入: ${user_input:0:60}..."
    echo -e "  期望: confidence=${expect_confidence} task_id=${expect_task_id:-"—"}"

    # 发起请求
    local http_code
    local response_file
    response_file=$(mktemp)

    http_code=$(curl -s -o "$response_file" -w "%{http_code}" \
        "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$(cat <<EOF
{
    "user_input": "$user_input",
    "session_id": "batch_test_${TEST_COUNT}"
}
EOF
    )" 2>/dev/null || true)

    # 解析响应
    local confidence task_id has_markdown has_required_fields has_result
    confidence=$(jq -r '.confidence // "null"' "$response_file" 2>/dev/null || echo "parse_error")
    task_id=$(jq -r '.task_id // "null"' "$response_file" 2>/dev/null || echo "parse_error")
    has_markdown=$(jq 'if (.markdown // "") | length > 0 then "yes" else "no" end' "$response_file" 2>/dev/null || echo "no")

    # 检查 required_fields（中/低置信度）
    if [ "$expect_confidence" = "medium" ]; then
        has_required_fields=$(jq '[.suggested_tasks[]?.required_fields? // [] | length] | add // 0' "$response_file" 2>/dev/null || echo "0")
    elif [ "$expect_confidence" = "low" ]; then
        has_required_fields=$(jq '[.available_tasks[]?.required_fields? // [] | length] | add // 0' "$response_file" 2>/dev/null || echo "0")
    else
        has_required_fields="—"
    fi

    # 判定
    local pass=true
    local fail_reasons=""

    if [ "$http_code" != "200" ]; then
        pass=false
        fail_reasons="${fail_reasons} HTTP=${http_code}"
    fi

    if [ "$confidence" != "$expect_confidence" ]; then
        pass=false
        fail_reasons="${fail_reasons} confidence=${confidence}"
    fi

    if [ -n "$expect_task_id" ] && [ "$expect_task_id" != "null" ]; then
        if [ "$task_id" != "$expect_task_id" ]; then
            pass=false
            fail_reasons="${fail_reasons} task_id=${task_id}"
        fi
    fi

    # 额外的 jq 检查
    if [ -n "$extra_check" ]; then
        if ! jq -e "$extra_check" "$response_file" >/dev/null 2>&1; then
            pass=false
            fail_reasons="${fail_reasons} extra_check_fail"
        fi
    fi

    # 输出结果摘要
    if [ "$pass" = true ]; then
        echo -e "  结果: ${GREEN}✅ PASS${NC}  confidence=${confidence} task_id=${task_id}"
        if [ "$has_markdown" = "yes" ]; then
            echo -e "        ${GREEN}✓ markdown${NC} 报告已返回"
        fi
        if [ "$has_required_fields" != "0" ] && [ "$has_required_fields" != "—" ]; then
            echo -e "        ${GREEN}✓ required_fields${NC} 合计 ${has_required_fields} 个字段"
        fi
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  结果: ${RED}❌ FAIL${NC}${fail_reasons}"
        echo -e "  ${RED}响应:${NC}"
        jq -c '{confidence, task_id, markdown: (.markdown // "—" | .[0:60]), suggested_count: (.suggested_tasks // [] | length), available_count: (.available_tasks // [] | length)}' "$response_file" 2>/dev/null || cat "$response_file"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi

    rm -f "$response_file"
    echo ""
}

# ── 开始测试 ──────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}组学智能体意图识别服务 - 批量测试${NC}"
echo -e "服务地址: ${BASE_URL}"
echo -e "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ── 健康检查 ──────────────────────────────────────────────────────────────
print_header "前置检查: 服务健康状态"

health_status=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
if [ "$health_status" = "200" ]; then
    echo -e "${GREEN}✅ 服务健康 (HTTP ${health_status})${NC}"
else
    echo -e "${RED}❌ 服务异常 (HTTP ${health_status})${NC}"
    echo "请先启动服务: cd project && uvicorn app.main:app --host 0.0.0.0 --port 8010"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
#  第一部分: 高置信度 — 11 个任务
# ═══════════════════════════════════════════════════════════════════════════
print_header "第一部分: 高置信度测试"

# 1. 嵌入提取 (201) — type=embedding
run_test "嵌入提取 (201)" \
    "帮我提取这段DNA序列ATGCGTACGATCGATCGTACGATC的嵌入向量" \
    "high" "201" \
    '.markdown != null and .markdown != ""'

# 2. 变异打分 (202) — type=variant_score
run_test "变异打分 (202)" \
    "请帮我评估序列ACGTACGTACGT在位置5处由A突变为G的变异影响" \
    "high" "202" \
    '.markdown != null and .markdown != ""'

# 3. 掩码预测 (203) — type=masked_predict
run_test "掩码预测 (203)" \
    "请帮我预测DNA序列ACGTACGTACGT在位置1,3,5的碱基概率分布" \
    "high" "203" \
    '.markdown != null and .markdown != ""'

# 4. ACR预测-拟南芥 (204) — type=predict task=acr_arabidopsis
run_test "ACR预测-拟南芥 (204)" \
    "这段DNA序列ACGTACGTACGT在拟南芥中是不是活跃调控区域" \
    "high" "204" \
    '.markdown != null and .markdown != ""'

# 5. ACR预测-九物种 (205) — type=predict task=acr_nine_species
run_test "ACR预测-九物种 (205)" \
    "帮我预测ACGTACGTACGT是否属于活跃调控区域" \
    "high" "205" \
    '.markdown != null and .markdown != ""'

# 6. ACR预测-细胞类型 (206) — type=predict task=acr_cell_type
run_test "ACR预测-细胞类型 (206)" \
    "预测ACGTACGTACGT在92种细胞类型中的调控状态" \
    "high" "206" \
    '.markdown != null and .markdown != ""'

# 7. 表达量预测-开/关 (207) — type=predict task=expression_on_off
run_test "表达量预测-开/关 (207)" \
    "预测序列ACGTACGTACGT在叶片中是否表达" \
    "high" "207" \
    '.markdown != null and .markdown != ""'

# 8. 表达量预测-绝对值 (208) — type=predict task=expression_absolute
run_test "表达量预测-绝对值 (208)" \
    "预测这段序列ACGTACGTACGT在叶片中的具体表达水平数值" \
    "high" "208" \
    '.markdown != null and .markdown != ""'

# 9. 翻译效率预测-开/关 (209) — type=predict task=translation_on_off
run_test "翻译效率预测-开/关 (209)" \
    "这段mRNA序列AUGCAUGCACGU会不会被翻译" \
    "high" "209" \
    '.markdown != null and .markdown != ""'

# 10. 翻译效率预测-绝对值 (210) — type=predict task=translation_absolute
run_test "翻译效率预测-绝对值 (210)" \
    "帮我预测AUGCAUGCACGU的翻译效率数值" \
    "high" "210" \
    '.markdown != null and .markdown != ""'

# 11. 基因序列预测生成 (101 - EVO2，不走 /report)
run_test "基因序列预测生成 (101)" \
    "帮我生成序列ACGTACGTACGT的后续序列" \
    "high" "101" \
    '.markdown == null'

# ═══════════════════════════════════════════════════════════════════════════
#  第二部分: 中置信度
# ═══════════════════════════════════════════════════════════════════════════
print_header "第二部分: 中置信度测试"

# 12. 模糊分析 — 有序列但意图不明确
run_test "模糊分析 → medium" \
    "帮我分析一下这段DNA序列ACGTACGTACGT" \
    "medium" "" \
    '.suggested_tasks != null and (.suggested_tasks | length > 0)'

# 13. 裸序列 — 只输序列没有任务关键词（验证提示词修复）
run_test "裸序列（无关键词）→ medium" \
    "ACGTCGCTGCTCGCTCGCCTG" \
    "medium" "" \
    '.suggested_tasks != null and (.suggested_tasks | length > 0)'

# ═══════════════════════════════════════════════════════════════════════════
#  第三部分: 低置信度
# ═══════════════════════════════════════════════════════════════════════════
print_header "第三部分: 低置信度测试"

# 14. 无关输入
run_test "无关输入 → low" \
    "今天天气怎么样" \
    "low" "" \
    '.available_tasks != null and (.available_tasks | length == 11)'

# ═══════════════════════════════════════════════════════════════════════════
#  汇总
# ═══════════════════════════════════════════════════════════════════════════
print_header "测试结果汇总"

echo -e "总用例: ${TEST_COUNT}"
echo -e "${GREEN}通过: ${PASS_COUNT}${NC}"
if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${RED}失败: ${FAIL_COUNT}${NC}"
else
    echo -e "失败: ${FAIL_COUNT}"
fi
echo ""

# 详细 summary
echo -e "${BOLD}────────────────────────────────────────────${NC}"
printf "%-30s %-12s %-8s\n" "用例" "期望" "结果"
echo -e "${BOLD}────────────────────────────────────────────${NC}"
# 这里只是标题示意，具体结果见逐条输出
echo "（各用例详细结果见上方逐条输出）"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${RED}⚠️  有 ${FAIL_COUNT} 个用例失败，请检查日志${NC}"
    exit 1
else
    echo -e "${GREEN}✅ 全部 ${TEST_COUNT} 个测试用例通过${NC}"
    exit 0
fi
