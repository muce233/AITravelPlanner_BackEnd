"""日志工具模块 - 用于记录对话日志"""
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


class ConversationLogger:
    """对话日志记录器 - 每个对话一个文件"""
    
    def __init__(self, log_dir: str = "logs", enabled: bool = True):
        """
        初始化对话日志记录器
        
        Args:
            log_dir: 日志文件夹路径
            enabled: 是否启用日志记录
        """
        self.log_dir = Path(log_dir)
        self.enabled = enabled
        
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def is_enabled(self) -> bool:
        """检查日志是否启用"""
        return self.enabled
    
    def _get_log_file_path(self, conversation_id: str) -> Path:
        """
        获取对话日志文件路径
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            日志文件路径
        """
        return self.log_dir / f"{conversation_id}.txt"
    
    def log(self, conversation_id: str, content: str):
        """
        记录日志内容
        
        Args:
            conversation_id: 对话ID
            content: 日志内容
        """
        if not self.enabled:
            return
        
        try:
            log_file_path = self._get_log_file_path(conversation_id)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {content}\n")
                
        except Exception as e:
            print(f"写入对话日志失败: {str(e)}")


# 创建全局日志记录器实例
_global_logger: Optional[ConversationLogger] = None


def get_logger(log_dir: str = "logs", enabled: bool = True) -> ConversationLogger:
    """
    获取全局日志记录器实例
    
    Args:
        log_dir: 日志文件夹路径
        enabled: 是否启用日志记录
        
    Returns:
        ConversationLogger实例
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = ConversationLogger(log_dir=log_dir, enabled=enabled)
    
    return _global_logger


def init_logger(log_dir: str = "logs", enabled: bool = True):
    """
    初始化全局日志记录器
    
    Args:
        log_dir: 日志文件夹路径
        enabled: 是否启用日志记录
    """
    global _global_logger
    _global_logger = ConversationLogger(log_dir=log_dir, enabled=enabled)
