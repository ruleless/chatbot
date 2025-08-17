"""
日志工具模块 - 提供统一的日志记录功能
"""

import logging
import sys
from datetime import datetime
from typing import Optional


class Logger:
    """日志管理器类"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """设置日志配置"""
        self._logger = logging.getLogger('chatbot')
        self._logger.setLevel(logging.INFO)

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 创建文件处理器
        file_handler = logging.FileHandler(
            f'chatbot_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 添加处理器
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)

    def info(self, message: str, **kwargs):
        """记录信息级别日志"""
        self._logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """记录调试级别日志"""
        self._logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录警告级别日志"""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录错误级别日志"""
        self._logger.error(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """记录异常日志"""
        self._logger.exception(message, **kwargs)


# 全局日志实例
logger = Logger()