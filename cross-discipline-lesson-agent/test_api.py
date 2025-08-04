#!/usr/bin/env python3
"""
测试 Innospark API 连接
"""

import requests
import json
from config.settings import INNOSPARK_API_KEY, INNOSPARK_API_URL


def test_api_connection():
    """测试API连接"""
    print("=== 测试 Innospark API 连接 ===")
    print(f"API URL: {INNOSPARK_API_URL}")
    print(f"API Key: {'已设置' if INNOSPARK_API_KEY != 'your_api_key_here' else '未设置'}")

    headers = {
        "Authorization": f"Bearer {INNOSPARK_API_KEY}",
        "Content-Type": "application/json"
    }

    # 简单的测试数据
    test_data = {
        "model": "InnoSpark-R",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False
    }

    print("\n发送测试请求...")

    try:
        # 设置较短的超时时间进行测试
        response = requests.post(
            INNOSPARK_API_URL,
            headers=headers,
            data=json.dumps(test_data),
            timeout=10  # 10秒超时
        )

        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            print("✓ API连接成功!")
            result = response.json()
            print("响应内容:", result)
        else:
            print(f"✗ API响应错误: {response.status_code}")
            print("错误内容:", response.text)

    except requests.exceptions.Timeout:
        print("✗ 连接超时 - API服务器响应太慢")
    except requests.exceptions.ConnectionError:
        print("✗ 连接错误 - 无法连接到API服务器")
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求错误: {e}")
    except Exception as e:
        print(f"✗ 其他错误: {e}")


if __name__ == "__main__":
    test_api_connection()