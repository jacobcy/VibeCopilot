#!/usr/bin/env python
"""
Obsidian 语法检查工具

专用于检查 Obsidian 特定的语法问题，如链接格式、嵌入语法等。
提供详细的警告和错误报告，帮助用户修复文档问题。
"""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# 添加项目根目录到模块搜索路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def setup_logging(verbose: bool = False) -> logging.Logger:
    """设置日志记录器

    Args:
        verbose: 是否输出详细日志

    Returns:
        日志记录器
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    return logging.getLogger("obsidian_syntax_checker")


class ObsidianSyntaxChecker:
    """Obsidian语法检查器，检查文档中的语法问题"""

    # Obsidian链接模式: [[文件名]] 或 [[文件名|显示文本]]
    OBSIDIAN_LINK_PATTERN = r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"

    # Obsidian嵌入模式: ![[文件名]]
    OBSIDIAN_EMBED_PATTERN = r"!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"

    # MDX组件未闭合模式
    MDX_UNCLOSED_TABS_PATTERN = r"<Tabs>(?:(?!<\/Tabs>).)*$"

    # 数字开头的JSX标签
    MDX_NUMBER_TAG_PATTERN = r"<(\d+)([:\s])"

    # 不正确的结束标签
    MDX_WRONG_CLOSING_TAG_PATTERN = r"<\/([\w-]+):([\w-]+)>"

    # YAML前置元数据检测
    YAML_FRONTMATTER_PATTERN = r"^---\s*\n(.*?)\n---\s*$"

    def __init__(self, base_dir: str, logger: Optional[logging.Logger] = None):
        """初始化语法检查器

        Args:
            base_dir: 基础目录路径
            logger: 日志记录器
        """
        self.base_dir = Path(base_dir)
        self.logger = logger or logging.getLogger("obsidian_syntax_checker")

        # 编译正则表达式
        self.obsidian_link_regex = re.compile(self.OBSIDIAN_LINK_PATTERN)
        self.obsidian_embed_regex = re.compile(self.OBSIDIAN_EMBED_PATTERN)
        self.mdx_unclosed_tabs_regex = re.compile(self.MDX_UNCLOSED_TABS_PATTERN, re.DOTALL)
        self.mdx_number_tag_regex = re.compile(self.MDX_NUMBER_TAG_PATTERN)
        self.mdx_wrong_closing_tag_regex = re.compile(self.MDX_WRONG_CLOSING_TAG_PATTERN)
        self.yaml_frontmatter_regex = re.compile(self.YAML_FRONTMATTER_PATTERN, re.DOTALL)

    def check_file(self, file_path: Union[str, Path]) -> Dict[str, List[Dict]]:
        """检查单个文件的语法问题

        Args:
            file_path: 文件路径

        Returns:
            语法问题列表，按类型分组
        """
        file_path = Path(file_path)
        issues = {"errors": [], "warnings": [], "info": []}  # 需要修复的严重问题  # 建议修复的问题  # 信息性提示

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查各种语法问题
            self._check_links(content, file_path, issues)
            self._check_embeds(content, file_path, issues)
            self._check_mdx_syntax(content, file_path, issues)
            self._check_frontmatter(content, file_path, issues)

        except Exception as e:
            issues["errors"].append(
                {
                    "type": "file_error",
                    "message": f"无法读取或处理文件: {str(e)}",
                    "line": 0,
                    "column": 0,
                    "text": "",
                }
            )

        return issues

    def check_directory(
        self, directory: Union[str, Path], recursive: bool = True
    ) -> Dict[str, Dict]:
        """检查目录中的所有Markdown文件

        Args:
            directory: 目录路径
            recursive: 是否递归检查子目录

        Returns:
            所有文件的问题列表
        """
        directory = Path(directory)
        all_issues = {}

        # 查找所有Markdown文件
        pattern = "**/*.md" if recursive else "*.md"
        for md_file in directory.glob(pattern):
            file_issues = self.check_file(md_file)

            # 只添加有问题的文件
            if any(file_issues.values()):
                all_issues[str(md_file.relative_to(self.base_dir))] = file_issues

        return all_issues

    def _check_links(self, content: str, file_path: Path, issues: Dict[str, List[Dict]]):
        """检查Obsidian链接语法和引用完整性

        Args:
            content: 文档内容
            file_path: 文件路径
            issues: 问题收集字典
        """
        current_dir = file_path.parent

        # 获取行号映射
        line_map = self._create_line_map(content)

        # 检查每个Obsidian链接
        for match in self.obsidian_link_regex.finditer(content):
            target_file = match.group(1).strip()
            section = match.group(2)

            # 检查目标文件是否存在
            target_path = self._resolve_link_path(target_file, current_dir)
            if not target_path:
                # 查找行号和列号
                start_pos = match.start()
                line_no, col_no = self._get_line_col(start_pos, line_map)

                issues["warnings"].append(
                    {
                        "type": "broken_link",
                        "message": f"链接目标不存在: {target_file}",
                        "line": line_no,
                        "column": col_no,
                        "text": match.group(0),
                    }
                )

            # 如果链接包含段落引用，但目标文件存在
            elif section and target_path:
                # 这里可以添加进一步检查段落引用的完整性
                # 但需要读取目标文件内容，可能会影响性能
                pass

    def _check_embeds(self, content: str, file_path: Path, issues: Dict[str, List[Dict]]):
        """检查Obsidian嵌入语法和引用完整性

        Args:
            content: 文档内容
            file_path: 文件路径
            issues: 问题收集字典
        """
        current_dir = file_path.parent

        # 获取行号映射
        line_map = self._create_line_map(content)

        # 检查每个Obsidian嵌入
        for match in self.obsidian_embed_regex.finditer(content):
            target_file = match.group(1).strip()

            # 检查目标文件是否存在
            target_path = self._resolve_link_path(target_file, current_dir)
            if not target_path:
                # 查找行号和列号
                start_pos = match.start()
                line_no, col_no = self._get_line_col(start_pos, line_map)

                issues["warnings"].append(
                    {
                        "type": "broken_embed",
                        "message": f"嵌入目标不存在: {target_file}",
                        "line": line_no,
                        "column": col_no,
                        "text": match.group(0),
                    }
                )

    def _check_mdx_syntax(self, content: str, file_path: Path, issues: Dict[str, List[Dict]]):
        """检查MDX语法问题

        Args:
            content: 文档内容
            file_path: 文件路径
            issues: 问题收集字典
        """
        # 获取行号映射
        line_map = self._create_line_map(content)

        # 检查未闭合的Tabs组件
        for match in self.mdx_unclosed_tabs_regex.finditer(content):
            start_pos = match.start()
            line_no, col_no = self._get_line_col(start_pos, line_map)

            issues["errors"].append(
                {
                    "type": "unclosed_tabs",
                    "message": "Tabs组件未闭合，缺少</Tabs>标签",
                    "line": line_no,
                    "column": col_no,
                    "text": "<Tabs>...",
                }
            )

        # 检查数字开头的JSX标签
        for match in self.mdx_number_tag_regex.finditer(content):
            start_pos = match.start()
            line_no, col_no = self._get_line_col(start_pos, line_map)

            issues["errors"].append(
                {
                    "type": "number_tag",
                    "message": f"数字开头的JSX标签: <{match.group(1)}{match.group(2)}",
                    "line": line_no,
                    "column": col_no,
                    "text": match.group(0),
                }
            )

        # 检查不正确的结束标签
        for match in self.mdx_wrong_closing_tag_regex.finditer(content):
            start_pos = match.start()
            line_no, col_no = self._get_line_col(start_pos, line_map)

            issues["errors"].append(
                {
                    "type": "wrong_closing_tag",
                    "message": f"不正确的结束标签: {match.group(0)}，应为</{match.group(1)}{match.group(2)}>",
                    "line": line_no,
                    "column": col_no,
                    "text": match.group(0),
                }
            )

    def _check_frontmatter(self, content: str, file_path: Path, issues: Dict[str, List[Dict]]):
        """检查YAML前置元数据

        Args:
            content: 文档内容
            file_path: 文件路径
            issues: 问题收集字典
        """
        # 检查是否有YAML前置元数据
        frontmatter_match = self.yaml_frontmatter_regex.search(content)
        if not frontmatter_match:
            issues["warnings"].append(
                {
                    "type": "missing_frontmatter",
                    "message": "文档缺少YAML前置元数据",
                    "line": 1,
                    "column": 1,
                    "text": "",
                }
            )
            return

        # 检查必要的元数据字段
        frontmatter = frontmatter_match.group(1)

        # 简单检查是否有title
        if "title:" not in frontmatter:
            issues["warnings"].append(
                {
                    "type": "missing_title",
                    "message": "YAML前置元数据缺少title字段",
                    "line": 2,
                    "column": 1,
                    "text": "---",
                }
            )

        # 简单检查是否有category
        if "category:" not in frontmatter:
            issues["info"].append(
                {
                    "type": "missing_category",
                    "message": "YAML前置元数据缺少category字段",
                    "line": 2,
                    "column": 1,
                    "text": "---",
                }
            )

    def _resolve_link_path(self, link_target: str, current_dir: Path) -> Optional[Path]:
        """解析Obsidian链接目标的实际路径

        Args:
            link_target: Obsidian链接目标
            current_dir: 当前文件所在目录

        Returns:
            解析后的目标路径，如果无法解析则返回None
        """
        # 如果有扩展名，直接在当前目录查找
        if "." in link_target:
            # 尝试相对于当前目录解析
            target_path = current_dir / link_target
            if target_path.exists():
                return target_path

        # 如果没有扩展名，尝试添加.md扩展名
        target_with_md = f"{link_target}.md"
        target_path = current_dir / target_with_md

        if target_path.exists():
            return target_path

        # 如果在当前目录找不到，尝试在整个文档库中查找
        for ext in [".md", ".mdx", ".markdown"]:
            for file_path in self.base_dir.glob(f"**/*{ext}"):
                if file_path.stem == link_target:
                    return file_path

        # 查找带空格的文件名
        for ext in [".md", ".mdx", ".markdown"]:
            for file_path in self.base_dir.glob(f"**/*{ext}"):
                if file_path.stem.replace(" ", "_") == link_target:
                    return file_path

        return None

    def _create_line_map(self, content: str) -> List[int]:
        """创建从字符位置到行号的映射

        Args:
            content: 文档内容

        Returns:
            行起始位置列表
        """
        line_map = [0]  # 第一行从位置0开始
        for i, char in enumerate(content):
            if char == "\n":
                line_map.append(i + 1)  # 下一行从位置i+1开始
        return line_map

    def _get_line_col(self, pos: int, line_map: List[int]) -> Tuple[int, int]:
        """根据字符位置获取行号和列号

        Args:
            pos: 字符位置
            line_map: 行映射

        Returns:
            (行号, 列号)元组，从1开始
        """
        # 找到最后一个小于等于pos的行首位置
        line = 0
        for i, start in enumerate(line_map):
            if start <= pos:
                line = i
            else:
                break

        # 计算列号（字符位置 - 行首位置 + 1）
        col = pos - line_map[line] + 1

        # 返回行号和列号（从1开始）
        return line + 1, col


def generate_report(issues: Dict[str, Dict], verbose: bool = False) -> int:
    """生成语法检查报告

    Args:
        issues: 检查问题
        verbose: 是否生成详细报告

    Returns:
        错误数量
    """
    error_count = 0
    warning_count = 0
    info_count = 0

    # 统计问题数量
    for file_path, file_issues in issues.items():
        error_count += len(file_issues["errors"])
        warning_count += len(file_issues["warnings"])
        info_count += len(file_issues["info"])

    # 打印总结
    print(f"\n语法检查报告:")
    print(f"- 发现 {len(issues)} 个文件存在问题")
    print(f"- {error_count} 个错误 (需要修复)")
    print(f"- {warning_count} 个警告 (建议修复)")
    print(f"- {info_count} 个提示")

    # 打印详细报告
    if verbose or error_count > 0:
        print("\n详细问题列表:")
        for file_path, file_issues in issues.items():
            if (
                file_issues["errors"]
                or file_issues["warnings"]
                or (verbose and file_issues["info"])
            ):
                print(f"\n文件: {file_path}")

                # 打印错误
                for issue in file_issues["errors"]:
                    print(f"  错误 (第{issue['line']}行): {issue['message']}")
                    if issue["text"]:
                        print(f"    {issue['text']}")

                # 打印警告
                for issue in file_issues["warnings"]:
                    print(f"  警告 (第{issue['line']}行): {issue['message']}")
                    if issue["text"] and verbose:
                        print(f"    {issue['text']}")

                # 打印信息
                if verbose:
                    for issue in file_issues["info"]:
                        print(f"  提示 (第{issue['line']}行): {issue['message']}")

    return error_count


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Obsidian 文档语法检查工具")
    parser.add_argument("path", help="要检查的文件或目录路径")
    parser.add_argument("--base-dir", help="文档基础目录，默认为当前目录", default=os.getcwd())
    parser.add_argument("--recursive", "-r", action="store_true", help="递归检查子目录")
    parser.add_argument("--verbose", "-v", action="store_true", help="输出详细日志")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出结果")
    parser.add_argument("--errors-only", action="store_true", help="只报告错误，忽略警告和提示")

    args = parser.parse_args()

    # 设置日志
    logger = setup_logging(args.verbose)

    # 创建检查器
    checker = ObsidianSyntaxChecker(args.base_dir, logger)

    # 检查路径
    path = Path(args.path)
    if path.is_file():
        logger.info(f"检查文件: {path}")
        issues = {str(path.relative_to(args.base_dir)): checker.check_file(path)}
    elif path.is_dir():
        logger.info(f"检查目录: {path}")
        issues = checker.check_directory(path, args.recursive)
    else:
        logger.error(f"无效的路径: {path}")
        return 1

    # 处理结果
    if args.json:
        import json

        print(json.dumps(issues, indent=2, ensure_ascii=False))
    else:
        # 过滤结果
        if args.errors_only:
            filtered_issues = {}
            for file_path, file_issues in issues.items():
                if file_issues["errors"]:
                    filtered_issues[file_path] = {
                        "errors": file_issues["errors"],
                        "warnings": [],
                        "info": [],
                    }
            issues = filtered_issues

        # 生成报告
        error_count = generate_report(issues, args.verbose)

        # 返回状态码
        return 1 if error_count > 0 else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
