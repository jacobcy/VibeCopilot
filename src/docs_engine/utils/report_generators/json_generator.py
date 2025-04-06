"""
JSON报告生成器

用于生成JSON格式的文档问题报告
"""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def generate_json_report(issues: Dict, output_file: str) -> None:
    """生成JSON格式的问题报告

    Args:
        issues: 问题字典
        output_file: 输出文件路径
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(issues, f, indent=2, ensure_ascii=False)

    logger.info(f"JSON报告已生成: {output_file}")
    print(f"JSON报告已生成: {output_file}")
