"""
HTML报告生成器

用于生成HTML格式的文档问题报告
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def generate_html_report(issues: Dict, output_file: str) -> None:
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

    logger.info(f"HTML报告已生成: {output_file}")
    print(f"HTML报告已生成: {output_file}")
