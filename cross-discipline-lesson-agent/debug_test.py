#!/usr/bin/env python3
"""
调试脚本 - 测试各个组件
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试所有模块导入"""
    print("=== 测试模块导入 ===")

    try:
        from app.models import LessonRequest, LessonModification, MediaRequest
        print("✓ 模型导入成功")
    except Exception as e:
        print(f"✗ 模型导入失败: {e}")
        return False

    try:
        from config.settings import INNOSPARK_API_KEY, INNOSPARK_API_URL
        print("✓ 配置导入成功")
        print(f"  API URL: {INNOSPARK_API_URL}")
        print(f"  API Key: {'已设置' if INNOSPARK_API_KEY != 'your_api_key_here' else '未设置'}")
    except Exception as e:
        print(f"✗ 配置导入失败: {e}")
        return False

    try:
        from app.api.innospark import InnosparkClient
        print("✓ Innospark 客户端导入成功")
    except Exception as e:
        print(f"✗ Innospark 客户端导入失败: {e}")
        return False

    try:
        from app.main import app
        print("✓ FastAPI 应用导入成功")
    except Exception as e:
        print(f"✗ FastAPI 应用导入失败: {e}")
        return False

    return True


def test_pydantic_models():
    """测试 Pydantic 模型"""
    print("\n=== 测试 Pydantic 模型 ===")

    try:
        from app.models import LessonRequest

        # 测试正常创建
        lesson_req = LessonRequest(
            grade="高中一年级",
            main_subject="物理",
            related_subjects=["数学", "化学"],
            estimated_hours=2,
            knowledge_goals=["理解牛顿第三定律", "掌握作用力与反作用力的应用"],
            academic_features="注重实验与理论结合"
        )
        print("✓ LessonRequest 模型创建成功")
        print(f"  转换为字典: {lesson_req.dict()}")

    except Exception as e:
        print(f"✗ LessonRequest 模型测试失败: {e}")
        return False

    return True


def test_api_connection():
    """测试 API 连接"""
    print("\n=== 测试 API 连接 ===")

    try:
        from app.api.innospark import InnosparkClient

        client = InnosparkClient()
        print("✓ Innospark 客户端初始化成功")

        # 测试连接（不实际调用 API）
        print(f"  API URL: {client.base_url}")
        print(f"  Headers: {client.headers}")

    except Exception as e:
        print(f"✗ API 连接测试失败: {e}")
        return False

    return True


def main():
    """主测试函数"""
    print("开始调试测试...\n")

    tests = [
        test_imports,
        test_pydantic_models,
        test_api_connection
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print(f"\n=== 测试结果 ===")
    if all_passed:
        print("✓ 所有测试通过，可以尝试启动服务")
    else:
        print("✗ 部分测试失败，需要修复问题后再启动服务")


if __name__ == "__main__":
    main()