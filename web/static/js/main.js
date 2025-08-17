// Web界面JavaScript主文件

class ChatApp {
    constructor() {
        this.currentConversationId = null;
        this.currentModel = null;
        this.conversations = [];
        this.isTyping = false;

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadModels();
        this.loadConversations();

        // 自动创建新对话
        this.createNewConversation();
    }

    bindEvents() {
        // 模型选择
        document.getElementById('modelSelect').addEventListener('change', (e) => {
            this.setModel(e.target.value);
        });

        // 新建对话按钮
        document.getElementById('newConversationBtn').addEventListener('click', () => {
            this.createNewConversation();
        });

        // 发送消息按钮
        document.getElementById('sendBtn').addEventListener('click', () => {
            this.sendMessage();
        });

        // 输入框回车发送
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 系统提示更新
        document.getElementById('updateSystemPromptBtn').addEventListener('click', () => {
            this.updateSystemPrompt();
        });

        // 清空对话
        document.getElementById('clearBtn').addEventListener('click', () => {
            this.clearConversation();
        });

        // 导出对话
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportConversation();
        });

        // 温度滑块
        document.getElementById('temperatureSlider').addEventListener('input', (e) => {
            document.getElementById('temperatureValue').textContent = e.target.value;
        });
    }

    async loadModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();

            if (data.success) {
                this.populateModelSelect(data.models, data.current_model);
            } else {
                this.showError('加载模型列表失败: ' + data.error);
            }
        } catch (error) {
            this.showError('网络错误: ' + error.message);
        }
    }

    populateModelSelect(models, currentModel) {
        const select = document.getElementById('modelSelect');
        select.innerHTML = '';

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            if (model === currentModel) {
                option.selected = true;
                this.setModel(model);
            }
            select.appendChild(option);
        });
    }

    async setModel(modelName) {
        if (!modelName) return;

        try {
            const response = await fetch(`/api/models/${modelName}`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                this.currentModel = modelName;
                this.updateModelStatus(data.available);
            } else {
                this.showError('设置模型失败: ' + data.error);
            }
        } catch (error) {
            this.showError('网络错误: ' + error.message);
        }
    }

    updateModelStatus(available) {
        const statusElement = document.getElementById('modelStatus');
        const badge = statusElement.querySelector('.badge');

        badge.className = 'badge';
        if (available) {
            badge.classList.add('bg-success');
            badge.textContent = '可用';
        } else {
            badge.classList.add('bg-danger');
            badge.textContent = '不可用';
        }
    }

    async loadConversations() {
        try {
            const response = await fetch('/api/conversations');
            const data = await response.json();

            if (data.success) {
                this.conversations = data.conversations;
                this.updateConversationList();
            } else {
                this.showError('加载对话列表失败: ' + data.error);
            }
        } catch (error) {
            this.showError('网络错误: ' + error.message);
        }
    }

    updateConversationList() {
        const listElement = document.getElementById('conversationList');

        if (this.conversations.length === 0) {
            listElement.innerHTML = `
                <div class="text-muted text-center">
                    <small>暂无对话</small>
                </div>
            `;
            return;
        }

        listElement.innerHTML = '';
        this.conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'conversation-item';
            if (conv.id === this.currentConversationId) {
                item.classList.add('active');
            }

            item.innerHTML = `
                <h6>${conv.title}</h6>
                <p>${conv.message_count} 条消息</p>
                <div class="timestamp">${this.formatTimestamp(conv.updated_at)}</div>
            `;

            item.addEventListener('click', () => {
                this.loadConversation(conv.id);
            });

            listElement.appendChild(item);
        });
    }

    async createNewConversation() {
        try {
            const response = await fetch('/api/conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    system_prompt: document.getElementById('systemPrompt').value
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentConversationId = data.conversation_id;
                document.getElementById('currentConversationTitle').textContent = '新对话';
                this.clearMessageContainer();
                this.loadConversations();
            } else {
                this.showError('创建对话失败: ' + data.error);
            }
        } catch (error) {
            this.showError('网络错误: ' + error.message);
        }
    }

    async loadConversation(conversationId) {
        try {
            const response = await fetch(`/api/conversations/${conversationId}`);
            const data = await response.json();

            if (data.success) {
                this.currentConversationId = conversationId;
                const conversation = data.conversation;

                document.getElementById('currentConversationTitle').textContent = conversation.title;
                document.getElementById('systemPrompt').value = conversation.system_prompt || '';

                this.displayMessages(conversation.messages);
                this.updateConversationList();
            } else {
                this.showError('加载对话失败: ' + data.error);
            }
        } catch (error) {
            this.showError('网络错误: ' + error.message);
        }
    }

    displayMessages(messages) {
        const container = document.getElementById('messageContainer');
        container.innerHTML = '';

        messages.forEach(msg => {
            this.addMessageToUI(msg.role, msg.content, msg.timestamp);
        });

        this.scrollToBottom();
    }

    addMessageToUI(role, content, timestamp = null) {
        const container = document.getElementById('messageContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const timeStr = timestamp ? this.formatTimestamp(timestamp) : this.getCurrentTimestamp();

        messageDiv.innerHTML = `
            <div class="message-bubble">${this.escapeHtml(content)}</div>
            <div class="message-timestamp">${timeStr}</div>
        `;

        container.appendChild(messageDiv);
        this.scrollToBottom();
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();

        if (!message) return;
        if (!this.currentModel) {
            this.showError('请先选择一个模型');
            return;
        }

        if (this.isTyping) return;

        // 清空输入框
        input.value = '';

        // 添加用户消息到UI
        this.addMessageToUI('user', message);

        // 显示正在输入指示器
        this.showTypingIndicator();
        this.isTyping = true;

        const streaming = document.getElementById('streamingCheckbox').checked;
        const temperature = parseFloat(document.getElementById('temperatureSlider').value);

        try {
            if (streaming) {
                await this.sendStreamMessage(message, temperature);
            } else {
                await this.sendNormalMessage(message, temperature);
            }
        } catch (error) {
            this.showError('发送消息失败: ' + error.message);
        } finally {
            this.hideTypingIndicator();
            this.isTyping = false;
        }
    }

    async sendNormalMessage(message, temperature) {
        const response = await fetch(`/api/conversations/${this.currentConversationId}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                stream: false,
                temperature: temperature,
                max_tokens: 2000
            })
        });

        const data = await response.json();

        if (data.success) {
            this.addMessageToUI('assistant', data.response);
            this.loadConversations();
        } else {
            this.showError(data.error);
        }
    }

    async sendStreamMessage(message, temperature) {
        const response = await fetch(`/api/conversations/${this.currentConversationId}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                stream: true,
                temperature: temperature,
                max_tokens: 2000
            })
        });

        if (!response.ok) {
            throw new Error('Stream request failed');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';

        // 创建消息容器
        const container = document.getElementById('messageContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-bubble" id="streamingMessage"></div>
            <div class="message-timestamp">${this.getCurrentTimestamp()}</div>
        `;
        container.appendChild(messageDiv);

        const messageElement = document.getElementById('streamingMessage');

        try {
            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.success === false) {
                                this.showError(data.error);
                                return;
                            }

                            if (data.content) {
                                assistantMessage += data.content;
                                messageElement.textContent = assistantMessage;
                                this.scrollToBottom();
                            }

                            if (data.done) {
                                this.loadConversations();
                                return;
                            }
                        } catch (e) {
                            // 忽略JSON解析错误
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Stream reading error:', error);
            this.showError('流式输出错误: ' + error.message);
        }
    }

    showTypingIndicator() {
        const container = document.getElementById('messageContainer');
        const indicator = document.createElement('div');
        indicator.className = 'message assistant';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        container.appendChild(indicator);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    async updateSystemPrompt() {
        if (!this.currentConversationId) {
            this.showError('请先创建或选择一个对话');
            return;
        }

        const systemPrompt = document.getElementById('systemPrompt').value;

        try {
            const response = await fetch(`/api/conversations/${this.currentConversationId}/system-prompt`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    system_prompt: systemPrompt
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('系统提示已更新');
            } else {
                this.showError('更新系统提示失败: ' + data.error);
            }
        } catch (error) {
            this.showError('网络错误: ' + error.message);
        }
    }

    async clearConversation() {
        if (!this.currentConversationId) {
            this.showError('没有可清空的对话');
            return;
        }

        if (!confirm('确定要清空当前对话的所有消息吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/conversations/${this.currentConversationId}/clear`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.clearMessageContainer();
                this.showSuccess('对话已清空');
            } else {
                this.showError('清空对话失败: ' + data.error);
            }
        } catch (error) {
            this.showError('网络错误: ' + error.message);
        }
    }

    async exportConversation() {
        if (!this.currentConversationId) {
            this.showError('没有可导出的对话');
            return;
        }

        try {
            const response = await fetch(`/api/conversations/${this.currentConversationId}/export?format=json`);
            const data = await response.json();

            if (data.success) {
                const blob = new Blob([data.content], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `conversation_${this.currentConversationId}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                this.showSuccess('对话已导出');
            } else {
                this.showError('导出对话失败: ' + data.error);
            }
        } catch (error) {
            this.showError('网络错误: ' + error.message);
        }
    }

    clearMessageContainer() {
        document.getElementById('messageContainer').innerHTML = `
            <div class="welcome-message">
                <h3><i class="fas fa-robot"></i> 欢迎使用 AI 聊天助手</h3>
                <p>请选择一个模型开始对话，或创建新的对话。</p>
            </div>
        `;
    }

    scrollToBottom() {
        const container = document.getElementById('messageContainer');
        container.scrollTop = container.scrollHeight;
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('zh-CN');
    }

    getCurrentTimestamp() {
        return this.formatTimestamp(new Date().toISOString());
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        const container = document.getElementById('messageContainer');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        container.appendChild(errorDiv);
        this.scrollToBottom();

        // 5秒后自动移除错误消息
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    showSuccess(message) {
        // 创建一个临时的成功提示
        const toast = document.createElement('div');
        toast.className = 'position-fixed top-0 end-0 p-3';
        toast.style.zIndex = '11';
        toast.innerHTML = `
            <div class="toast show" role="alert">
                <div class="toast-header">
                    <strong class="me-auto">成功</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        document.body.appendChild(toast);

        // 3秒后自动移除
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});