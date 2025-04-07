#!/usr/bin/env python
"""
创建任务脚本

直接使用Task仓库创建任务
"""

import logging
import sys
import uuid

from src.db import TaskRepository, get_engine, get_session_factory
from src.models.db.roadmap import Task

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        # 创建数据库引擎和会话
        engine = get_engine()
        session_factory = get_session_factory(engine)
        session = session_factory()

        # 创建仓库
        task_repo = TaskRepository(session)

        # 创建任务数据
        task_id = f"T{uuid.uuid4().hex[:6]}"
        task_data = {
            "id": task_id,
            "title": "测试任务创建",
            "description": "直接使用仓库创建任务",
            "status": "todo",
            "priority": "P1",
            "epic": "测试Epic",
        }

        # 创建任务实例
        task = Task(**task_data)

        # 添加到会话并提交
        logger.info(f"正在创建任务: {task_id}")
        session.add(task)
        session.commit()
        logger.info(f"任务创建成功: {task_id}")

        # 从数据库中获取并显示
        saved_task = task_repo.get_by_id(task_id)
        if saved_task:
            for key, value in saved_task.__dict__.items():
                if not key.startswith("_"):
                    print(f"{key}: {value}")

        return 0
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
