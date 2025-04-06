"""
报告生成器模块

提供多种格式的文档问题报告生成功能
"""

from src.docs_engine.utils.report_generators.html_generator import generate_html_report
from src.docs_engine.utils.report_generators.json_generator import generate_json_report
from src.docs_engine.utils.report_generators.text_generator import generate_text_report

__all__ = ["generate_html_report", "generate_json_report", "generate_text_report"]
