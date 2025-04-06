#!/usr/bin/env python
"""
文档问题报告生成器

用于生成文档问题的详细报告，支持导出为不同格式。
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到模块搜索路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from adapters.obsidian.checker.checker import ObsidianSyntaxChecker
    from src.docs_engine.api.document_engine import DocumentEngine
    from src.docs_engine.utils.report_generators import (
        generate_html_report,
        generate_json_report,
        generate_text_report,
    )
except ImportError as e:
    print(f"错误: 无法导入模块 - {e}")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="文档问题报告生成器")
    parser.add_argument("--docs-dir", help="文档目录路径", default=os.path.join(project_root, "docs"))
    parser.add_argument("--format", choices=["html", "json", "text"], default="html", help="报告格式")
    parser.add_argument("--output", help="输出文件路径", default="docs_report")
    parser.add_argument("--include-info", action="store_true", help="包含信息级别的提示")

    args = parser.parse_args()

    # 检查文档目录
    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists() or not docs_dir.is_dir():
        logger.error(f"错误: 无效的文档目录 - {docs_dir}")
        return 1

    # 创建检查器
    checker = ObsidianSyntaxChecker(str(docs_dir))

    # 检查文档
    logger.info(f"检查文档目录: {docs_dir}")
    issues = checker.check_directory(docs_dir)

    if not issues:
        logger.info("没有发现问题，所有文档都符合规范!")
        return 0

    # 根据格式生成报告
    if args.format == "html":
        output_file = f"{args.output}.html" if not args.output.endswith(".html") else args.output
        generate_html_report(issues, output_file)
    elif args.format == "json":
        output_file = f"{args.output}.json" if not args.output.endswith(".json") else args.output
        generate_json_report(issues, output_file)
    else:  # text
        output_file = f"{args.output}.txt" if not args.output.endswith(".txt") else args.output
        generate_text_report(issues, output_file, args.include_info)

    return 0


if __name__ == "__main__":
    sys.exit(main())
