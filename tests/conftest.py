"""
pytest配置文件
"""

import logging
import os
import sys
from pathlib import Path

import pytest

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# 配置日志
@pytest.fixture(autouse=True)
def setup_logging():
    """设置测试日志配置"""
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@pytest.fixture(scope="session")
def project_root():
    """返回项目根目录路径"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir():
    """返回测试数据目录路径"""
    data_dir = PROJECT_ROOT / "tests" / "fixtures"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def temp_dir(tmp_path_factory):
    """创建临时目录用于测试"""
    return tmp_path_factory.mktemp("vibecopilot_test_")


# 可以添加更多全局fixture
