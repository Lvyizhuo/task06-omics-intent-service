"""
测试优化3和优化4

优化3: 无论high/medium/low，都提取用户输入的数据并返回
优化4: 动态信息提示，提醒用户缺少哪些参数
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8010"


async def test_case(name: str, user_input: str, expected_confidence: str):
    """测试单个用例"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"输入: {user_input}")
    print(f"预期置信度: {expected_confidence}")
    print('-'*60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/intent/recognize",
                json={"user_input": user_input}
            )
            result = response.json()

            confidence = result.get("confidence")
            params = result.get("params")
            guide_message = result.get("guide_message", "")

            print(f"实际置信度: {confidence}")
            print(f"引导信息: {guide_message}")

            if params:
                print(f"提取的参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
            else:
                print("提取的参数: 无")

            # 验证置信度
            if confidence == expected_confidence:
                print("✅ 置信度符合预期")
            else:
                print(f"❌ 置信度不符合预期 (预期: {expected_confidence}, 实际: {confidence})")

            # 验证优化3: medium/low 也应该提取参数
            if confidence in ["medium", "low"] and params:
                print("✅ 优化3验证通过: medium/low 场景也返回了提取的参数")

            # 验证优化4: 动态提示
            if confidence == "medium" and "请补充" in guide_message:
                print("✅ 优化4验证通过: 动态提示缺少的参数")
            elif confidence == "medium" and "请提供" in guide_message:
                print("✅ 优化4验证通过: 动态提示需要的参数")

            return result

        except Exception as e:
            print(f"❌ 请求失败: {str(e)}")
            return None


async def main():
    """运行所有测试用例"""
    print("优化3和优化4测试")
    print("="*60)

    # 测试1: 高置信度 - 完整参数
    await test_case(
        "高置信度 - 完整参数",
        "使用EVO2帮我预测一下这个序列：AGCTTCATCTAACTACATCTACATCTACTA",
        "high"
    )

    # 测试2: 中置信度 - 只说任务名，没有序列
    await test_case(
        "中置信度 - 只说任务名",
        "我想做变异打分",
        "medium"
    )

    # 测试3: 中置信度 - 有序列，缺少其他参数
    await test_case(
        "中置信度 - 有序列缺位置",
        "变异打分，序列是AGCTTCATCTAACTACATCTACATCTACTA",
        "medium"
    )

    # 测试4: 中置信度 - 掩码预测，有序列缺位置
    await test_case(
        "中置信度 - 掩码预测缺位置",
        "掩码预测，序列是AGCTTCATCTAACTACATCTACATCTACTA",
        "medium"
    )

    # 测试5: 低置信度 - 模糊输入但有序列
    await test_case(
        "低置信度 - 模糊输入有序列",
        "帮我分析一下这个序列AGCTTCATCTAACTACATCTACATCTACTA",
        "low"
    )

    # 测试6: 低置信度 - 完全模糊
    await test_case(
        "低置信度 - 完全模糊",
        "你好",
        "low"
    )

    print("\n" + "="*60)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(main())
