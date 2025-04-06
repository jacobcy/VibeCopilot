"""
文本报告生成器

用于生成文本格式的文档问题报告
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def generate_text_report(issues: Dict, output_file: str, include_info: bool = False) -> None:
    """生成文本格式的问题报告

    Args:
        issues: 问题字典
        output_file: 输出文件路径
        include_info: 是否包含信息级别的提示
    """
    with open(output_file, "w", encoding="utf-8") as f:
        # 写入总结
        total_files = len(issues)
        total_errors = sum(len(file_issues["errors"]) for file_issues in issues.values())
        total_warnings = sum(len(file_issues["warnings"]) for file_issues in issues.values())
        total_infos = sum(len(file_issues["info"]) for file_issues in issues.values())

        f.write(f"文档问题报告\n")
        f.write(f"=============\n\n")
        f.write(f"总结: 检查了 {total_files} 个文件\n")
        f.write(f"- {total_errors} 个错误\n")
        f.write(f"- {total_warnings} 个警告\n")
        f.write(f"- {total_infos} 个提示\n\n")

        f.write(f"详细问题列表\n")
        f.write(f"-------------\n\n")

        # 按文件写入详细问题
        for file_path, file_issues in issues.items():
            if (
                not file_issues["errors"]
                and not file_issues["warnings"]
                and (not include_info or not file_issues["info"])
            ):
                continue

            f.write(f"\n文件: {file_path}\n")
            f.write("=" * len(f"文件: {file_path}") + "\n")

            # 写入错误
            if file_issues["errors"]:
                f.write("\n错误:\n")
                for issue in file_issues["errors"]:
                    f.write(f"- 第{issue['line']}行: {issue['message']}\n")
                    if issue["text"]:
                        f.write(f"  {issue['text']}\n")

            # 写入警告
            if file_issues["warnings"]:
                f.write("\n警告:\n")
                for issue in file_issues["warnings"]:
                    f.write(f"- 第{issue['line']}行: {issue['message']}\n")
                    if issue["text"]:
                        f.write(f"  {issue['text']}\n")

            # 写入信息
            if include_info and file_issues["info"]:
                f.write("\n提示:\n")
                for issue in file_issues["info"]:
                    f.write(f"- 第{issue['line']}行: {issue['message']}\n")
                    if issue["text"]:
                        f.write(f"  {issue['text']}\n")

    logger.info(f"文本报告已生成: {output_file}")
    print(f"文本报告已生成: {output_file}")
