"""
Ollama内容解析器 (兼容层)

此文件为兼容层，提供与原始 OllamaParser 类相同的接口，
但将实际解析工作委托给重构后的模块。
新代码应直接使用 adapters.content_parser.ollama 包。
"""

from adapters.content_parser.ollama import OllamaParser

# 重新导出所有类以保持向后兼容性
__all__ = ["OllamaParser"]
