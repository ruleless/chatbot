"""
辅助函数模块 - 提供通用的工具函数
"""

import json
import re
from typing import List, Dict, Any, Optional
from utils.logger import logger


def validate_model_name(model_name: str, available_models: List[str]) -> bool:
    """
    验证模型名称是否有效

    Args:
        model_name: 要验证的模型名称
        available_models: 可用模型列表

    Returns:
        bool: 是否有效
    """
    if not model_name or not isinstance(model_name, str):
        return False
    return model_name in available_models


def sanitize_input(text: str) -> str:
    """
    清理用户输入，移除潜在的危险字符

    Args:
        text: 输入文本

    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""

    # 移除控制字符，保留基本标点
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    return sanitized.strip()


def format_conversation_history(history: List[Dict[str, str]]) -> str:
    """
    格式化对话历史记录

    Args:
        history: 对话历史列表，每个元素包含role和content

    Returns:
        str: 格式化后的对话历史
    """
    if not history:
        return ""

    formatted = []
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")

    return "\n".join(formatted)


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    截断文本到指定长度

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def save_conversation_to_file(history: List[Dict[str, str]], filename: str) -> bool:
    """
    保存对话历史到文件

    Args:
        history: 对话历史
        filename: 文件名

    Returns:
        bool: 是否保存成功
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.info(f"Conversation saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save conversation: {str(e)}")
        return False


def load_conversation_from_file(filename: str) -> Optional[List[Dict[str, str]]]:
    """
    从文件加载对话历史

    Args:
        filename: 文件名

    Returns:
        Optional[List[Dict[str, str]]]: 对话历史，加载失败返回None
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            history = json.load(f)
        logger.info(f"Conversation loaded from {filename}")
        return history
    except Exception as e:
        logger.error(f"Failed to load conversation: {str(e)}")
        return None


def parse_model_response(response: str) -> str:
    """
    解析模型响应，提取主要内容

    Args:
        response: 模型原始响应

    Returns:
        str: 解析后的内容
    """
    if not response:
        return ""

    # 移除多余的空白字符
    cleaned = re.sub(r'\s+', ' ', response.strip())
    return cleaned


def create_error_response(error_message: str, error_type: str = "general") -> Dict[str, Any]:
    """
    创建标准错误响应格式

    Args:
        error_message: 错误消息
        error_type: 错误类型

    Returns:
        Dict[str, Any]: 错误响应字典
    """
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": error_message
        },
        "timestamp": str(re.sub(r'\.\d+', '', str(__import__('datetime').datetime.now())))
    }


def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """
    创建标准成功响应格式

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        Dict[str, Any]: 成功响应字典
    """
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": str(re.sub(r'\.\d+', '', str(__import__('datetime').datetime.now())))
    }