#!/usr/bin/env python3
import filecmp
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Tuple

# 默认排除的文件和目录模式
DEFAULT_EXCLUDES = {
    # Python
    "*.pyc",
    "__pycache__",
    "*.pyo",
    "*.pyd",
    ".Python",
    "*.so",
    # 虚拟环境
    "env/",
    "venv/",
    ".env/",
    ".venv/",
    # 编辑器和IDE
    ".idea/",
    ".vscode/",
    "*.swp",
    ".DS_Store",
    # 构建和缓存
    "build/",
    "dist/",
    "*.egg-info/",
    ".pytest_cache/",
    ".coverage",
    "htmlcov/",
    # Node.js
    "node_modules/",
    "package-lock.json",
    "yarn.lock",
}


def should_exclude(file_path: str, exclude_patterns: Set[str]) -> bool:
    """检查文件是否应该被排除"""
    path = Path(file_path)

    # 检查文件名或目录名是否匹配任何排除模式
    for pattern in exclude_patterns:
        # 移除末尾的斜杠（用于目录模式）
        pattern = pattern.rstrip("/")

        # 如果模式以*开头，只检查文件扩展名
        if pattern.startswith("*"):
            if path.name.endswith(pattern[1:]):
                return True
        # 否则检查完整路径
        elif pattern in str(path):
            return True

    return False


def calculate_file_hash(file_path: str) -> str:
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_all_files(directory: str, exclude_patterns: Set[str]) -> Dict[str, str]:
    """获取目录下所有文件的相对路径和哈希值，排除指定的文件"""
    files = {}
    directory = Path(directory)
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(directory))
            # 检查是否应该排除该文件
            if not should_exclude(relative_path, exclude_patterns):
                files[relative_path] = calculate_file_hash(str(file_path))
    return files


def compare_directories(dir1: str, dir2: str, exclude_patterns: Set[str]) -> Tuple[Set[str], Set[str], Set[str]]:
    """比较两个目录，返回缺失的、新增的和修改的文件"""
    # 获取两个目录的所有文件
    files1 = get_all_files(dir1, exclude_patterns)
    files2 = get_all_files(dir2, exclude_patterns)

    # 获取文件路径集合
    paths1 = set(files1.keys())
    paths2 = set(files2.keys())

    # 找出缺失和新增的文件
    missing_files = paths1 - paths2  # 在dir1中存在但在dir2中不存在的文件
    new_files = paths2 - paths1  # 在dir2中存在但在dir1中不存在的文件

    # 找出修改过的文件
    common_files = paths1 & paths2
    modified_files = {f for f in common_files if files1[f] != files2[f]}

    return missing_files, new_files, modified_files


def generate_report(dir1: str, dir2: str, missing: Set[str], new: Set[str], modified: Set[str], exclude_patterns: Set[str]) -> str:
    """生成比较报告"""
    report = []
    report.append(f"目录比较报告")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n源目录: {dir1}")
    report.append(f"目标目录: {dir2}")

    report.append("\n排除的文件模式:")
    for pattern in sorted(exclude_patterns):
        report.append(f"  - {pattern}")

    report.append("\n缺失的文件:")
    for file in sorted(missing):
        report.append(f"  - {file}")

    report.append("\n新增的文件:")
    for file in sorted(new):
        report.append(f"  + {file}")

    report.append("\n修改的文件:")
    for file in sorted(modified):
        report.append(f"  * {file}")

    report.append(f"\n统计信息:")
    report.append(f"- 缺失文件数: {len(missing)}")
    report.append(f"- 新增文件数: {len(new)}")
    report.append(f"- 修改文件数: {len(modified)}")

    return "\n".join(report)


def parse_exclude_patterns(patterns_file: str) -> Set[str]:
    """从文件中读取排除模式"""
    if not patterns_file:
        return DEFAULT_EXCLUDES

    try:
        with open(patterns_file, "r") as f:
            patterns = {line.strip() for line in f if line.strip() and not line.startswith("#")}
        return patterns | DEFAULT_EXCLUDES  # 合并自定义模式和默认模式
    except FileNotFoundError:
        print(f"警告: 排除模式文件 '{patterns_file}' 不存在，使用默认排除模式")
        return DEFAULT_EXCLUDES


def main():
    import argparse

    parser = argparse.ArgumentParser(description="比较两个目录的差异")
    parser.add_argument("dir1", help="源目录路径")
    parser.add_argument("dir2", help="目标目录路径")
    parser.add_argument("-o", "--output", help="输出报告文件路径")
    parser.add_argument("-e", "--exclude-file", help="包含排除模式的文件路径")
    parser.add_argument("--show-excludes", action="store_true", help="显示默认排除模式并退出")
    args = parser.parse_args()

    # 显示默认排除模式
    if args.show_excludes:
        print("默认排除的文件和目录模式:")
        for pattern in sorted(DEFAULT_EXCLUDES):
            print(f"  {pattern}")
        return

    # 检查目录是否存在
    if not os.path.isdir(args.dir1):
        print(f"错误: 源目录 '{args.dir1}' 不存在")
        return
    if not os.path.isdir(args.dir2):
        print(f"错误: 目标目录 '{args.dir2}' 不存在")
        return

    # 获取排除模式
    exclude_patterns = parse_exclude_patterns(args.exclude_file)

    # 比较目录
    missing, new, modified = compare_directories(args.dir1, args.dir2, exclude_patterns)

    # 生成报告
    report = generate_report(args.dir1, args.dir2, missing, new, modified, exclude_patterns)

    # 输出报告
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存到: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
