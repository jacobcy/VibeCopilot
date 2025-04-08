"""
规则仓库使用示例

展示RuleRepository的基本用法，包括创建、查询、更新和删除规则。
"""

import json
import logging
import uuid
from datetime import datetime

from src.db import RuleRepository, get_engine, get_session_factory, init_db

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.debug("初始化数据库...")
    engine = init_db()
    SessionFactory = get_session_factory(engine)

    with SessionFactory() as session:
        repo = RuleRepository(session)
        logger.info("RuleRepository创建成功")

        # 创建一个新规则
        rule_id = f"example-rule-{uuid.uuid4().hex[:8]}"
        logger.info(f"创建新规则，ID: {rule_id}")

        rule_data = {
            "id": rule_id,
            "name": "示例规则",
            "type": "tech",  # 技术规则
            "description": "这是一个用于演示的示例规则",
            "globs": json.dumps(["*.py", "*.md"]),  # 适用于Python和Markdown文件
            "always_apply": False,
            "content": "# 示例规则\n\n这是一个演示规则，用于展示规则仓库的功能。",
            "author": "VibeCopilot",
            "tags": json.dumps(["example", "demo"]),
            "version": "1.0.0",
        }

        # 规则条目
        items = [{"content": "始终使用明确的变量名称", "priority": 8, "category": "命名规范"}, {"content": "函数应该有清晰的文档字符串", "priority": 7, "category": "文档规范"}]

        # 规则示例
        examples = [
            {
                "content": 'def calculate_total(items):\n    """计算总金额"""\n    return sum(item.price for item in items)',
                "is_valid": True,
                "description": "好的示例：函数有清晰的文档",
            },
            {"content": "def calc(x):\n    return x * 1.1", "is_valid": False, "description": "不良示例：缺少文档且变量名不明确"},
        ]

        # 创建规则（包含条目和示例）
        rule = repo.create_rule(rule_data, items, examples)
        logger.info(f"规则创建成功: {rule.name} (ID: {rule.id})")

        # 查询规则
        retrieved_rule = repo.get_by_id(rule.id)
        logger.info(f"查询到规则: {retrieved_rule.name} (ID: {retrieved_rule.id})")
        logger.info(f"规则描述: {retrieved_rule.description}")
        logger.info(f"规则条目数量: {len(retrieved_rule.items)}")
        logger.info(f"规则示例数量: {len(retrieved_rule.examples)}")

        # 按类型查询规则
        tech_rules = repo.get_by_type("tech")
        logger.info(f"技术类规则数量: {len(tech_rules)}")

        # 查询适用于特定文件的规则
        file_path = "example.py"
        applicable_rules = repo.get_for_file(file_path)
        logger.info(f"适用于{file_path}的规则数量: {len(applicable_rules)}")

        # 更新规则
        updated_data = {"description": "这是一个已更新的示例规则", "version": "1.0.1", "updated_at": datetime.utcnow()}
        updated_rule = repo.update(rule.id, updated_data)
        logger.info(f"规则已更新: {updated_rule.description} (版本: {updated_rule.version})")

        # 更新规则，包括关联数据
        new_items = [{"content": "使用类型注解提高代码可读性", "priority": 9, "category": "类型安全"}, {"content": "避免使用全局变量", "priority": 6, "category": "代码结构"}]

        updated_rule = repo.update_rule_with_relations(rule.id, {"description": "带有新条目的规则"}, items=new_items)
        logger.info(f"规则及关联数据已更新: {updated_rule.description}")
        logger.info(f"新的规则条目数量: {len(updated_rule.items)}")

        # 删除规则
        # 注意：在实际使用中，可能需要添加确认机制
        logger.info(f"删除规则: {rule.id}")
        deleted = repo.delete(rule.id)
        logger.info(f"规则删除{'成功' if deleted else '失败'}")

        # 验证删除结果
        check_rule = repo.get_by_id(rule.id)
        logger.info(f"删除后查询结果: {'找不到规则' if check_rule is None else '规则仍存在'}")


if __name__ == "__main__":
    main()
