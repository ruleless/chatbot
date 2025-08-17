"""
配置文件 - 包含模型设置、系统配置等
"""

import os
from typing import Dict, List, Optional

class Config:
    """应用配置类"""

    # 基础配置
    APP_NAME = "AI ChatBot"
    DEBUG = False
    HOST = "127.0.0.1"
    PORT = 5000

    # Ollama配置
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODELS = [
        "llama3.1:8b",
        "deepseek-r1:8b",
        "gemma3:12b",
    ]
    DEFAULT_OLLAMA_MODEL = "llama3.1:8b"

    # 线上模型配置
    ONLINE_MODELS = {
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat"
        },
        "gemini": {
            "api_key": os.getenv("GEMINI_API_KEY", ""),
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "model": "gemini-pro"
        },
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo"
        }
    }
    DEFAULT_ONLINE_MODEL = "deepseek"

    # 对话配置
    MAX_HISTORY_LENGTH = 50  # 最大对话历史长度
    DEFAULT_SYSTEM_PROMPT = "你是一个专业的AI助手，请用中文回答用户的问题。"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 2000

    # Web界面配置
    WEB_TITLE = "AI 聊天助手"
    STREAMING_ENABLED = True

    @classmethod
    def get_available_models(cls) -> List[str]:
        """获取所有可用模型列表"""
        return cls.OLLAMA_MODELS + list(cls.ONLINE_MODELS.keys())

    @classmethod
    def get_model_config(cls, model_name: str) -> Optional[Dict]:
        """获取特定模型的配置"""
        if model_name in cls.OLLAMA_MODELS:
            return {
                "type": "ollama",
                "model_name": model_name,
                "base_url": cls.OLLAMA_BASE_URL
            }
        elif model_name in cls.ONLINE_MODELS:
            return {
                "type": "online",
                "provider": model_name,
                **cls.ONLINE_MODELS[model_name]
            }
        return None

    @classmethod
    def is_valid_model(cls, model_name: str) -> bool:
        """检查模型是否有效"""
        return model_name in cls.get_available_models()