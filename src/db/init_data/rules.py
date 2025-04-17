"""
规则初始数据模块

提供规则表的初始数据
"""

import json
import logging
import uuid
from datetime import datetime

from src.core.config import refresh_config
from src.db import get_session
from src.db.repositories.rule_repository import RuleRepository
from src.models.base import RuleType

logger = logging.getLogger(__name__)


def init_rules():
    """初始化规则数据"""
    # 刷新配置
    refresh_config()

    session = get_session()
    # Initialize repo without session
    repo = RuleRepository()

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

    success_count = 0
    for rule in rules:
        try:
            # Pass session to create method
            repo.create(session, data=rule)
            success_count += 1
        except Exception as e:
            logger.error(f"创建规则失败: {rule['name']}", exc_info=True)

    logger.info(f"规则初始化完成: 成功 {success_count}/{len(rules)}")
    session.close()
