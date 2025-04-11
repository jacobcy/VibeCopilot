#!/usr/bin/env python
"""
路线图YAML验证工具命令行界面

提供命令行工具，用于验证和修复路线图YAML文件
"""

import argparse
import logging
import os
import sys
from typing import List, Optional

# 将项目根目录添加到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.roadmap.validator.yaml_validator import RoadmapYamlValidator

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("yaml_validator_cli")


def setup_args() -> argparse.ArgumentParser:
    """设置命令行参数"""
    parser = argparse.ArgumentParser(
        description="路线图YAML验证工具 - 用于验证和修复路线图YAML文件格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  验证YAML文件:
    python yaml_validator_cli.py validate path/to/roadmap.yaml

  自动修复YAML文件:
    python yaml_validator_cli.py validate path/to/roadmap.yaml --fix

  显示标准模板:
    python yaml_validator_cli.py template

  生成标准模板:
    python yaml_validator_cli.py template --output path/to/template.yaml

  批量验证多个文件:
    python yaml_validator_cli.py validate path/to/roadmap1.yaml path/to/roadmap2.yaml
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # validate 命令
    validate_parser = subparsers.add_parser("validate", help="验证YAML文件")
    validate_parser.add_argument("yaml_files", nargs="+", help="要验证的YAML文件路径，支持多个文件")
    validate_parser.add_argument("--fix", action="store_true", help="自动修复并生成新的YAML文件")
    validate_parser.add_argument("--template", help="指定自定义模板文件路径")

    # template 命令
    template_parser = subparsers.add_parser("template", help="显示或生成标准模板")
    template_parser.add_argument("--output", "-o", help="输出模板文件的路径")

    return parser


def validate_yaml_files(yaml_files: List[str], fix: bool = False, template_path: Optional[str] = None) -> bool:
    """
    验证多个YAML文件

    Args:
        yaml_files: YAML文件路径列表
        fix: 是否自动修复
        template_path: 自定义模板路径

    Returns:
        bool: 是否全部验证通过
    """
    validator = RoadmapYamlValidator(template_path)
    all_valid = True

    for yaml_file in yaml_files:
        logger.info(f"正在验证文件: {yaml_file}")
        is_valid, message = validator.check_and_suggest(yaml_file, fix)
        print("\n" + message + "\n")

        if not is_valid:
            all_valid = False

    return all_valid


def show_template(output_path: Optional[str] = None) -> None:
    """
    显示或生成标准模板

    Args:
        output_path: 输出文件路径，不提供则打印到控制台
    """
    validator = RoadmapYamlValidator()
    template_str = validator.show_template()

    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(template_str)
            logger.info(f"标准模板已生成至: {output_path}")
        except Exception as e:
            logger.error(f"生成模板文件失败: {str(e)}")
    else:
        print("\n=== 路线图YAML标准模板 ===\n")
        print(template_str)


def main() -> None:
    """主函数"""
    parser = setup_args()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "validate":
            success = validate_yaml_files(args.yaml_files, fix=args.fix, template_path=args.template)

            if success:
                logger.info("所有文件验证通过！")
                sys.exit(0)
            else:
                logger.warning("部分文件验证失败，请检查详细信息")
                sys.exit(1)

        elif args.command == "template":
            show_template(args.output)

    except KeyboardInterrupt:
        logger.info("已取消操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"验证过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
