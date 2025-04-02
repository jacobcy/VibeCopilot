"""
pytest配置文件
"""

import logging

import pytest


# 配置日志
@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


# 可以添加更多全局fixture
