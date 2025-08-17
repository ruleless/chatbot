# AI 聊天助手

一个功能完整的Python聊天机器人程序，支持本地Ollama模型和线上模型（如DeepSeek、Gemini等），提供Web界面和命令行交互。

## 🌟 主要功能

- **多模型支持**: 支持本地Ollama模型和线上模型（DeepSeek、Gemini、OpenAI等）
- **双重界面**: 提供现代化的Web界面和功能完整的命令行界面
- **多轮对话**: 维护对话上下文，支持连续交互
- **系统提示配置**: 允许自定义系统提示，设定AI助手角色
- **模型切换**: 支持动态选择不同的模型
- **流式输出**: 利用模型API的流模式，实现实时逐字显示
- **对话管理**: 支持创建、删除、清空、导出对话
- **错误处理**: 完善的错误处理和用户友好的提示信息

## 📁 项目结构

```
chatbot/
├── main.py                 # 主程序入口
├── cli.py                  # 命令行界面
├── config.py               # 配置文件
├── requirements.txt        # 项目依赖
├── README.md              # 项目说明
├── models/                # 模型交互层
│   ├── __init__.py
│   ├── base_model.py      # 基础模型接口
│   ├── ollama_model.py    # Ollama模型实现
│   └── online_model.py    # 线上模型实现
├── chat/                  # 对话管理
│   ├── __init__.py
│   └── conversation_manager.py  # 对话管理器
├── web/                   # Web界面
│   ├── __init__.py
│   ├── app.py            # Flask应用
│   ├── templates/
│   │   └── index.html    # 主页面
│   └── static/
│       ├── css/
│       │   └── style.css # 样式文件
│       └── js/
│           └── main.js   # JavaScript文件
└── utils/                 # 工具函数
    ├── __init__.py
    ├── logger.py         # 日志工具
    └── helpers.py        # 辅助函数
```

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装：
- Python 3.8+
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动本地Ollama服务（可选）

如果要使用本地Ollama模型，需要先启动Ollama服务：

```bash
# 安装Ollama（如果尚未安装）
# 访问 https://ollama.com 下载安装

# 拉取模型
ollama pull llama2

# 启动Ollama服务
ollama serve
```

### 4. 配置线上模型API密钥（可选）

如果要使用线上模型，需要设置相应的环境变量：

```bash
# Windows
set DEEPSEEK_API_KEY=your_deepseek_api_key
set GEMINI_API_KEY=your_gemini_api_key
set OPENAI_API_KEY=your_openai_api_key

# Linux/Mac
export DEEPSEEK_API_KEY=your_deepseek_api_key
export GEMINI_API_KEY=your_gemini_api_key
export OPENAI_API_KEY=your_openai_api_key
```

### 5. 运行程序

#### Web界面模式

```bash
# 启动Web界面
python main.py --web

# 或者使用cli.py
python cli.py --web
```

然后打开浏览器访问 `http://localhost:5000`

#### 命令行模式

```bash
# 启动命令行界面
python main.py

# 或者使用cli.py
python cli.py

# 指定初始模型
python main.py --model llama2

# 指定系统提示
python main.py --prompt "你是一个专业的Python开发助手"
```

## 📖 使用说明

### Web界面使用

1. **选择模型**: 在左侧边栏的"模型选择"下拉菜单中选择要使用的模型
2. **创建对话**: 点击"新建"按钮创建新的对话
3. **设置系统提示**: 在"系统提示"文本框中输入AI助手的角色设定
4. **开始对话**: 在底部输入框中输入问题，点击发送按钮或按Enter键
5. **管理对话**: 可以清空当前对话或导出对话记录

### 命令行使用

启动命令行界面后，可以使用以下命令：

```
help, h     - 显示帮助信息
models, m   - 列出所有可用模型
set, s      - 设置当前模型 (用法: set llama2)
new, n      - 创建新对话
clear, c    - 清空当前对话
history, hi - 显示对话历史
export, e   - 导出当前对话 (用法: export conversation.txt)
prompt, p   - 设置系统提示 (用法: prompt 你是一个Python专家)
quit, q     - 退出程序
```

直接输入文本即可与AI对话，命令以 `/`、`\` 或 `:` 开头。

## 🔧 配置说明

### 支持的模型

#### 本地Ollama模型
- llama2
- mistral
- codellama
- vicuna
- wizardlm

#### 线上模型
- **DeepSeek**: 需要DEEPSEEK_API_KEY
- **Gemini**: 需要GEMINI_API_KEY
- **OpenAI**: 需要OPENAI_API_KEY

### 配置文件

在 `config.py` 中可以修改以下配置：

```python
# 基础配置
HOST = "127.0.0.1"      # Web服务地址
PORT = 5000             # Web服务端口
DEBUG = True            # 调试模式

# 对话配置
MAX_HISTORY_LENGTH = 50 # 最大对话历史长度
DEFAULT_SYSTEM_PROMPT = "你是一个专业的AI助手"  # 默认系统提示
DEFAULT_TEMPERATURE = 0.7    # 默认温度参数
DEFAULT_MAX_TOKENS = 2000    # 默认最大令牌数

# Ollama配置
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama服务地址
```

## 🛠️ 开发说明

### 添加新模型

#### 1. 添加Ollama模型

在 `config.py` 中的 `OLLAMA_MODELS` 列表中添加新的模型名称：

```python
OLLAMA_MODELS = [
    "llama2",
    "mistral",
    "codellama",
    "vicuna",
    "wizardlm",
    "your_new_model"  # 添加新模型
]
```

#### 2. 添加线上模型

在 `config.py` 中的 `ONLINE_MODELS` 字典中添加新的模型配置：

```python
ONLINE_MODELS = {
    "deepseek": {...},
    "gemini": {...},
    "openai": {...},
    "new_provider": {  # 添加新提供商
        "api_key": os.getenv("NEW_PROVIDER_API_KEY", ""),
        "base_url": "https://api.newprovider.com/v1",
        "model": "new-model-name"
    }
}
```

#### 3. 实现新的模型接口

如果需要支持新的API格式，可以在 `models/online_model.py` 中添加相应的实现方法。

### 日志系统

程序使用Python的logging模块记录日志，日志文件会按日期生成在项目根目录：
- `chatbot_YYYYMMDD.log`

日志级别分为：
- DEBUG: 调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息

## 🐛 常见问题

### 1. Ollama连接失败

**问题**: 提示"Ollama service or model is not available"

**解决方案**:
- 确保Ollama服务已启动: `ollama serve`
- 检查Ollama服务地址是否正确
- 确保已下载相应的模型: `ollama pull llama2`

### 2. 线上模型API密钥无效

**问题**: 提示"模型不可用"或API认证失败

**解决方案**:
- 检查环境变量是否正确设置
- 验证API密钥是否有效
- 确认API密钥权限是否足够

### 3. Web界面无法访问

**问题**: 浏览器无法连接到Web界面

**解决方案**:
- 检查端口5000是否被占用
- 确保防火墙允许本地连接
- 检查程序是否正常启动

### 4. 依赖安装失败

**问题**: pip install 时出现错误

**解决方案**:
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进本项目！

## 📞 联系

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**祝你使用愉快！** 🎉