"""
规则初始化数据模块

提供规则表的初始数据
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict

from src.core.config import refresh_config
from src.db import get_session
from src.db.repositories.rule_repository import RuleExampleRepository, RuleItemRepository, RuleRepository
from src.models.base import RuleType

logger = logging.getLogger(__name__)

default_rules = []
default_rule_items = []
default_rule_examples = []


def init_rules() -> Dict[str, int]:
    """初始化规则数据，并返回统计"""
    # 刷新配置
    refresh_config()

    session = get_session()
    rule_repo = RuleRepository()
    item_repo = RuleItemRepository()
    example_repo = RuleExampleRepository()

    success_count = 0
    fail_count = 0

    # 检查表是否为空
    rule_count = rule_repo.count(session)
    item_count = item_repo.count(session)
    example_count = example_repo.count(session)

    # 只有当所有相关表都为空时才初始化
    if rule_count == 0 and item_count == 0 and example_count == 0:
        logger.info("规则相关表为空，开始初始化默认规则...")
        # 添加一些示例规则
        rules = [
            {
                "id": f"rule_{uuid.uuid4().hex[:8]}",
                "name": "命名规范",
                "type": RuleType.RULE.value,
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
                "globs": json.dumps(["*.ts", "*.tsx", "*.py"]),
                "always_apply": True,
                "author": "system",
                "version": "1.0.0",
                "tags": json.dumps(["naming", "convention", "core"]),
                "dependencies": json.dumps([]),
                "usage_count": 0,
                "effectiveness": 80,
            }
        ]

        for rule in rules:
            try:
                # Pass session to create method
                rule_repo.create(session, data=rule)
                success_count += 1
            except Exception as e:
                logger.error(f"创建规则失败: {rule['name']}", exc_info=True)
                fail_count += 1
    else:
        logger.info(f"规则表不为空 (Rules: {rule_count}, Items: {item_count}, Examples: {example_count})，跳过初始化")

    session.close()
    logger.info(f"规则初始化完成: 成功 {success_count}, 失败 {fail_count}")
    return {"success": success_count, "failed": fail_count}
