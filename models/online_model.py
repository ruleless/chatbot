"""
线上模型实现 - 支持DeepSeek、Gemini、OpenAI等线上模型调用
"""

import json
import requests
from typing import List, Dict, Any, Iterator, Optional
from models.base_model import BaseModel, ModelFactory
from utils.logger import logger
from utils.helpers import create_error_response, create_success_response


class OnlineModel(BaseModel):
    """线上模型实现类"""

    def __init__(self, model_name: str, base_url: str, **kwargs):
        """
        初始化线上模型

        Args:
            model_name: 模型名称
            base_url: API基础URL
            **kwargs: 其他配置参数，包括 provider 和 api_key
        """
        super().__init__(model_name, **kwargs)
        self.provider = kwargs.get('provider')
        self.api_key = kwargs.get('api_key')
        self.base_url = base_url.rstrip('/')
        self.headers = self._build_headers()

    def _build_headers(self) -> Dict[str, str]:
        """
        构建请求头

        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = {
            "Content-Type": "application/json"
        }

        if self.provider == "deepseek":
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == "openai":
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == "gemini":
            # Gemini使用不同的认证方式
            pass

        return headers

    def is_available(self) -> bool:
        """
        检查线上模型是否可用

        Returns:
            bool: 模型是否可用
        """
        if not self.api_key:
            logger.warning(f"No API key provided for {self.provider}")
            return False

        try:
            # 发送简单的测试请求
            test_messages = [{"role": "user", "content": "Hello"}]

            if self.provider in ["deepseek", "openai"]:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model_name,
                        "messages": test_messages,
                        "max_tokens": 1
                    },
                    headers=self.headers,
                    timeout=10
                )
                return response.status_code == 200

            elif self.provider == "gemini":
                # Gemini的API格式不同
                response = requests.post(
                    f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": "Hello"}]}],
                        "generationConfig": {"maxOutputTokens": 1}
                    },
                    timeout=10
                )
                return response.status_code == 200

            return False

        except Exception as e:
            logger.error(f"{self.provider} model availability check failed: {str(e)}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "name": self.model_name,
            "type": "online",
            "provider": self.provider,
            "base_url": self.base_url,
            "available": self.is_available()
        }

    def _format_messages_for_provider(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> Any:
        """
        根据提供商格式化消息

        Args:
            messages: 消息列表
            system_prompt: 系统提示

        Returns:
            Any: 格式化后的消息
        """
        formatted_messages = self.format_messages(messages, system_prompt)

        if self.provider in ["deepseek", "openai"]:
            return formatted_messages
        elif self.provider == "gemini":
            # Gemini使用不同的消息格式
            gemini_messages = []
            for msg in formatted_messages:
                if msg["role"] == "system":
                    # 将系统提示添加到第一条用户消息中
                    if gemini_messages and gemini_messages[-1]["role"] == "user":
                        system_content = f"{msg['content']}\n\n"
                        current_text = gemini_messages[-1]["parts"][0]["text"]
                        gemini_messages[-1]["parts"][0]["text"] = system_content + current_text
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_messages.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })
            return gemini_messages

        return formatted_messages

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
            return create_error_response(f"{self.provider} model '{self.model_name}' is not available")

        try:
            if self.provider in ["deepseek", "openai"]:
                return self._chat_openai_style(messages, system_prompt, temperature, max_tokens, stream)
            elif self.provider == "gemini":
                return self._chat_gemini_style(messages, system_prompt, temperature, max_tokens, stream)
            else:
                return create_error_response(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"{self.provider} chat request failed: {str(e)}")
            return create_error_response(f"Request failed: {str(e)}")

    def _chat_openai_style(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """OpenAI风格API调用"""

        formatted_messages = self._format_messages_for_provider(messages, system_prompt)

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=self.headers,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            if stream:
                return create_success_response({"stream": True})
            else:
                return create_success_response({
                    "content": result["choices"][0]["message"]["content"],
                    "total_tokens": result.get("usage", {}).get("total_tokens", 0),
                    "model": result.get("model", self.model_name)
                })
        else:
            error_response = response.json().get("error", {})
            error_msg = error_response.get("message", f"API error: {response.status_code}")
            return create_error_response(error_msg)

    def _chat_gemini_style(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Gemini风格API调用"""

        formatted_messages = self._format_messages_for_provider(messages, system_prompt)

        payload = {
            "contents": formatted_messages,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"

        response = requests.post(
            url,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                return create_success_response({
                    "content": content,
                    "model": self.model_name
                })
            else:
                return create_error_response("No response content from Gemini")
        else:
            error_response = response.json().get("error", {})
            error_msg = error_response.get("message", f"API error: {response.status_code}")
            return create_error_response(error_msg)

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
            error_response = create_error_response("Invalid message format")
            yield json.dumps(error_response, ensure_ascii=False)
            return

        if not self.is_available():
            error_msg = f"{self.provider} model '{self.model_name}' is not available"
            error_response = create_error_response(error_msg)
            yield json.dumps(error_response, ensure_ascii=False)
            return

        try:
            if self.provider in ["deepseek", "openai"]:
                yield from self._chat_stream_openai_style(messages, system_prompt, temperature, max_tokens)
            elif self.provider == "gemini":
                yield from self._chat_stream_gemini_style(messages, system_prompt, temperature, max_tokens)
            else:
                error_msg = f"Unsupported provider: {self.provider}"
                error_response = create_error_response(error_msg)
                yield json.dumps(error_response, ensure_ascii=False)

        except Exception as e:
            logger.error(f"{self.provider} stream chat request failed: {str(e)}")
            error_msg = f"Stream request failed: {str(e)}"
            error_response = create_error_response(error_msg)
            yield json.dumps(error_response, ensure_ascii=False)

    def _chat_stream_openai_style(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Iterator[str]:
        """OpenAI风格流式API调用"""

        formatted_messages = self._format_messages_for_provider(messages, system_prompt)

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=self.headers,
            stream=True,
            timeout=60
        )

        if response.status_code != 200:
            error_msg = f"Stream API error: {response.status_code}"
            error_response = create_error_response(error_msg)
            yield json.dumps(error_response, ensure_ascii=False)
            return

        yield from self._process_stream_response(response)

    def _process_stream_response(self, response) -> Iterator[str]:
        """处理流式响应数据"""
        for line in response.iter_lines():
            if not line:
                continue

            line_text = line.decode('utf-8')
            if not line_text.startswith("data: "):
                continue

            data_str = line_text[6:]  # 移除 "data: " 前缀
            if data_str == "[DONE]":
                break

            content = self._extract_content_from_stream_data(data_str)
            if content:
                yield content

    def _extract_content_from_stream_data(self, data_str: str) -> Optional[str]:
        """从流式数据中提取内容"""
        try:
            data = json.loads(data_str)
            if "choices" not in data or len(data["choices"]) == 0:
                return None

            delta = data["choices"][0].get("delta", {})
            return delta.get("content", "")
        except json.JSONDecodeError:
            return None

    def _chat_stream_gemini_style(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Iterator[str]:
        """Gemini流式API调用（简化版，Gemini的流式API较复杂）"""

        # Gemini的流式API实现较复杂，这里先使用非流式方式
        result = self._chat_gemini_style(messages, system_prompt, temperature, max_tokens, False)
        if result["success"]:
            content = result["data"]["content"]
            # 模拟流式输出，按字符逐个返回
            for char in content:
                yield char
        else:
            yield json.dumps(result, ensure_ascii=False)


# 注册线上模型类型
ModelFactory.register_model("online", OnlineModel)