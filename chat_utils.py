"""
对话工具模块
包含API请求、消息处理、格式转换等核心功能
支持模拟输出和真实模型扩展接口
"""
import time
import re
import random
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

def simulate_response(user_message: str) -> Generator[str, None, None]:
    """
    模拟AI响应（用于演示和测试）
    支持流式输出，模拟真实对话体验
    
    Args:
        user_message: 用户输入的消息
        
    Yields:
        模拟的响应文本片段
    """
    # 预定义的响应模板
    responses = {
        "你好": "你好！很高兴见到你。我是一个智能对话助手，有什么可以帮助你的吗？",
        "你是谁": "我是一个智能对话Chatbot系统，基于Python和Streamlit开发。我可以和你进行对话，回答问题，提供帮助。",
        "功能": "我支持以下功能：\n1. 多轮对话，记住上下文\n2. 对话历史管理\n3. 导出对话记录\n4. 深色/浅色主题切换\n5. 后续可扩展接入真实AI模型",
        "帮助": "我可以帮助你：\n• 回答问题\n• 进行对话交流\n• 提供信息查询\n• 记录对话历史\n\n你可以随时查看历史对话或导出记录。",
    }
    
    # 默认响应
    default_responses = [
        "这是一个很有趣的问题！让我想想...\n\n作为模拟助手，我会尽力回答你的问题。不过目前我运行在模拟模式下，后续可以接入真实的AI模型来获得更好的回答。",
        "我理解你的问题。虽然现在是模拟模式，但我可以和你进行基本的对话交流。\n\n如果你需要更智能的回答，可以配置真实的API密钥来接入OpenAI或其他模型。",
        "感谢你的提问！\n\n当前是演示模式，我可以：\n• 进行基本对话\n• 记住对话历史\n• 支持多轮交流\n\n要获得更智能的回复，请在侧边栏配置API密钥。",
    ]
    
    # 查找匹配的响应
    response = None
    for key, value in responses.items():
        if key in user_message:
            response = value
            break
    
    # 如果没有匹配，使用默认响应
    if not response:
        response = random.choice(default_responses)
    
    # 模拟流式输出（逐字输出）
    for char in response:
        yield char
        time.sleep(0.02)  # 模拟打字延迟

def call_deepseek_api(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    api_key: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    top_p: float = 1.0,
    stream: bool = True
) -> Generator[str, None, None]:
    """
    调用DeepSeek API进行对话
    DeepSeek API兼容OpenAI格式
    
    Args:
        messages: 消息列表
        model: 模型名称 (deepseek-chat 或 deepseek-coder)
        api_key: DeepSeek API密钥
        temperature: 温度参数
        max_tokens: 最大token数
        top_p: Top-p参数
        stream: 是否流式输出
        
    Yields:
        生成的文本片段
    """
    # DeepSeek API地址
    base_url = "https://api.deepseek.com/v1"
    
    # 复用OpenAI API调用逻辑
    for chunk in call_openai_api(
        messages=messages,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stream=stream
    ):
        yield chunk

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
    params: Dict[str, Any],
    use_simulation: bool = True,
    api_type: str = "deepseek"
) -> Generator[str, None, None]:
    """
    根据配置获取对应的响应生成器
    
    Args:
        messages: 消息列表
        model: 模型名称
        api_key: API密钥
        base_url: API基础URL
        params: 其他参数
        use_simulation: 是否使用模拟模式
        api_type: API类型 (deepseek/openai/anthropic)
        
    Yields:
        生成的文本片段
    """
    # 如果使用模拟模式或没有配置API密钥
    if use_simulation or not api_key:
        # 获取最后一条用户消息
        last_user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        
        return simulate_response(last_user_message)
    
    # 验证API密钥格式
    if not validate_api_key(api_key):
        yield "❌ API密钥无效！请检查您的API密钥是否正确。"
        last_user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        for chunk in simulate_response(last_user_message):
            yield chunk
        return
    
    # 真实API调用（预留扩展接口）
    try:
        # 根据api_type选择API（优先使用api_type）
        if api_type == "deepseek" or "deepseek" in model.lower():
            # DeepSeek模型
            yield "🔄 正在连接DeepSeek API..."
            return call_deepseek_api(
                messages=messages,
                model=model,
                api_key=api_key,
                **params
            )
        elif api_type == "anthropic" or "claude" in model.lower():
            # Anthropic Claude模型
            yield "🔄 正在连接Anthropic API..."
            return call_anthropic_api(
                messages=messages,
                model=model,
                api_key=api_key,
                **params
            )
        else:
            # OpenAI模型（默认）
            yield "🔄 正在连接OpenAI API..."
            return call_openai_api(
                messages=messages,
                model=model,
                api_key=api_key,
                base_url=base_url,
                **params
            )
    except ImportError as e:
        # 缺少依赖库
        error_msg = f"❌ 缺少必要的依赖库: {str(e)}\n\n请安装对应的库：\n- DeepSeek/OpenAI: pip install openai\n- Anthropic: pip install anthropic"
        yield error_msg
        last_user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        for chunk in simulate_response(last_user_message):
            yield chunk
    except Exception as e:
        # 如果API调用失败，回退到模拟模式
        error_msg = f"⚠️ API调用失败: {str(e)}\n\n可能的原因：\n• API密钥不正确或已过期\n• 网络连接问题\n• 模型名称错误\n• API配额不足\n\n已切换到模拟模式。"
        yield error_msg
        last_user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        for chunk in simulate_response(last_user_message):
            yield chunk

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
