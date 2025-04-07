"""
Specific parser implementations for different backends.
"""

from src.core.parsing.parsers.ollama_parser import OllamaParser
from src.core.parsing.parsers.openai_parser import OpenAIParser
from src.core.parsing.parsers.regex_parser import RegexParser

__all__ = ["OpenAIParser", "OllamaParser", "RegexParser"]
