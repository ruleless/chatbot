"""
基础模型接口 - 定义所有模型实现的通用接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional
from utils.logger import logger


class BaseModel(ABC):
    """基础模型抽象类"""

    def __init__(self, model_name: str, **kwargs):
        """
        初始化模型

        Args:
            model_name: 模型名称
            **kwargs: 其他配置参数
        """
        self.model_name = model_name
        self.config = kwargs
        logger.info(f"Initializing model: {model_name}")

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Any:
        """
        发送聊天请求

        Args:
            messages: 消息历史列表
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大令牌数
            stream: 是否流式输出

        Returns:
            Any: 模型响应
        """
        pass

    @abstractmethod
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Iterator[str]:
        """
        流式聊天请求

        Args:
            messages: 消息历史列表
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大令牌数

        Returns:
            Iterator[str]: 流式响应迭代器
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查模型是否可用

        Returns:
            bool: 模型是否可用
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息字典
        """
        pass

    def format_messages(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        格式化消息列表，添加系统提示

        Args:
            messages: 原始消息列表
            system_prompt: 系统提示

        Returns:
            List[Dict[str, str]]: 格式化后的消息列表
        """
        formatted = []

        # 添加系统提示
        if system_prompt:
            formatted.append({
                "role": "system",
                "content": system_prompt
            })

        # 添加历史消息
        for msg in messages:
            if msg.get("role") in ["user", "assistant"]:
                formatted.append({
                    "role": msg["role"],
                    "content": msg.get("content", "")
                })

        return formatted

    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """
        验证消息格式

        Args:
            messages: 消息列表

        Returns:
            bool: 消息格式是否有效
        """
        if not isinstance(messages, list):
            return False

        # 允许空消息列表（新对话的情况）
        if not messages:
            return True

        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in ["user", "assistant", "system"]:
                return False

        return True

    def get_error_response(self, error_msg: str) -> Dict[str, Any]:
        """
        获取标准错误响应

        Args:
            error_msg: 错误消息

        Returns:
            Dict[str, Any]: 错误响应
        """
        return {
            "success": False,
            "error": error_msg,
            "model": self.model_name
        }


class ModelFactory:
    """模型工厂类"""

    _models = {}

    @classmethod
    def register_model(cls, model_type: str, model_class):
        """
        注册模型类

        Args:
            model_type: 模型类型
            model_class: 模型类
        """
        cls._models[model_type] = model_class
        logger.info(f"Registered model type: {model_type}")

    @classmethod
    def create_model(cls, model_type: str, model_name: str, **kwargs) -> Optional[BaseModel]:
        """
        创建模型实例

        Args:
            model_type: 模型类型
            model_name: 模型名称
            **kwargs: 配置参数

        Returns:
            Optional[BaseModel]: 模型实例，创建失败返回None
        """
        if model_type not in cls._models:
            logger.error(f"Unknown model type: {model_type}")
            return None

        try:
            model_class = cls._models[model_type]
            return model_class(model_name, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create model {model_name}: {str(e)}")
            return None

    @classmethod
    def get_available_model_types(cls) -> List[str]:
        """
        获取可用的模型类型

        Returns:
            List[str]: 模型类型列表
        """
        return list(cls._models.keys())