"""
健康检查配置加载模块
"""
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import click
import yaml

# 配置文件默认路径
DEFAULT_CONFIG_PATH = Path(__file__).parent / "config"
DEFAULT_BASE_CONFIG = DEFAULT_CONFIG_PATH / "check_config.yaml"
DEFAULT_COMMAND_CONFIG = DEFAULT_CONFIG_PATH / "commands" / "config.yaml"
DEFAULT_DATABASE_CONFIG = DEFAULT_CONFIG_PATH / "database_check_config.yaml"
DEFAULT_SYSTEM_CONFIG = DEFAULT_CONFIG_PATH / "system_check_config.yaml"
DEFAULT_STATUS_CONFIG = DEFAULT_CONFIG_PATH / "status_check_config.yaml"


def load_config(config_path: Optional[Path] = None) -> Dict:
    """加载配置文件

    Args:
        config_path: 配置文件路径，如果为None则使用默认配置

    Returns:
        Dict: 配置信息
    """
    if not config_path:
        config_path = DEFAULT_BASE_CONFIG

    if not config_path.exists():
        click.echo(f"错误: 配置文件不存在: {config_path}", err=True)
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        click.echo(f"错误: 读取配置文件失败: {e}", err=True)
        sys.exit(1)


def load_module_config(module: str) -> Dict:
    """加载特定模块的配置

    Args:
        module: 模块名称

    Returns:
        Dict: 模块配置
    """
    if module == "command":
        config_path = DEFAULT_COMMAND_CONFIG
    elif module == "database":
        config_path = DEFAULT_DATABASE_CONFIG
    elif module == "system":
        config_path = DEFAULT_SYSTEM_CONFIG
    elif module == "status":
        config_path = DEFAULT_STATUS_CONFIG
    else:
        click.echo(f"错误: 未知模块: {module}", err=True)
        sys.exit(1)

    if not config_path.exists():
        click.echo(f"错误: 模块配置文件不存在: {config_path}", err=True)
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        click.echo(f"错误: 读取模块配置文件失败: {e}", err=True)
        sys.exit(1)
