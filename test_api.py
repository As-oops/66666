#!/usr/bin/env python3
"""
API连接测试脚本
用于诊断DeepSeek API连接问题
"""
import sys
import os

def test_deepseek_api():
    try:
        import openai
        from openai import OpenAIError
        
        # 检查环境变量中的API密钥
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        
        if not api_key:
            print("ERROR: 未找到API密钥，请设置环境变量 DEEPSEEK_API_KEY")
            print("   或者在侧边栏中输入API密钥")
            return False
        
        print("Initializing OpenAI client...")
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            timeout=15
        )
        
        print("Connecting to DeepSeek API...")
        messages = [{"role": "user", "content": "Hello"}]
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=50,
            stream=False
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            print("SUCCESS: API连接成功!")
            print("   Response:", content[:50], "...")
            return True
        else:
            print("ERROR: API响应为空")
            return False
            
    except ImportError as e:
        print("ERROR: 导入错误:", e)
        print("   请安装openai库: pip install openai")
        return False
    except OpenAIError as e:
        print("ERROR: OpenAI错误:", e)
        return False
    except TimeoutError:
        print("ERROR: 请求超时，请检查网络连接")
        return False
    except Exception as e:
        print("ERROR: 未知错误:", type(e).__name__, ":", e)
        import traceback
        traceback.print_exc()
        return False

def test_network():
    """测试网络连接"""
    print("\nTesting network connection...")
    try:
        import urllib.request
        response = urllib.request.urlopen("https://api.deepseek.com/v1", timeout=10)
        print("SUCCESS: 网络连接正常")
        return True
    except Exception as e:
        print("ERROR: 网络连接失败:", e)
        return False

if __name__ == "__main__":
    print("="*50)
    print("DeepSeek API Connection Test")
    print("="*50)
    
    # 测试网络
    test_network()
    
    print("\n" + "="*50)
    
    # 测试API
    test_deepseek_api()
