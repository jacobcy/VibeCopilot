#!/usr/bin/env python
"""
YAML验证器集成命令行接口

提供命令行参数解析和主函数
"""

import argparse
import logging
import sys

from examples.roadmap_sync.yaml_integration.core import (
    YAML_SYNC_BACKUP_PATH,
    backup_yaml_sync,
    check_files_exist,
    integrate_validator,
    restore_yaml_sync,
    validate_yaml_file,
)

# 配置日志
logger = logging.getLogger("yaml_integration.cli")


def setup_args() -> argparse.ArgumentParser:
    """设置命令行参数"""
    parser = argparse.ArgumentParser(
        description="YAML验证器集成工具 - 将验证器集成到YAML同步服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  集成验证器:
    python yaml_integration.py --integrate

  恢复原始文件:
    python yaml_integration.py --restore

  验证YAML文件:
    python yaml_integration.py --validate path/to/roadmap.yaml

  验证并修复YAML文件:
    python yaml_integration.py --validate path/to/roadmap.yaml --fix
""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--integrate", action="store_true", help="将验证器集成到YAML同步服务")
    group.add_argument("--restore", action="store_true", help="恢复原始的YAML同步服务文件")
    group.add_argument("--validate", metavar="YAML_FILE", help="验证YAML文件")

    parser.add_argument("--fix", action="store_true", help="自动修复YAML文件，与--validate一起使用")

    return parser


def main() -> None:
    """主函数"""
    parser = setup_args()
    args = parser.parse_args()

    # 检查文件
    if not check_files_exist():
        sys.exit(1)

    try:
        if args.integrate:
            # 集成验证器
            if integrate_validator():
                print("\n✅ 已成功集成验证器到YAML同步服务")
                print(f"👉 原始文件已备份至: {YAML_SYNC_BACKUP_PATH}")
            else:
                print("\n❌ 集成验证器失败")
                sys.exit(1)

        elif args.restore:
            # 恢复原始文件
            if restore_yaml_sync():
                print("\n✅ 已成功恢复原始的YAML同步服务文件")
            else:
                print("\n❌ 恢复原始文件失败")
                sys.exit(1)

        elif args.validate:
            # 验证YAML文件
            validate_yaml_file(args.validate, args.fix)

    except KeyboardInterrupt:
        logger.info("已取消操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        sys.exit(1)
