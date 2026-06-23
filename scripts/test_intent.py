#!/usr/bin/env python3
"""
组学智能体意图识别服务 - 测试脚本
测试三种置信度场景：高、中、低
"""

import httpx
import json
import sys
from typing import Dict, Any

# 服务地址
BASE_URL = "http://localhost:8010"


def test_intent(user_input: str, expected_confidence: str = None) -> Dict[str, Any]:
    """测试意图识别接口"""
    url = f"{BASE_URL}/intent/recognize"
    payload = {"user_input": user_input}

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            # 打印结果
            print(f"\n{'='*60}")
            print(f"用户输入: {user_input}")
            print(f"{'='*60}")
            print(f"置信度: {result.get('confidence')}")

            if result.get('confidence') == 'high':
                print(f"任务ID: {result.get('task_id')}")
                print(f"任务名称: {result.get('task_name')}")
                print(f"模型: {result.get('model')}")
                print(f"参数: {json.dumps(result.get('params'), ensure_ascii=False, indent=2)}")
                if result.get('result'):
                    print(f"执行结果: {json.dumps(result.get('result'), ensure_ascii=False, indent=2)}")

            elif result.get('confidence') == 'medium':
                print(f"引导信息: {result.get('guide_message')}")
                if result.get('suggested_tasks'):
                    print("推荐任务:")
                    for task in result['suggested_tasks']:
                        print(f"  - [{task['task_id']}] {task['task_name']}")

            elif result.get('confidence') == 'low':
                print(f"引导信息: {result.get('guide_message')}")
                if result.get('available_tasks'):
                    print("可用任务:")
                    for task in result['available_tasks'][:5]:  # 只显示前5个
                        print(f"  - [{task['task_id']}] {task['task_name']}")
                    if len(result['available_tasks']) > 5:
                        print(f"  ... 还有 {len(result['available_tasks'])-5} 个任务")

            if result.get('error'):
                print(f"错误: {json.dumps(result['error'], ensure_ascii=False, indent=2)}")

            # 验证置信度
            if expected_confidence and result.get('confidence') != expected_confidence:
                print(f"⚠️  警告: 期望置信度 '{expected_confidence}'，实际 '{result.get('confidence')}'")

            return result

    except httpx.ConnectError:
        print(f"❌ 连接失败: 服务未启动或地址错误 ({BASE_URL})")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP 错误: {e.response.status_code}")
        print(f"响应: {e.response.text}")
        return {}
    except Exception as e:
        print(f"❌ 异常: {e}")
        return {}


def test_health():
    """测试健康检查接口"""
    print("\n" + "="*60)
    print("测试健康检查接口")
    print("="*60)

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{BASE_URL}/health")
            response.raise_for_status()
            result = response.json()
            print(f"状态: {result.get('status')}")
            print(f"服务: {result.get('service')}")
            print(f"版本: {result.get('version')}")
            return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


def test_high_confidence():
    """测试高置信度场景 - 明确的单一任务"""
    print("\n" + "🔵"*30)
    print("测试场景 1: 高置信度 (直接执行)")
    print("🔵"*30)

    test_cases = [
        "帮我分析这个基因序列的嵌入向量: ATGCGATCGATCGATCG",
        "我想预测这个变异的致病性: chr1:12345 A>T",
        "预测位置 chr1:5000 的碱基，参考碱基是 A",
        "生成一段 500bp 的启动子序列",
    ]

    for case in test_cases:
        test_intent(case, expected_confidence="high")


def test_medium_confidence():
    """测试中置信度场景 - 有多个可能的任务"""
    print("\n" + "🟡"*30)
    print("测试场景 2: 中置信度 (推荐任务)")
    print("🟡"*30)

    test_cases = [
        "我想分析玉米的基因表达",
        "帮我预测这个基因的功能",
        "分析一下这个 DNA 序列",
        "我想做基因组分析",
    ]

    for case in test_cases:
        test_intent(case, expected_confidence="medium")


def test_low_confidence():
    """测试低置信度场景 - 模糊或无关的输入"""
    print("\n" + "🔴"*30)
    print("测试场景 3: 低置信度 (引导用户)")
    print("🔴"*30)

    test_cases = [
        "你好",
        "今天天气怎么样？",
        "帮我写个 Python 脚本",
        "什么是人工智能？",
    ]

    for case in test_cases:
        test_intent(case, expected_confidence="low")


def test_all_tasks():
    """测试所有任务类型"""
    print("\n" + "🟢"*30)
    print("测试所有任务类型")
    print("🟢"*30)

    task_tests = [
        ("EVO2 基因序列生成", "用 EVO2 生成一段 200bp 的启动子序列"),
        ("嵌入提取", "提取这段序列的嵌入向量: ATGCGATCG"),
        ("变异打分", "评估变异 chr1:1000 G>C 的影响"),
        ("掩码预测", "预测 chr1:5000 位置的碱基"),
        ("ACR 预测 - 玉米", "预测玉米基因组中的开放染色质区域"),
        ("ACR 预测 - 水稻", "预测水稻的 ACR 区域"),
        ("ACR 预测 - 大豆", "分析大豆的染色质可及性"),
        ("表达量预测 - 玉米", "预测玉米中 Zm00001d000001 的表达量"),
        ("表达量预测 - 水稻", "预测水稻基因的表达水平"),
        ("翻译效率预测 - 玉米", "预测玉米基因的翻译效率"),
        ("翻译效率预测 - 水稻", "分析水稻的翻译效率"),
    ]

    for name, query in task_tests:
        print(f"\n📋 测试: {name}")
        test_intent(query)


def main():
    """主测试函数"""
    print("\n" + "🚀"*20)
    print("组学智能体意图识别服务 - 自动化测试")
    print("🚀"*20)

    # 先测试健康检查
    if not test_health():
        print("\n❌ 服务未就绪，请检查服务是否启动")
        print(f"   确认服务地址: {BASE_URL}")
        sys.exit(1)

    # 根据命令行参数运行测试
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "high":
            test_high_confidence()
        elif test_type == "medium":
            test_medium_confidence()
        elif test_type == "low":
            test_low_confidence()
        elif test_type == "all":
            test_all_tasks()
        else:
            print(f"未知测试类型: {test_type}")
            print("可用类型: high, medium, low, all")
            sys.exit(1)
    else:
        # 默认运行所有场景测试
        test_high_confidence()
        test_medium_confidence()
        test_low_confidence()

    print("\n" + "✅"*20)
    print("测试完成!")
    print("✅"*20)


if __name__ == "__main__":
    main()
