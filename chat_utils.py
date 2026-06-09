"""
对话工具模块
包含API请求、消息处理、格式转换等核心功能
"""
import time
import re
from typing import Generator, List, Dict, Any, Optional
from config import config

def validate_message(message: str, max_length: int = 4000) -> tuple[bool, str]:
    """
    验证消息格式和长度
    
    Args:
        message: 消息内容
        max_length: 最大长度限制
        
    Returns:
        (是否有效, 错误信息)
    """
    if not message or not message.strip():
        return False, "消息不能为空"
    
    if len(message) > max_length:
        return False, f"消息长度不能超过{max_length}个字符"
    
    return True, ""

def clean_message(message: str) -> str:
    """
    清理消息内容
    
    Args:
        message: 原始消息
        
    Returns:
        清理后的消息
    """
    # 去除首尾空白
    message = message.strip()
    
    # 移除可能的控制字符
    message = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', message)
    
    return message

def build_messages(messages: List[Dict[str, str]], system_prompt: str = None) -> List[Dict[str, str]]:
    """
    构建API请求所需的消息列表
    
    Args:
        messages: 历史消息列表
        system_prompt: 系统提示词
        
    Returns:
        构建好的消息列表
    """
    result = []
    
    # 添加系统提示词
    if system_prompt:
        result.append({
            "role": "system",
            "content": system_prompt
        })
    
    # 添加历史消息
    result.extend(messages)
    
    return result

def call_openai_api(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    api_key: str = None,
    base_url: str = "https://api.openai.com/v1",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    stream: bool = True
) -> Generator[str, None, None]:
    """
    调用OpenAI API进行对话
    
    Args:
        messages: 消息列表
        model: 模型名称
        api_key: API密钥
        base_url: API基础URL
        temperature: 温度参数
        max_tokens: 最大token数
        top_p: Top-p参数
        frequency_penalty: 频率惩罚
        presence_penalty: 存在惩罚
        stream: 是否流式输出
        
    Yields:
        生成的文本片段
    """
    try:
        import openai
        
        # 配置API密钥和基础URL
        openai.api_key = api_key
        openai.api_base = base_url
        
        # 构建请求参数
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": stream
        }
        
        # 移除None值
        params = {k: v for k, v in params.items() if v is not None}
        
        # 发起请求
        response = openai.ChatCompletion.create(**params)
        
        if stream:
            # 流式响应
            for chunk in response:
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
        else:
            # 非流式响应
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                yield content
                
    except ImportError:
        yield "请安装 openai 库: pip install openai"
    except Exception as e:
        yield f"API请求失败: {str(e)}"

def call_anthropic_api(
    messages: List[Dict[str, str]],
    model: str = "claude-3-sonnet-20240229",
    api_key: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    stream: bool = True
) -> Generator[str, None, None]:
    """
    调用Anthropic Claude API
    
    Args:
        messages: 消息列表
        model: 模型名称
        api_key: API密钥
        temperature: 温度参数
        max_tokens: 最大token数
        stream: 是否流式输出
        
    Yields:
        生成的文本片段
    """
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # 将消息格式转换为Claude格式
        text_messages = []
        system_prompt = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                text_messages.append(msg)
        
        params = {
            "model": model,
            "messages": text_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if system_prompt:
            params["system"] = system_prompt
        
        with client.messages.stream(**params) as stream:
            for text in stream.text_stream:
                yield text
                
    except ImportError:
        yield "请安装 anthropic 库: pip install anthropic"
    except Exception as e:
        yield f"API请求失败: {str(e)}"

def get_response_generator(
    messages: List[Dict[str, str]],
    model: str,
    api_key: str,
    base_url: str,
    params: Dict[str, Any]
) -> Generator[str, None, None]:
    """
    根据模型类型获取对应的响应生成器
    
    Args:
        messages: 消息列表
        model: 模型名称
        api_key: API密钥
        base_url: API基础URL
        params: 其他参数
        
    Yields:
        生成的文本片段
    """
    # 根据模型类型选择API
    if "claude" in model.lower():
        return call_anthropic_api(
            messages=messages,
            model=model,
            api_key=api_key,
            **params
        )
    else:
        return call_openai_api(
            messages=messages,
            model=model,
            api_key=api_key,
            base_url=base_url,
            **params
        )

def format_timestamp(timestamp: str = None) -> str:
    """
    格式化时间戳
    
    Args:
        timestamp: ISO格式时间戳，默认为当前时间
        
    Returns:
        格式化的时间字符串
    """
    from datetime import datetime
    
    if timestamp:
        dt = datetime.fromisoformat(timestamp)
    else:
        dt = datetime.now()
    
    return dt.strftime("%Y年%m月%d日 %H:%M")

def count_tokens(text: str) -> int:
    """
    简单估算token数量（英文约4字符1token，中文约2字符1token）
    
    Args:
        text: 文本内容
        
    Returns:
        估算的token数量
    """
    # 简单的估算方法
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(text) - chinese_chars
    
    return int(chinese_chars * 0.5 + english_chars * 0.25)

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 文本内容
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_safe_filename(title: str) -> str:
    """
    将标题转换为安全的文件名
    
    Args:
        title: 原始标题
        
    Returns:
        安全的文件名
    """
    # 替换不安全字符
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    # 限制长度
    safe = safe[:50]
    return safe.strip() or "conversation"
