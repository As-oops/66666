"""
配置管理模块
负责加载、保存和管理应用程序的配置参数
"""
import json
import os
from typing import Dict, Any, Optional

class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        从文件加载配置
        
        Returns:
            配置字典
        """
        default_config = {
            "api_key": "",
            "selected_model": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1",
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "theme": "light",
            "system_prompt": "你是星期八，一个友好、有趣的AI助手。请用中文进行回复。",
            "api_type": "deepseek",
            "use_simulation": False,
            "context_memory_limit": 10  # 默认保留最近10条历史消息
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        return default_config
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            是否保存成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        批量更新配置
        
        Args:
            updates: 要更新的配置字典
        """
        self.config.update(updates)

# 全局配置实例
config = Config()

def get_available_models() -> list:
    """
    获取可用的模型列表
    
    Returns:
        模型列表
    """
    return [
        # DeepSeek模型
        {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "DeepSeek"},
        {"id": "deepseek-coder", "name": "DeepSeek Coder", "provider": "DeepSeek"},
        # OpenAI模型
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "OpenAI"},
        {"id": "gpt-4", "name": "GPT-4", "provider": "OpenAI"},
        {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo", "provider": "OpenAI"},
        # Anthropic模型
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "Anthropic"},
        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "provider": "Anthropic"},
        # 本地模型
        {"id": "local-model", "name": "本地模型", "provider": "自定义"}
    ]

def get_default_params() -> Dict[str, Any]:
    """
    获取默认参数配置
    
    Returns:
        默认参数字典
    """
    return {
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }

def validate_api_key(api_key: str) -> bool:
    """
    验证API密钥格式
    
    Args:
        api_key: API密钥
        
    Returns:
        是否有效
    """
    if not api_key:
        return False
    # 基本的格式验证（根据不同API调整）
    return len(api_key) >= 20

def get_theme_colors(theme: str) -> Dict[str, str]:
    """
    获取主题颜色配置
    
    Args:
        theme: 主题名称 ('light' 或 'dark')
        
    Returns:
        颜色配置字典
    """
    themes = {
        "light": {
            "background": "#ffffff",
            "secondary_background": "#f0f2f6",
            "text": "#31333f",
            "user_bubble": "#dcf8c6",
            "assistant_bubble": "#ffffff",
            "border": "#e0e0e0",
            "primary": "#ff4b4b"
        },
        "dark": {
            "background": "#1a1a2e",
            "secondary_background": "#16213e",
            "text": "#e0e0e0",
            "user_bubble": "#4a7c59",
            "assistant_bubble": "#2d3436",
            "border": "#3d3d5c",
            "primary": "#ff6b6b"
        }
    }
    return themes.get(theme, themes["light"])
