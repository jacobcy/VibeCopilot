#!/usr/bin/env python
"""
文档问题报告生成器

用于生成文档问题的详细报告，支持导出为不同格式。
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到模块搜索路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.docs.utils.obsidian.syntax_checker import ObsidianSyntaxChecker
    from src.docs_engine.docs_engine import create_docs_engine
except ImportError as e:
    print(f"错误: 无法导入模块 - {e}")
    sys.exit(1)


def generate_html_report(issues, output_file):
    """生成HTML格式的问题报告

    Args:
        issues: 问题字典
        output_file: 输出文件路径
    """
    html = """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文档问题报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .summary {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .file {
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
        }
        .file-header {
            background-color: #f1f1f1;
            padding: 10px;
            margin: -15px -15px 15px -15px;
            border-radius: 5px 5px 0 0;
        }
        .issue {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 3px;
        }
        .error {
            background-color: #ffeded;
            border-left: 4px solid #f44336;
        }
        .warning {
            background-color: #fff8e6;
            border-left: 4px solid #ff9800;
        }
        .info {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
        }
        .code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            background-color: #f5f5f5;
            padding: 3px 5px;
            border-radius: 3px;
        }
        .meta {
            font-size: 0.9em;
            color: #666;
        }
        .issue-count {
            display: inline-block;
            min-width: 20px;
            padding: 0 5px;
            border-radius: 10px;
            text-align: center;
            color: white;
            font-size: 0.9em;
            margin-left: 5px;
        }
        .error-count {
            background-color: #f44336;
        }
        .warning-count {
            background-color: #ff9800;
        }
        .info-count {
            background-color: #2196f3;
        }
    </style>
</head>
<body>
    <h1>文档问题报告</h1>
"""

    # 计算总体统计信息
    total_files = len(issues)
    total_errors = sum(len(file_issues["errors"]) for file_issues in issues.values())
    total_warnings = sum(len(file_issues["warnings"]) for file_issues in issues.values())
    total_infos = sum(len(file_issues["info"]) for file_issues in issues.values())

    # 添加总结部分
    html += f"""
    <div class="summary">
        <h2>总结</h2>
        <p>
            检查了 <strong>{total_files}</strong> 个文件，发现:
            <span class="issue-count error-count">{total_errors}</span> 个错误,
            <span class="issue-count warning-count">{total_warnings}</span> 个警告,
            <span class="issue-count info-count">{total_infos}</span> 个提示
        </p>
    </div>
    <h2>详细问题列表</h2>
"""

    # 按文件添加详细问题
    for file_path, file_issues in issues.items():
        error_count = len(file_issues["errors"])
        warning_count = len(file_issues["warnings"])
        info_count = len(file_issues["info"])

        # 跳过没有问题的文件
        if error_count == 0 and warning_count == 0 and info_count == 0:
            continue

        html += f"""
    <div class="file">
        <div class="file-header">
            <h3>{file_path}
                <span class="issue-count error-count">{error_count}</span>
                <span class="issue-count warning-count">{warning_count}</span>
                <span class="issue-count info-count">{info_count}</span>
            </h3>
        </div>
"""

        # 添加错误
        if error_count > 0:
            html += "        <h4>错误</h4>\n"
            for issue in file_issues["errors"]:
                html += f"""
        <div class="issue error">
            <div><strong>{issue["message"]}</strong></div>
            <div class="meta">行 {issue["line"]}, 列 {issue["column"]}</div>
            {f'<div class="code">{issue["text"]}</div>' if issue["text"] else ''}
        </div>
"""

        # 添加警告
        if warning_count > 0:
            html += "        <h4>警告</h4>\n"
            for issue in file_issues["warnings"]:
                html += f"""
        <div class="issue warning">
            <div><strong>{issue["message"]}</strong></div>
            <div class="meta">行 {issue["line"]}, 列 {issue["column"]}</div>
            {f'<div class="code">{issue["text"]}</div>' if issue["text"] else ''}
        </div>
"""

        # 添加信息
        if info_count > 0:
            html += "        <h4>提示</h4>\n"
            for issue in file_issues["info"]:
                html += f"""
        <div class="issue info">
            <div><strong>{issue["message"]}</strong></div>
            <div class="meta">行 {issue["line"]}, 列 {issue["column"]}</div>
            {f'<div class="code">{issue["text"]}</div>' if issue["text"] else ''}
        </div>
"""

        html += "    </div>\n"

    # 关闭HTML
    html += """
</body>
</html>
"""

    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML报告已生成: {output_file}")


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
        print(f"错误: 无效的文档目录 - {docs_dir}")
        return 1

    # 创建检查器
    checker = ObsidianSyntaxChecker(str(docs_dir))

    # 检查文档
    print(f"检查文档目录: {docs_dir}")
    issues = checker.check_directory(docs_dir)

    if not issues:
        print("没有发现问题，所有文档都符合规范!")
        return 0

    # 根据格式生成报告
    if args.format == "html":
        output_file = f"{args.output}.html" if not args.output.endswith(".html") else args.output
        generate_html_report(issues, output_file)
    elif args.format == "json":
        output_file = f"{args.output}.json" if not args.output.endswith(".json") else args.output
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(issues, f, indent=2, ensure_ascii=False)
        print(f"JSON报告已生成: {output_file}")
    else:  # text
        output_file = f"{args.output}.txt" if not args.output.endswith(".txt") else args.output
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
                    and (not args.include_info or not file_issues["info"])
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
                if args.include_info and file_issues["info"]:
                    f.write("\n提示:\n")
                    for issue in file_issues["info"]:
                        f.write(f"- 第{issue['line']}行: {issue['message']}\n")
                        if issue["text"]:
                            f.write(f"  {issue['text']}\n")

        print(f"文本报告已生成: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
