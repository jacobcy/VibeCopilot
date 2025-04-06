#!/usr/bin/env python
"""
YAML验证器集成脚本

提供将YAML验证器集成到现有YAML同步服务的功能
"""

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# 将项目根目录添加到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

try:
    from src.roadmap.sync.yaml_validator import RoadmapYamlValidator
except ImportError:
    sys.exit("错误: 无法导入RoadmapYamlValidator模块，请确保已正确安装")

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("yaml_integration")

# 定义YAML同步服务文件路径
YAML_SYNC_PATH = os.path.join(project_root, "src", "roadmap", "sync", "yaml.py")
YAML_SYNC_BACKUP_PATH = os.path.join(project_root, "src", "roadmap", "sync", "yaml.py.bak")
YAML_VALIDATOR_PATH = os.path.join(project_root, "src", "roadmap", "sync", "yaml_validator.py")


def check_files_exist() -> bool:
    """
    检查必要的文件是否存在

    Returns:
        bool: 是否所有文件都存在
    """
    files_exist = True

    # 检查YAML同步服务文件
    if not os.path.exists(YAML_SYNC_PATH):
        logger.error(f"错误: YAML同步服务文件不存在: {YAML_SYNC_PATH}")
        files_exist = False

    # 检查YAML验证器文件
    if not os.path.exists(YAML_VALIDATOR_PATH):
        logger.error(f"错误: YAML验证器文件不存在: {YAML_VALIDATOR_PATH}")
        files_exist = False

    return files_exist


def backup_yaml_sync() -> bool:
    """
    备份原始YAML同步服务文件

    Returns:
        bool: 是否成功备份
    """
    try:
        # 检查是否已经有备份
        if os.path.exists(YAML_SYNC_BACKUP_PATH):
            logger.warning(f"备份文件已存在: {YAML_SYNC_BACKUP_PATH}")
            return True

        # 复制文件
        shutil.copy2(YAML_SYNC_PATH, YAML_SYNC_BACKUP_PATH)
        logger.info(f"已备份YAML同步服务文件: {YAML_SYNC_BACKUP_PATH}")
        return True

    except Exception as e:
        logger.error(f"备份YAML同步服务文件失败: {str(e)}")
        return False


def restore_yaml_sync() -> bool:
    """
    从备份恢复YAML同步服务文件

    Returns:
        bool: 是否成功恢复
    """
    try:
        # 检查备份是否存在
        if not os.path.exists(YAML_SYNC_BACKUP_PATH):
            logger.error(f"备份文件不存在: {YAML_SYNC_BACKUP_PATH}")
            return False

        # 复制文件
        shutil.copy2(YAML_SYNC_BACKUP_PATH, YAML_SYNC_PATH)
        logger.info(f"已恢复YAML同步服务文件: {YAML_SYNC_PATH}")
        return True

    except Exception as e:
        logger.error(f"恢复YAML同步服务文件失败: {str(e)}")
        return False


def read_file_content(file_path: str) -> Optional[str]:
    """
    读取文件内容

    Args:
        file_path: 文件路径

    Returns:
        Optional[str]: 文件内容，失败则返回None
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
        return None


def write_file_content(file_path: str, content: str) -> bool:
    """
    写入文件内容

    Args:
        file_path: 文件路径
        content: 文件内容

    Returns:
        bool: 是否成功写入
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"写入文件失败: {file_path}, 错误: {str(e)}")
        return False


def integrate_validator() -> bool:
    """
    将验证器集成到YAML同步服务

    Returns:
        bool: 是否成功集成
    """
    # 读取YAML同步服务文件内容
    yaml_sync_content = read_file_content(YAML_SYNC_PATH)
    if not yaml_sync_content:
        return False

    # 检查是否已集成
    if "RoadmapYamlValidator" in yaml_sync_content:
        logger.info("验证器已集成到YAML同步服务中")
        return True

    # 备份原始文件
    if not backup_yaml_sync():
        return False

    # 添加导入语句
    import_statement = "from src.roadmap.sync.yaml_validator import RoadmapYamlValidator"
    if import_statement not in yaml_sync_content:
        import_lines = yaml_sync_content.split("\n", 30)
        for i, line in enumerate(import_lines):
            if line.startswith("import ") or line.startswith("from "):
                last_import_line = i

        import_lines.insert(last_import_line + 1, import_statement)
        yaml_sync_content = "\n".join(import_lines)

    # 修改import_yaml方法
    original_import_method = """    def import_yaml(self, yaml_path: str) -> str:
        \"\"\"从YAML文件导入路线图数据\"\"\"
        try:
            with open(yaml_path, 'r', encoding='utf-8') as file:
                yaml_data = yaml.safe_load(file)

            # 处理YAML数据
            roadmap_name = self._process_yaml_data(yaml_data)
            return roadmap_name

        except Exception as e:
            logger.error(f"从YAML导入失败: {str(e)}")
            raise ValueError(f"导入YAML失败: {str(e)}")"""

    modified_import_method = """    def import_yaml(self, yaml_path: str) -> str:
        \"\"\"从YAML文件导入路线图数据\"\"\"
        try:
            # 验证YAML文件格式
            validator = RoadmapYamlValidator()
            is_valid, messages, fixed_data = validator.validate(yaml_path)

            if not is_valid:
                logger.warning("YAML文件格式验证失败:")
                for msg in messages:
                    logger.warning(f"  {msg}")

                # 创建修复后的文件
                fixed_path = f"{os.path.splitext(yaml_path)[0]}_fixed.yaml"
                validator.generate_fixed_yaml(fixed_data, fixed_path)
                logger.info(f"已生成修复后的文件: {fixed_path}")

                # 提示确认是否继续
                print("=" * 50)
                print("⚠️ YAML文件格式验证失败")
                print(f"✅ 已生成修复后的文件: {fixed_path}")
                print("=" * 50)
                continue_import = input("是否继续导入? (y/n): ").lower().strip() == 'y'

                if not continue_import:
                    raise ValueError("用户取消了导入操作")

                # 使用修复后的数据
                yaml_data = fixed_data
            else:
                # 读取YAML文件
                with open(yaml_path, 'r', encoding='utf-8') as file:
                    yaml_data = yaml.safe_load(file)

            # 处理YAML数据
            roadmap_name = self._process_yaml_data(yaml_data)
            return roadmap_name

        except Exception as e:
            logger.error(f"从YAML导入失败: {str(e)}")
            raise ValueError(f"导入YAML失败: {str(e)}")"""

    # 替换方法
    yaml_sync_content = yaml_sync_content.replace(original_import_method, modified_import_method)

    # 写入修改后的文件
    if write_file_content(YAML_SYNC_PATH, yaml_sync_content):
        logger.info("已成功集成验证器到YAML同步服务")
        return True
    else:
        return False


def validate_yaml_file(yaml_path: str, fix: bool = False) -> None:
    """
    验证YAML文件

    Args:
        yaml_path: YAML文件路径
        fix: 是否自动修复
    """
    if not os.path.exists(yaml_path):
        logger.error(f"文件不存在: {yaml_path}")
        return

    validator = RoadmapYamlValidator()
    is_valid, message = validator.check_and_suggest(yaml_path, fix)

    print("\n" + message + "\n")

    if not is_valid and fix:
        fixed_path = f"{os.path.splitext(yaml_path)[0]}_fixed.yaml"
        if os.path.exists(fixed_path):
            logger.info(f"修复后的文件已生成: {fixed_path}")


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


if __name__ == "__main__":
    main()
