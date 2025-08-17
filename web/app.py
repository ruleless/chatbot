"""
Flask Web应用主文件
提供Web界面和API接口
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
from typing import Dict, Any, Optional

from config import Config
from models.base_model import ModelFactory
from chat.conversation_manager import ConversationManager
from utils.logger import logger
from utils.helpers import validate_model_name, sanitize_input


class WebApp:
    """Web应用类"""

    def __init__(self):
        """初始化Web应用"""
        self.app = Flask(__name__)
        self.app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
        CORS(self.app)

        # 初始化组件
        self.conversation_manager = ConversationManager(Config.MAX_HISTORY_LENGTH)
        self.current_model = None
        self.current_model_name = Config.DEFAULT_OLLAMA_MODEL

        # 注册路由
        self._register_routes()

        logger.info("WebApp initialized")

    def _register_routes(self):
        """注册路由"""

        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')

        @self.app.route('/api/models', methods=['GET'])
        def get_models():
            """获取可用模型列表"""
            try:
                available_models = Config.get_available_models()
                model_configs = {}

                for model in available_models:
                    config = Config.get_model_config(model)
                    if config:
                        model_configs[model] = config

                return jsonify({
                    "success": True,
                    "models": available_models,
                    "configs": model_configs,
                    "current_model": self.current_model_name
                })
            except Exception as e:
                logger.error(f"Failed to get models: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/models/<model_name>', methods=['POST'])
        def set_model(model_name):
            """设置当前模型"""
            try:
                # 验证模型名称
                if not self._validate_model_name(model_name):
                    return jsonify({
                        "success": False,
                        "error": f"Invalid model name: {model_name}"
                    }), 400

                # 创建模型实例
                creation_result = self._create_model_instance(model_name)
                if not creation_result["success"]:
                    return jsonify(creation_result["response"]), creation_result["status"]

                self.current_model_name = model_name
                logger.info(f"Model set to: {model_name}")

                return jsonify({
                    "success": True,
                    "model": model_name,
                    "available": self.current_model.is_available()
                })

            except Exception as e:
                logger.error(f"Failed to set model: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/conversations', methods=['GET'])
        def get_conversations():
            """获取对话列表"""
            try:
                conversations = self.conversation_manager.get_all_conversations()
                return jsonify({
                    "success": True,
                    "conversations": conversations
                })
            except Exception as e:
                logger.error(f"Failed to get conversations: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/conversations', methods=['POST'])
        def create_conversation():
            """创建新对话"""
            try:
                data = request.get_json()
                system_prompt = data.get('system_prompt', Config.DEFAULT_SYSTEM_PROMPT)

                conversation_id = self.conversation_manager.create_conversation(system_prompt)

                return jsonify({
                    "success": True,
                    "conversation_id": conversation_id
                })
            except Exception as e:
                logger.error(f"Failed to create conversation: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/conversations/<conversation_id>', methods=['GET'])
        def get_conversation(conversation_id):
            """获取对话详情"""
            try:
                conversation = self.conversation_manager.get_conversation(conversation_id)
                if not conversation:
                    return jsonify({
                        "success": False,
                        "error": "Conversation not found"
                    }), 404

                return jsonify({
                    "success": True,
                    "conversation": conversation
                })
            except Exception as e:
                logger.error(f"Failed to get conversation: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
        def delete_conversation(conversation_id):
            """删除对话"""
            try:
                success = self.conversation_manager.delete_conversation(conversation_id)
                if not success:
                    return jsonify({
                        "success": False,
                        "error": "Conversation not found"
                    }), 404

                return jsonify({"success": True})
            except Exception as e:
                logger.error(f"Failed to delete conversation: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/conversations/<conversation_id>/clear', methods=['POST'])
        def clear_conversation(conversation_id):
            """清空对话消息"""
            try:
                success = self.conversation_manager.clear_conversation(conversation_id)
                if not success:
                    return jsonify({
                        "success": False,
                        "error": "Conversation not found"
                    }), 404

                return jsonify({"success": True})
            except Exception as e:
                logger.error(f"Failed to clear conversation: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/conversations/<conversation_id>/chat', methods=['POST'])
        def chat(conversation_id):
            """发送聊天请求"""
            return self._handle_chat_request(conversation_id)

        @self.app.route('/api/conversations/<conversation_id>/system-prompt', methods=['PUT'])
        def update_system_prompt(conversation_id):
            """更新系统提示"""
            try:
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')

                success = self.conversation_manager.update_system_prompt(conversation_id, system_prompt)
                if not success:
                    return jsonify({
                        "success": False,
                        "error": "Conversation not found"
                    }), 404

                return jsonify({"success": True})
            except Exception as e:
                logger.error(f"Failed to update system prompt: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/conversations/<conversation_id>/export', methods=['GET'])
        def export_conversation(conversation_id):
            """导出对话"""
            try:
                format_type = request.args.get('format', 'json')
                content = self.conversation_manager.export_conversation(conversation_id, format_type)

                if not content:
                    return jsonify({
                        "success": False,
                        "error": "Conversation not found"
                    }), 404

                return jsonify({
                    "success": True,
                    "content": content,
                    "format": format_type
                })
            except Exception as e:
                logger.error(f"Failed to export conversation: {str(e)}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.errorhandler(404)
        def not_found(error):
            """404错误处理"""
            return jsonify({"success": False, "error": "Endpoint not found"}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            """500错误处理"""
            logger.error(f"Internal server error: {str(error)}")
            return jsonify({
                "success": False,
                "error": "Internal server error"
            }), 500

    def run(self, host: str = None, port: int = None):
        """运行Web应用"""
        host = host or Config.HOST
        port = port or Config.PORT

        # 使用 HTTP/1.1 协议运行应用
        self.app.run(host=host, port=port)

    def _validate_model_name(self, model_name: str) -> bool:
        """验证模型名称是否有效"""
        return validate_model_name(model_name, Config.get_available_models())

    def _create_model_instance(self, model_name: str) -> Dict[str, Any]:
        """创建模型实例"""
        # 获取模型配置
        model_config = Config.get_model_config(model_name)
        if not model_config:
            return {
                "success": False,
                "response": {
                    "success": False,
                    "error": f"Model configuration not found: {model_name}"
                },
                "status": 400
            }

        # 创建模型实例
        if model_config["type"] == "ollama":
            self.current_model = ModelFactory.create_model(
                "ollama",
                model_name,
                base_url=model_config["base_url"]
            )
        elif model_config["type"] == "online":
            # 创建在线模型实例，避免参数重复传递
            model_kwargs = {
                "provider": model_config["provider"],
                "api_key": model_config["api_key"],
                "base_url": model_config["base_url"],
                "model": model_config["model"]
            }
            self.current_model = ModelFactory.create_model(
                "online",
                model_config["model"],  # 使用实际的模型名称而不是provider名称
                **model_kwargs
            )

        if not self.current_model:
            return {
                "success": False,
                "response": {
                    "success": False,
                    "error": f"Failed to create model: {model_name}"
                },
                "status": 500
            }

        return {"success": True}

    def _parse_chat_request(self) -> Dict[str, Any]:
        """解析聊天请求"""
        data = request.get_json()
        message = data.get('message', '').strip()
        stream = data.get('stream', False)
        temperature = float(data.get('temperature', Config.DEFAULT_TEMPERATURE))
        max_tokens = int(data.get('max_tokens', Config.DEFAULT_MAX_TOKENS))

        if not message:
            return {
                "valid": False,
                "response": {
                    "success": False,
                    "error": "Message cannot be empty"
                },
                "status": 400
            }

        return {
            "valid": True,
            "message": sanitize_input(message),
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    def _prepare_chat_context(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """准备聊天上下文"""
        # 检查对话是否存在
        conversation = self.conversation_manager.get_conversation(conversation_id)
        if not conversation:
            # 如果对话不存在，创建新对话
            conversation_id = self.conversation_manager.create_conversation()
            messages = []
        else:
            # 获取对话历史
            messages = conversation["messages"]

        # 添加用户消息
        self.conversation_manager.add_message(
            conversation_id, "user", message
        )

        # 重新获取包含最新用户消息的完整对话历史
        messages = self.conversation_manager.get_conversation_messages(
            conversation_id
        )

        # 获取系统提示
        conversation = self.conversation_manager.get_conversation(
            conversation_id
        )
        system_prompt = conversation.get(
            "system_prompt",
            Config.DEFAULT_SYSTEM_PROMPT
        )

        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "system_prompt": system_prompt
        }

    def _handle_streaming_response(self, context: Dict[str, Any],
                                 temperature: float, max_tokens: int):
        """处理流式响应"""
        def generate_stream():
            try:
                full_response = ""
                for chunk in self.current_model.chat_stream(
                    messages=context["messages"],
                    system_prompt=context["system_prompt"],
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    # 处理每个数据块
                    result = self._process_stream_chunk(chunk, full_response)
                    if result.get("is_error"):
                        yield result["response"]
                        return

                    if result.get("is_complete"):
                        full_response = result["full_response"]
                        yield result["response"]
                    else:
                        full_response = result["full_response"]
                        yield result["response"]

                # 添加助手回复到对话历史
                self._save_assistant_response(context["conversation_id"], full_response)

                # 发送完成信号
                yield self._create_stream_response({'done': True})

            except Exception as e:
                yield self._create_stream_response(
                    {"success": False, "error": str(e)}
                )

        return self.app.response_class(
            generate_stream(),
            mimetype='text/event-stream'
        )

    def _process_stream_chunk(self, chunk: str, full_response: str) -> Dict[str, Any]:
        """处理流式数据块"""
        try:
            data = json.loads(chunk)

            if not isinstance(data, dict):
                return self._create_content_response(chunk, full_response)

            if "success" in data and not data["success"]:
                return {
                    "is_error": True,
                    "response": self._create_stream_response(data)
                }

            if "content" in data:
                content = data["content"]
                updated_response = full_response + content
                return {
                    "is_complete": True,
                    "full_response": updated_response,
                    "response": self._create_stream_response({'content': content})
                }

            return self._create_content_response(chunk, full_response)

        except json.JSONDecodeError:
            return self._create_content_response(chunk, full_response)

    def _create_content_response(self, content: str, full_response: str) -> Dict[str, Any]:
        """创建内容响应"""
        updated_response = full_response + content
        return {
            "is_complete": False,
            "full_response": updated_response,
            "response": self._create_stream_response({'content': content})
        }

    def _create_stream_response(self, data: Dict[str, Any]) -> str:
        """创建流式响应格式"""
        json_data = json.dumps(data, ensure_ascii=False)
        return f"data: {json_data}\n\n"

    def _save_assistant_response(self, conversation_id: str, response: str):
        """保存助手回复到对话历史"""
        if response.strip():
            self.conversation_manager.add_message(
                conversation_id,
                "assistant",
                response
            )

    def _handle_non_streaming_response(self, context: Dict[str, Any],
                                     temperature: float, max_tokens: int):
        """处理非流式响应"""
        response = self.current_model.chat(
            messages=context["messages"],
            system_prompt=context["system_prompt"],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )

        if response["success"]:
            # 添加助手回复到对话历史
            assistant_response = response["data"]["content"]
            self.conversation_manager.add_message(
                context["conversation_id"],
                "assistant",
                assistant_response
            )

            return jsonify({
                "success": True,
                "response": assistant_response,
                "conversation_id": context["conversation_id"]
            })
        else:
            return jsonify(response), 500

    def _handle_chat_request(self, conversation_id: str):
        """处理聊天请求"""
        try:
            if not self.current_model:
                return jsonify({
                    "success": False,
                    "error": "No model selected"
                }), 400

            # 解析请求
            parsed_request = self._parse_chat_request()
            if not parsed_request["valid"]:
                return parsed_request["response"], parsed_request["status"]

            # 准备上下文
            context = self._prepare_chat_context(
                conversation_id,
                parsed_request["message"]
            )

            # 根据请求类型处理响应
            if parsed_request["stream"]:
                return self._handle_streaming_response(
                    context,
                    parsed_request["temperature"],
                    parsed_request["max_tokens"]
                )
            else:
                return self._handle_non_streaming_response(
                    context,
                    parsed_request["temperature"],
                    parsed_request["max_tokens"]
                )

        except Exception as e:
            logger.error(f"Chat request failed: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500


def create_app() -> WebApp:
    """创建Web应用实例"""
    return WebApp()


app = create_app().app