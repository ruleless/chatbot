"""
命令行界面模块 - 提供基础的命令行交互功能
"""

import click
import sys
import os
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models.base_model import ModelFactory
from chat.conversation_manager import ConversationManager
from utils.logger import logger
from utils.helpers import validate_model_name, sanitize_input, format_conversation_history
import colorama
from colorama import Fore, Style, Back

# 初始化colorama
colorama.init()


class CLIApp:
    """命令行应用类"""

    def __init__(self):
        """初始化CLI应用"""
        self.conversation_manager = ConversationManager(Config.MAX_HISTORY_LENGTH)
        self.current_model = None
        self.current_model_name = Config.DEFAULT_OLLAMA_MODEL
        self.current_conversation_id = None
        self.running = True

        logger.info("CLI App initialized")

    def display_banner(self):
        """显示应用横幅"""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                 AI Chat Assistant - CLI Version               ║
║           Supports Local Ollama and Online Models             ║
╚═══════════════════════════════════════════════════════════════╝
        """
        print(Fore.CYAN + banner + Style.RESET_ALL)

    def display_help(self):
        """显示帮助信息"""
        help_text = """
Available commands:
  help, h     - Show this help information
  models, m   - List all available models
  set, s      - Set current model (usage: set <model_name>)
  new, n      - Create new conversation
  clear, c    - Clear current conversation
  history, hi - Show conversation history
  export, e   - Export current conversation (usage: export <filename>)
  prompt, p   - Set system prompt (usage: prompt <prompt_content>)
  quit, q     - Exit program

