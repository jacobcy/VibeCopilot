#!/usr/bin/env python
"""
YAML验证器集成包

提供将YAML验证器集成到现有YAML同步服务的功能
"""

from examples.roadmap_sync.yaml_integration.cli import main, setup_args
from examples.roadmap_sync.yaml_integration.core import (
    backup_yaml_sync,
    check_files_exist,
    integrate_validator,
    restore_yaml_sync,
    validate_yaml_file,
)
from examples.roadmap_sync.yaml_integration.utils import read_file_content, write_file_content

__all__ = [
    "main",
    "setup_args",
    "check_files_exist",
    "backup_yaml_sync",
    "restore_yaml_sync",
    "integrate_validator",
    "validate_yaml_file",
    "read_file_content",
    "write_file_content",
]
