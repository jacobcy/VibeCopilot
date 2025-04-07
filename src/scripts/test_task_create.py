#!/usr/bin/env python
"""
测试Task创建脚本

分析Task对象创建过程
"""

import logging
import sys
import uuid
from datetime import datetime

from src.db import get_engine, get_session_factory
from src.models.db.roadmap import Task

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        # 创建测试数据
        task_id = f"T{uuid.uuid4().hex[:6]}"

        # 测试数据集，包含各种形式
        test_datasets = [
            # 使用位置参数
            (task_id, "测试任务1", None, "描述1", "todo", "P1"),
            # 使用关键字参数
            {
                "id": task_id,
                "title": "测试任务2",
                "description": "描述2",
                "status": "todo",
                "priority": "P1",
            },
            # 使用字典拆包
            {
                "id": task_id,
                "title": "测试任务3",
                "description": "描述3",
                "status": "todo",
                "priority": "P1",
            },
        ]

        # 尝试创建任务实例
        for i, data in enumerate(test_datasets):
            logger.info(f"测试 #{i+1}")
            if isinstance(data, tuple):
                logger.info(f"使用位置参数: {data}")
                try:
                    task = Task(*data)
                    logger.info(f"✅ 任务创建成功，ID: {task.id}")
                    print_task_attrs(task)
                except Exception as e:
                    logger.error(f"❌ 使用位置参数创建失败: {e}")
            else:
                logger.info(f"使用关键字参数: {data}")

                # 先测试直接传递字典
                try:
                    logger.info("尝试方法1: 传递字典作为参数")
                    task = Task(data)
                    logger.info(f"✅ 任务创建成功，ID: {task.id}")
                    print_task_attrs(task)
                except Exception as e:
                    logger.error(f"❌ 方法1创建失败: {e}")

                # 再测试拆包字典
                try:
                    logger.info("尝试方法2: 拆包字典")
                    task = Task(**data)
                    logger.info(f"✅ 任务创建成功，ID: {task.id}")
                    print_task_attrs(task)
                except Exception as e:
                    logger.error(f"❌ 方法2创建失败: {e}")

        # 测试数据库连接和会话
        logger.info("测试与数据库的交互")
        engine = get_engine()
        session_factory = get_session_factory(engine)
        session = session_factory()

        # 创建新任务并保存到数据库
        new_task_id = f"T{uuid.uuid4().hex[:6]}"
        new_task = Task(
            id=new_task_id, title="数据库测试任务", description="测试数据库操作", status="todo", priority="P1"
        )

        # 添加到会话
        logger.info(f"将任务添加到数据库: {new_task_id}")
        session.add(new_task)

        # 提交事务
        try:
            session.commit()
            logger.info("✅ 任务成功保存到数据库")
        except Exception as e:
            session.rollback()
            logger.error(f"❌ 保存到数据库失败: {e}")

        # 从数据库中读取
        try:
            saved_task = session.query(Task).filter(Task.id == new_task_id).first()
            if saved_task:
                logger.info(f"✅ 成功从数据库读取任务: {saved_task.id}")
                print_task_attrs(saved_task)
            else:
                logger.error("❌ 无法从数据库读取任务")
        except Exception as e:
            logger.error(f"❌ 读取任务失败: {e}")

        # 关闭会话
        session.close()

        return 0
    except Exception as e:
        logger.error(f"测试过程出现错误: {e}")
        return 1


def print_task_attrs(task):
    """打印任务属性"""
    print("\n任务属性:")
    print("=" * 50)
    for attr_name in dir(task):
        if not attr_name.startswith("_"):
            attr_value = getattr(task, attr_name)
            # 跳过方法和内部属性
            if not callable(attr_value) and not attr_name.startswith("_"):
                print(f"{attr_name}: {attr_value}")
    print("=" * 50)


if __name__ == "__main__":
    sys.exit(main())
