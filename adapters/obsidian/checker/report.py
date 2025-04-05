#!/usr/bin/env python
"""
Obsidian语法检查报告生成模块
"""

from typing import Dict


def generate_report(issues: Dict[str, Dict], verbose: bool = False) -> int:
    """生成并打印问题报告

    Args:
        issues: 所有文件的问题字典
        verbose: 是否显示详细信息

    Returns:
        错误总数
    """
    error_count = 0
    warning_count = 0
    info_count = 0

    # 收集所有问题的计数
    for file_path, file_issues in issues.items():
        error_count += len(file_issues.get("errors", []))
        warning_count += len(file_issues.get("warnings", []))
        info_count += len(file_issues.get("info", []))

    # 打印摘要
    print("\n===== Obsidian语法检查报告 =====")
    print(f"检查了 {len(issues)} 个有问题的文件")
    print(f"发现 {error_count} 个错误，{warning_count} 个警告，{info_count} 个提示")

    # 如果没有问题或不需要详细报告，就到此为止
    if error_count + warning_count + info_count == 0 or not verbose:
        return error_count

    # 打印每个文件的详细问题
    print("\n----- 详细问题列表 -----")
    for file_path, file_issues in sorted(issues.items()):
        has_issues = (
            len(file_issues.get("errors", [])) > 0
            or len(file_issues.get("warnings", [])) > 0
            or len(file_issues.get("info", [])) > 0
        )

        if has_issues:
            print(f"\n文件: {file_path}")

            # 打印错误
            for issue in file_issues.get("errors", []):
                print(f"  错误 [{issue['line']}:{issue['column']}]: {issue['message']}")
                if verbose and "text" in issue:
                    print(f"    > {issue['text']}")

            # 打印警告
            for issue in file_issues.get("warnings", []):
                print(f"  警告 [{issue['line']}:{issue['column']}]: {issue['message']}")
                if verbose and "text" in issue:
                    print(f"    > {issue['text']}")

            # 打印信息
            if verbose:
                for issue in file_issues.get("info", []):
                    print(f"  信息 [{issue['line']}:{issue['column']}]: {issue['message']}")
                    if "text" in issue:
                        print(f"    > {issue['text']}")

    return error_count
