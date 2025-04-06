"""
适配器模块
提供各种外部服务的适配器
"""

# 导入主要的适配器模块
# from adapters.basic_memory import MemoryManager  # 暂时注释，等实现完成再启用
from adapters.content_parser import ContentParser

# 暴露的接口
__all__ = [
    # "MemoryManager",  # 知识库管理器 (暂时注释，等实现完成再启用)
    "ContentParser",  # 内容解析器
]