Type directly to chat with AI.
        """
        print(Fore.YELLOW + help_text + Style.RESET_ALL)

    def display_models(self):
        """显示可用模型列表"""
        print(Fore.GREEN + "\nAvailable models list:" + Style.RESET_ALL)
        models = Config.get_available_models()

        for i, model in enumerate(models, 1):
            status = "Default" if model == self.current_model_name else ""
            config = Config.get_model_config(model)
            model_type = config["type"] if config else "Unknown"

            print(f"  {i:2d}. {Fore.CYAN}{model}{Style.RESET_ALL} ({model_type}) {status}")

        print(f"\nCurrent model: {Fore.YELLOW}{self.current_model_name}{Style.RESET_ALL}")

    async def set_model(self, model_name: str):
        """设置当前模型"""
        if not validate_model_name(model_name, Config.get_available_models()):
            print(Fore.RED + f"Error: Invalid model name '{model_name}'" + Style.RESET_ALL)
            return False

        try:
            model_config = Config.get_model_config(model_name)
            if not model_config:
                print(Fore.RED + f"Error: Model configuration not found '{model_name}'" + Style.RESET_ALL)
                return False

            # 创建模型实例
            if model_config["type"] == "ollama":
                self.current_model = ModelFactory.create_model(
                    "ollama",
                    model_name,
                    base_url=model_config["base_url"]
                )
            elif model_config["type"] == "online":
                self.current_model = ModelFactory.create_model(
                    "online",
                    model_name,
                    provider=model_config["provider"],
                    api_key=model_config["api_key"],
                    base_url=model_config["base_url"],
                    model=model_config["model"]
                )

            if not self.current_model:
                print(Fore.RED + f"Error: Failed to create model instance '{model_name}'" + Style.RESET_ALL)
                return False

            # 检查模型是否可用
            if self.current_model.is_available():
                self.current_model_name = model_name
                print(Fore.GREEN + f"✓ Model set to: {model_name}" + Style.RESET_ALL)
                logger.info(f"Model set to: {model_name}")
                return True
            else:
                print(Fore.RED + f"Error: Model '{model_name}' is not available" + Style.RESET_ALL)
                return False

        except Exception as e:
            print(Fore.RED + f"Error: Failed to set model - {str(e)}" + Style.RESET_ALL)
            logger.error(f"Failed to set model: {str(e)}")
            return False

    def create_new_conversation(self, system_prompt: Optional[str] = None):
        """创建新对话"""
        if system_prompt is None:
            system_prompt = Config.DEFAULT_SYSTEM_PROMPT

        self.current_conversation_id = self.conversation_manager.create_conversation(system_prompt)
        print(Fore.GREEN + f"✓ New conversation created: {self.current_conversation_id}" + Style.RESET_ALL)
        print(Fore.BLUE + f"System prompt: {system_prompt}" + Style.RESET_ALL)

    def clear_current_conversation(self):
        """清空当前对话"""
        if not self.current_conversation_id:
            print(Fore.YELLOW + "No active conversation" + Style.RESET_ALL)
            return

        if self.conversation_manager.clear_conversation(self.current_conversation_id):
            print(Fore.GREEN + "✓ Conversation cleared" + Style.RESET_ALL)
        else:
            print(Fore.RED + "Error: Failed to clear conversation" + Style.RESET_ALL)

    def display_conversation_history(self):
        """显示对话历史"""
        if not self.current_conversation_id:
            print(Fore.YELLOW + "No active conversation" + Style.RESET_ALL)
            return

        messages = self.conversation_manager.get_conversation_messages(self.current_conversation_id)
        if not messages:
            print(Fore.YELLOW + "No messages in current conversation" + Style.RESET_ALL)
            return

        print(Fore.GREEN + f"\nConversation history ({len(messages)} messages total):" + Style.RESET_ALL)
        print("-" * 60)

        for i, msg in enumerate(messages, 1):
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            timestamp = msg.get("timestamp", "")

            print(f"{Fore.CYAN}[{timestamp}]{Style.RESET_ALL} {Fore.YELLOW}{role}:{Style.RESET_ALL}")
            print(f"  {content}")
            if i < len(messages):
                print()

        print("-" * 60)

    def export_conversation(self, filename: str):
        """导出对话"""
        if not self.current_conversation_id:
            print(Fore.YELLOW + "No active conversation" + Style.RESET_ALL)
            return

        content = self.conversation_manager.export_conversation(self.current_conversation_id, "txt")
        if content:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(Fore.GREEN + f"✓ Conversation exported to: {filename}" + Style.RESET_ALL)
            except Exception as e:
                print(Fore.RED + f"Error: Export failed - {str(e)}" + Style.RESET_ALL)
        else:
            print(Fore.RED + "Error: Failed to export conversation" + Style.RESET_ALL)

    def set_system_prompt(self, prompt: str):
        """设置系统提示"""
        if not self.current_conversation_id:
            print(Fore.YELLOW + "Please create a conversation first" + Style.RESET_ALL)
            return

        if self.conversation_manager.update_system_prompt(self.current_conversation_id, prompt):
            print(Fore.GREEN + "✓ System prompt updated" + Style.RESET_ALL)
            print(Fore.BLUE + f"New prompt: {prompt}" + Style.RESET_ALL)
        else:
            print(Fore.RED + "Error: Failed to update system prompt" + Style.RESET_ALL)

    async def send_message(self, message: str):
        """发送消息并获取回复"""
        if not self.current_model:
            print(Fore.RED + "Error: Please select a model first" + Style.RESET_ALL)
            return

        if not self.current_conversation_id:
            self.create_new_conversation()

        # 清理输入
        message = sanitize_input(message)

        # 获取对话历史和系统提示
        messages = self.conversation_manager.get_conversation_messages(self.current_conversation_id)
        conversation = self.conversation_manager.get_conversation(self.current_conversation_id)
        system_prompt = conversation.get("system_prompt", Config.DEFAULT_SYSTEM_PROMPT)

        # 添加用户消息到对话历史
        self.conversation_manager.add_message(self.current_conversation_id, "user", message)

        # 显示用户消息
        print(f"\n{Fore.YELLOW}User:{Style.RESET_ALL} {message}")

        # 显示正在输入指示
        print(f"{Fore.BLUE}Assistant is thinking...{Style.RESET_ALL}", end="", flush=True)

        try:
            # 发送请求到模型
            response = self.current_model.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=Config.DEFAULT_TEMPERATURE,
                max_tokens=Config.DEFAULT_MAX_TOKENS,
                stream=False
            )

            # 清除"正在思考"提示
            print("\r" + " " * 50 + "\r", end="")

            if response["success"]:
                assistant_response = response["data"]["content"]

                # 添加助手回复到对话历史
                self.conversation_manager.add_message(self.current_conversation_id, "assistant", assistant_response)

                # 显示助手回复
                print(f"{Fore.CYAN}Assistant:{Style.RESET_ALL} {assistant_response}")
            else:
                print(Fore.RED + f"Error: {response['error']}" + Style.RESET_ALL)

        except Exception as e:
            print("\r" + " " * 50 + "\r", end="")
            print(Fore.RED + f"Error: Request failed - {str(e)}" + Style.RESET_ALL)
            logger.error(f"Chat request failed: {str(e)}")

        print()  # 添加空行分隔

    async def process_command(self, command: str, args: List[str]):
        """处理命令"""
        command = command.lower()

        if command in ["help", "h"]:
            self.display_help()

        elif command in ["models", "m"]:
            self.display_models()

        elif command in ["set", "s"]:
            if len(args) == 0:
                print(Fore.YELLOW + "Usage: set <model_name>" + Style.RESET_ALL)
                return
            await self.set_model(args[0])

        elif command in ["new", "n"]:
            self.create_new_conversation()

        elif command in ["clear", "c"]:
            self.clear_current_conversation()

        elif command in ["history", "hi"]:
            self.display_conversation_history()

        elif command in ["export", "e"]:
            if len(args) == 0:
                print(Fore.YELLOW + "Usage: export <filename>" + Style.RESET_ALL)
                return
            self.export_conversation(args[0])

        elif command in ["prompt", "p"]:
            if len(args) == 0:
                print(Fore.YELLOW + "Usage: prompt <prompt_content>" + Style.RESET_ALL)
                return
            prompt_text = " ".join(args)
            self.set_system_prompt(prompt_text)

        elif command in ["quit", "q", "exit"]:
            self.running = False
            print(Fore.GREEN + "Goodbye!" + Style.RESET_ALL)

        else:
            print(Fore.RED + f"Unknown command: {command}" + Style.RESET_ALL)
            print("Type 'help' to see available commands")

    async def run(self):
        """运行CLI应用"""
        self.display_banner()

        # 设置默认模型
        await self.set_model(self.current_model_name)

        # 创建第一个对话
        self.create_new_conversation()

        print(Fore.GREEN + "\nApplication started! Type 'help' to see available commands." + Style.RESET_ALL)

        while self.running:
            try:
                # 获取用户输入
                user_input = input(Fore.WHITE + "\n> " + Style.RESET_ALL).strip()

                if not user_input:
                    continue

                # 检查是否是命令
                if user_input.startswith(('/', '\\', ':')):
                    # 解析命令和参数
                    parts = user_input[1:].split()
                    command = parts[0] if parts else ""
                    args = parts[1:] if len(parts) > 1 else []

                    await self.process_command(command, args)
                else:
                    # 作为消息发送
                    await self.send_message(user_input)

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Program interrupted by user" + Style.RESET_ALL)
                self.running = False
            except EOFError:
                print(f"\n{Fore.YELLOW}Input ended" + Style.RESET_ALL)
                self.running = False
            except Exception as e:
                print(f"\n{Fore.RED}Error occurred: {str(e)}" + Style.RESET_ALL)
                logger.error(f"CLI error: {str(e)}")

        logger.info("CLI App shutdown")


@click.command()
@click.option('--model', '-m', default=None, help='指定初始模型')
@click.option('--prompt', '-p', default=None, help='指定系统提示')
@click.option('--web', '-w', is_flag=True, help='启动Web界面')
def main(model, prompt, web):
    """AI聊天助手主程序"""

    if web:
        # 启动Web界面
        from web.app import create_app

        app = create_app()
        print(Fore.GREEN + "Starting Web interface..." + Style.RESET_ALL)
        app.run()
    else:
        # 启动命令行界面
        import asyncio

        cli_app = CLIApp()

        # 设置初始模型
        if model:
            asyncio.run(cli_app.set_model(model))

        # 设置初始系统提示
        if prompt:
            cli_app.create_new_conversation(prompt)

        # 运行CLI应用
        asyncio.run(cli_app.run())


if __name__ == '__main__':
    main()