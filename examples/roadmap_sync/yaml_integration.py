#!/usr/bin/env python
"""
YAML验证器集成入口点

此模块是YAML验证器集成功能的入口点，提供命令行接口
用于将YAML验证器集成到YAML同步服务中
"""

import logging
import os
import sys
from pathlib import Path

# 将项目根目录添加到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 尝试导入集成模块
try:
    from examples.roadmap_sync.yaml_integration.cli import main
except ImportError:
    sys.exit("错误: 无法导入YAML集成模块，请确保已正确安装")

if __name__ == "__main__":
    main()
