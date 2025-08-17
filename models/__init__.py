"""
模型交互模块 - 提供统一的模型接口
"""

# 导入所有模型实现，这样它们就会自动注册到 ModelFactory
from models.ollama_model import OllamaModel
from models.online_model import OnlineModel