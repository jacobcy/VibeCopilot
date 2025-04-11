#!/usr/bin/env python3
"""
路线图命令迁移脚本

执行从旧版路线图命令到新版Click实现的迁移操作。
此脚本会执行以下步骤：
1. 创建备份目录
2. 复制旧代码到备份目录
3. 将新代码复制到正式目录
4. 更新导入路径

使用方式：
    python migrate_roadmap.py [--dry-run] [--no-backup]

参数：
    --dry-run: 仅打印将要执行的操作，不实际执行
    --no-backup: 不创建备份，直接替换（谨慎使用）
"""

import argparse
import os
import shutil
import sys

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="路线图命令迁移脚本")
    parser.add_argument("--dry-run", action="store_true", help="仅打印将要执行的操作，不实际执行")
    parser.add_argument("--no-backup", action="store_true", help="不创建备份，直接替换（谨慎使用）")
    return parser.parse_args()


def create_backup(src_dir, backup_dir, dry_run=False):
    """创建备份"""
    print(f"备份 {src_dir} 到 {backup_dir}")

    if dry_run:
        print(f"[DRY RUN] 将会复制 {src_dir} 到 {backup_dir}")
        return True

    try:
        if os.path.exists(backup_dir):
            print(f"备份目录 {backup_dir} 已存在，正在删除...")
            shutil.rmtree(backup_dir)

        print(f"正在复制 {src_dir} 到 {backup_dir}...")
        shutil.copytree(src_dir, backup_dir)
        print("备份完成")
        return True
    except Exception as e:
        print(f"备份失败: {str(e)}")
        return False


def replace_with_new(new_dir, target_dir, dry_run=False):
    """用新代码替换旧代码"""
    print(f"替换 {target_dir} 为 {new_dir} 中的内容")

    if dry_run:
        print(f"[DRY RUN] 将会删除 {target_dir} 并用 {new_dir} 替换")
        return True

    try:
        if os.path.exists(target_dir):
            print(f"目标目录 {target_dir} 已存在，正在删除...")
            shutil.rmtree(target_dir)

        print(f"正在复制 {new_dir} 到 {target_dir}...")
        shutil.copytree(new_dir, target_dir)
        print("替换完成")
        return True
    except Exception as e:
        print(f"替换失败: {str(e)}")
        return False


def main():
    """主函数"""
    args = parse_args()

    # 定义路径
    src_cli = os.path.join(project_root, "src", "cli", "commands")
    old_roadmap = os.path.join(src_cli, "roadmap")
    new_roadmap = os.path.join(src_cli, "roadmap_new")
    backup_roadmap = os.path.join(src_cli, "roadmap_bak")

    # 检查目录是否存在
    if not os.path.exists(old_roadmap):
        print(f"错误: 旧版路线图目录不存在: {old_roadmap}")
        return 1

    if not os.path.exists(new_roadmap):
        print(f"错误: 新版路线图目录不存在: {new_roadmap}")
        return 1

    # 执行迁移步骤
    print("开始执行路线图命令迁移...")

    # 1. 创建备份
    if not args.no_backup:
        if not create_backup(old_roadmap, backup_roadmap, args.dry_run):
            print("迁移中止: 备份失败")
            return 1
    else:
        print("跳过备份步骤")

    # 2. 替换为新代码
    if not replace_with_new(new_roadmap, old_roadmap, args.dry_run):
        print("迁移中止: 替换失败")
        return 1

    print("路线图命令迁移完成!")
    if args.dry_run:
        print("[DRY RUN] 这只是一次演示，没有实际修改文件")

    return 0


if __name__ == "__main__":
    sys.exit(main())
