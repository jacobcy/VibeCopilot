#!/usr/bin/env python
"""
YAML验证器集成核心功能

提供验证器集成和YAML文件验证的核心功能
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

from examples.roadmap_sync.yaml_integration.utils import read_file_content, write_file_content

# 使用src.validation中的验证器
from src.validation.validator_factory import ValidatorFactory

# 配置日志
logger = logging.getLogger("yaml_integration.core")

# 获取项目根目录
current_dir = Path(__file__).parent.parent.parent.parent
project_root = current_dir

# 定义YAML同步服务文件路径
YAML_SYNC_PATH = os.path.join(project_root, "src", "roadmap", "sync", "yaml.py")
YAML_SYNC_BACKUP_PATH = os.path.join(project_root, "src", "roadmap", "sync", "yaml.py.bak")
VALIDATOR_PATH = os.path.join(project_root, "src", "validation", "core", "yaml_validator.py")


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
    if not os.path.exists(VALIDATOR_PATH):
        logger.error(f"错误: YAML验证器文件不存在: {VALIDATOR_PATH}")
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
    if "ValidatorFactory" in yaml_sync_content:
        logger.info("验证器已集成到YAML同步服务中")
        return True

    # 备份原始文件
    if not backup_yaml_sync():
        return False

    # 添加导入语句
    import_statement = "from src.validation.validator_factory import ValidatorFactory"
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
            validator = ValidatorFactory.get_validator_for_file(yaml_path)
            result = validator.validate_from_file(yaml_path)

            if not result.is_valid:
                logger.warning("YAML文件格式验证失败:")
                for msg in result.messages:
                    logger.warning(f"  {msg}")

                # 创建修复后的文件
                fixed_path = f"{os.path.splitext(yaml_path)[0]}_fixed.yaml"
                validator.generate_fixed_yaml(result.data, fixed_path)
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
                yaml_data = result.data
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

    # 使用ValidatorFactory获取适当的验证器
    validator = ValidatorFactory.get_validator_for_file(yaml_path)
    result = validator.validate_from_file(yaml_path)

    message = "验证结果:\n"
    if result.is_valid:
        message += "✅ YAML文件格式验证通过\n"
    else:
        message += "❌ YAML文件格式验证失败:\n"
        for msg in result.messages:
            message += f"  - {msg}\n"

        if fix:
            # 创建修复后的文件
            fixed_path = f"{os.path.splitext(yaml_path)[0]}_fixed.yaml"
            success = validator.generate_fixed_yaml(result.data, fixed_path)
            if success:
                message += f"\n✅ 已生成修复后的文件: {fixed_path}\n"
                logger.info(f"修复后的文件已生成: {fixed_path}")
            else:
                message += "\n❌ 无法生成修复后的文件\n"

    print("\n" + message + "\n")
