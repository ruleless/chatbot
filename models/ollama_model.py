"""
Ollama模型实现 - 支持本地Ollama模型调用
"""

import json
import requests
from typing import List, Dict, Any, Iterator, Optional
from models.base_model import BaseModel, ModelFactory
from utils.logger import logger
from utils.helpers import create_error_response, create_success_response


class OllamaModel(BaseModel):
    """Ollama模型实现类"""

    def __init__(self, model_name: str, base_url: str = "http://localhost:11434", **kwargs):
        """
        初始化Ollama模型

        Args:
            model_name: 模型名称
            base_url: Ollama服务地址
            **kwargs: 其他配置参数
        """
        super().__init__(model_name, **kwargs)
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"

    def is_available(self) -> bool:
        """
        检查Ollama服务是否可用

        Returns:
            bool: 服务是否可用
        """
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                return self.model_name in available_models
            return False
        except Exception as e:
            logger.error(f"Ollama service check failed: {str(e)}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "name": self.model_name,
            "type": "ollama",
            "base_url": self.base_url,
            "available": self.is_available()
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        发送聊天请求

        Args:
            messages: 消息历史列表
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大令牌数
            stream: 是否流式输出

        Returns:
            Dict[str, Any]: 模型响应
        """
        if not self.validate_messages(messages):
            return create_error_response("Invalid message format")

        if not self.is_available():
            return create_error_response(f"Ollama service or model '{self.model_name}' is not available")

        try:
            # 格式化消息
            formatted_messages = self.format_messages(messages, system_prompt)

            # 构建请求数据
            payload = {
                "model": self.model_name,
                "messages": formatted_messages,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            response = requests.post(
                f"{self.api_url}/chat",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                if stream:
                    return create_success_response({"stream": True})
                else:
                    result = response.json()
                    return create_success_response({
                        "content": result.get("message", {}).get("content", ""),
                        "total_duration": result.get("total_duration", 0),
                        "load_duration": result.get("load_duration", 0),
                        "eval_count": result.get("eval_count", 0)
                    })
            else:
                return create_error_response(f"Ollama API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Ollama chat request failed: {str(e)}")
            return create_error_response(f"Request failed: {str(e)}")

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
        if not self.validate_messages(messages):
            yield json.dumps(
                create_error_response("Invalid message format"),
                ensure_ascii=False
            )
            return

        if not self.is_available():
            error_msg = f"Ollama service or model '{self.model_name}' is not available"
            yield json.dumps(
                create_error_response(error_msg),
                ensure_ascii=False
            )
            return

        try:
            # 格式化消息
            formatted_messages = self.format_messages(messages, system_prompt)

            # 构建请求数据
            payload = {
                "model": self.model_name,
                "messages": formatted_messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            response = requests.post(
                f"{self.api_url}/chat",
                json=payload,
                stream=True,
                timeout=60
            )

            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code}"
                yield json.dumps(
                    create_error_response(error_msg),
                    ensure_ascii=False
                )
                return

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    data = json.loads(line.decode('utf-8'))
                    content = self._extract_content_from_stream_data(data)
                    if content:  # 只返回非空内容
                        yield content
                except json.JSONDecodeError as e:
                    warning_msg = f"Failed to parse stream data: {str(e)}"
                    logger.warning(warning_msg)
                    continue

        except Exception as e:
            error_msg = f"Ollama stream chat request failed: {str(e)}"
            logger.error(error_msg)
            yield json.dumps(
                create_error_response(f"Stream request failed: {str(e)}"),
                ensure_ascii=False
            )

    def _extract_content_from_stream_data(self, data: Dict[str, Any]) -> Optional[str]:
        """
        从流式数据中提取内容

        Args:
            data: 流式响应数据

        Returns:
            Optional[str]: 提取的内容，如果没有则返回None
        """
        message = data.get("message", {})
        return message.get("content") if isinstance(message, dict) else None

    def get_available_models(self) -> List[str]:
        """
        获取可用的Ollama模型列表

        Returns:
            List[str]: 可用模型列表
        """
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
            return []


# 注册Ollama模型类型
ModelFactory.register_model("ollama", OllamaModel)