"""
规则初始数据模块

提供规则表的初始数据
"""

import logging
from datetime import datetime

from src.db import get_session
from src.db.repositories.rule_repository import RuleRepository

logger = logging.getLogger(__name__)


def init_rules():
    """初始化规则数据"""
    session = get_session()
    repo = RuleRepository(session)

    # 添加一些示例规则
    rules = [
        {
            "name": "命名规范",
            "description": "项目命名规范",
            "content": """
# 命名规范

## 文件命名
- 组件文件使用PascalCase
- 普通文件使用kebab-case
- 测试文件以.test.ts结尾

## 变量命名
- 使用camelCase
- 常量使用UPPER_SNAKE_CASE
- 私有变量以_开头

## 类型命名
- 接口以I开头
- 类型使用PascalCase
- 枚举使用PascalCase
""",
            "category": "core",
            "priority": "P0",
            "status": "active",
        }
    ]

    success_count = 0
    for rule in rules:
        try:
            repo.create(**rule)
            success_count += 1
        except Exception as e:
            logger.error(f"创建规则失败: {rule['name']}", exc_info=True)

    logger.info(f"规则初始化完成: 成功 {success_count}/{len(rules)}")
    session.close()
