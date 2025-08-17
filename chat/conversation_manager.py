"""
对话管理器 - 负责维护多轮对话上下文和历史记录
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.logger import logger
from utils.helpers import save_conversation_to_file, load_conversation_from_file


class ConversationManager:
    """对话管理器类"""

    def __init__(self, max_history_length: int = 50):
        """
        初始化对话管理器

        Args:
            max_history_length: 最大对话历史长度
        """
        self.max_history_length = max_history_length
        self.conversations = {}  # {conversation_id: conversation_data}
        logger.info("ConversationManager initialized")

    def create_conversation(self, system_prompt: Optional[str] = None) -> str:
        """
        创建新的对话

        Args:
            system_prompt: 系统提示

        Returns:
            str: 对话ID
        """
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = {
            "id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "system_prompt": system_prompt,
            "messages": [],
            "title": "新对话"
        }
        logger.info(f"Created new conversation: {conversation_id}")
        return conversation_id

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取对话信息

        Args:
            conversation_id: 对话ID

        Returns:
            Optional[Dict[str, Any]]: 对话信息，不存在则返回None
        """
        return self.conversations.get(conversation_id)

    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        获取对话消息列表

        Args:
            conversation_id: 对话ID

        Returns:
            List[Dict[str, str]]: 消息列表
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            return conversation["messages"]
        return []

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        update_title: bool = True
    ) -> bool:
        """
        添加消息到对话

        Args:
            conversation_id: 对话ID
            role: 消息角色 ("user" 或 "assistant")
            content: 消息内容
            update_title: 是否更新对话标题

        Returns:
            bool: 添加是否成功
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return False

        # 验证角色
        if role not in ["user", "assistant"]:
            logger.warning(f"Invalid message role: {role}")
            return False

        # 创建消息对象
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        # 添加消息
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.now().isoformat()

        # 如果是第一条用户消息，更新对话标题
        if update_title and role == "user" and len(conversation["messages"]) == 1:
            self._update_conversation_title(conversation_id, content)

        # 检查历史长度限制
        if len(conversation["messages"]) > self.max_history_length * 2:  # *2 因为包含用户和助手消息
            # 保留最近的对话，移除最早的对话对
            conversation["messages"] = conversation["messages"][-self.max_history_length * 2:]
            logger.info(f"Trimmed conversation {conversation_id} to max length")

        logger.info(f"Added {role} message to conversation {conversation_id}")
        return True

    def _update_conversation_title(self, conversation_id: str, first_message: str):
        """
        更新对话标题

        Args:
            conversation_id: 对话ID
            first_message: 第一条用户消息
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            # 截取前20个字符作为标题
            title = first_message[:20].strip()
            if len(first_message) > 20:
                title += "..."
            conversation["title"] = title
            logger.info(f"Updated conversation title: {title}")

    def update_system_prompt(self, conversation_id: str, system_prompt: str) -> bool:
        """
        更新系统提示

        Args:
            conversation_id: 对话ID
            system_prompt: 新的系统提示

        Returns:
            bool: 更新是否成功
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation["system_prompt"] = system_prompt
            conversation["updated_at"] = datetime.now().isoformat()
            logger.info(f"Updated system prompt for conversation {conversation_id}")
            return True
        return False

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话

        Args:
            conversation_id: 对话ID

        Returns:
            bool: 删除是否成功
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False

    def clear_conversation(self, conversation_id: str) -> bool:
        """
        清空对话消息（保留对话本身和系统提示）

        Args:
            conversation_id: 对话ID

        Returns:
            bool: 清空是否成功
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation["messages"] = []
            conversation["updated_at"] = datetime.now().isoformat()
            logger.info(f"Cleared messages in conversation {conversation_id}")
            return True
        return False

    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """
        获取所有对话列表（不包含消息内容）

        Returns:
            List[Dict[str, Any]]: 对话列表
        """
        conversations = []
        for conv_id, conv_data in self.conversations.items():
            # 创建不包含详细消息的对话摘要
            summary = {
                "id": conv_id,
                "title": conv_data["title"],
                "created_at": conv_data["created_at"],
                "updated_at": conv_data["updated_at"],
                "message_count": len(conv_data["messages"]),
                "system_prompt": conv_data["system_prompt"]
            }
            conversations.append(summary)

        # 按更新时间倒序排列
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations

    def export_conversation(self, conversation_id: str, format_type: str = "json") -> Optional[str]:
        """
        导出对话

        Args:
            conversation_id: 对话ID
            format_type: 导出格式 ("json" 或 "txt")

        Returns:
            Optional[str]: 导出的内容，失败返回None
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        try:
            if format_type == "json":
                return json.dumps(conversation, ensure_ascii=False, indent=2)
            elif format_type == "txt":
                return self._format_conversation_as_text(conversation)
            else:
                logger.warning(f"Unsupported export format: {format_type}")
                return None
        except Exception as e:
            logger.error(f"Failed to export conversation {conversation_id}: {str(e)}")
            return None

    def _format_conversation_as_text(self, conversation: Dict[str, Any]) -> str:
        """
        将对话格式化为文本

        Args:
            conversation: 对话数据

        Returns:
            str: 格式化后的文本
        """
        lines = []
        lines.append(f"对话标题: {conversation['title']}")
        lines.append(f"创建时间: {conversation['created_at']}")
        lines.append(f"更新时间: {conversation['updated_at']}")

        if conversation.get("system_prompt"):
            lines.append(f"系统提示: {conversation['system_prompt']}")

        lines.append("=" * 50)

        for msg in conversation["messages"]:
            role = "用户" if msg["role"] == "user" else "助手"
            timestamp = msg.get("timestamp", "")
            lines.append(f"[{timestamp}] {role}:")
            lines.append(msg["content"])
            lines.append("-" * 30)

        return "\n".join(lines)

    def save_conversation_to_file(self, conversation_id: str, filename: str) -> bool:
        """
        保存对话到文件

        Args:
            conversation_id: 对话ID
            filename: 文件名

        Returns:
            bool: 保存是否成功
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False

        return save_conversation_to_file(conversation, filename)

    def load_conversation_from_file(self, filename: str) -> Optional[str]:
        """
        从文件加载对话

        Args:
            filename: 文件名

        Returns:
            Optional[str]: 对话ID，加载失败返回None
        """
        conversation = load_conversation_from_file(filename)
        if not conversation:
            return None

        # 生成新的对话ID
        conversation_id = str(uuid.uuid4())
        conversation["id"] = conversation_id

        # 验证对话数据结构
        if not self._validate_conversation_data(conversation):
            logger.error("Invalid conversation data structure")
            return None

        self.conversations[conversation_id] = conversation
        logger.info(f"Loaded conversation from file: {filename}")
        return conversation_id

    def _validate_conversation_data(self, conversation: Dict[str, Any]) -> bool:
        """
        验证对话数据结构

        Args:
            conversation: 对话数据

        Returns:
            bool: 数据结构是否有效
        """
        required_fields = ["messages"]
        for field in required_fields:
            if field not in conversation:
                return False

        # 验证消息列表
        if not isinstance(conversation["messages"], list):
            return False

        for msg in conversation["messages"]:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in ["user", "assistant"]:
                return False

        return True

    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        获取对话统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total_conversations = len(self.conversations)
        total_messages = sum(len(conv["messages"]) for conv in self.conversations.values())

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_messages_per_conversation": total_messages / total_conversations if total_conversations > 0 else 0
        }