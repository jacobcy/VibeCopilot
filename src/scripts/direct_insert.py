#!/usr/bin/env python
"""
直接数据库操作脚本

绕过SQLAlchemy直接使用SQLite3进行数据库操作
"""

import logging
import os
import sqlite3
import sys
import uuid
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        # 获取数据库路径
        home_dir = os.path.expanduser("~")
        db_path = os.path.join(home_dir, ".vibecopilot", "vibecopilot.db")

        logger.info(f"使用数据库: {db_path}")

        # 生成任务ID
        task_id = f"T{uuid.uuid4().hex[:6]}"
        title = "直接插入的测试任务"
        desc = "使用SQLite3直接创建的任务"
        status = "todo"
        priority = "high"
        now = datetime.now().isoformat()

        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 构造插入语句
        insert_sql = """
        INSERT INTO tasks
            (id, title, description, status, priority, milestone, story_id, epic, assignee, estimate, created_at, updated_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # 执行插入
        cursor.execute(
            insert_sql,
            (
                task_id,  # id
                title,  # title
                desc,  # description
                status,  # status
                priority,  # priority
                "",  # milestone
                None,  # story_id
                "",  # epic
                "",  # assignee
                0,  # estimate
                now,  # created_at
                now,  # updated_at
            ),
        )

        # 提交事务
        conn.commit()
        logger.info(f"任务创建成功: {task_id}")

        # 验证插入是否成功
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()

        if task:
            # 获取列名
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [col[1] for col in cursor.fetchall()]

            print("\n创建的任务:")
            print("=" * 80)
            for i, col in enumerate(columns):
                print(f"{col}: {task[i]}")
            print("=" * 80)
        else:
            logger.error("无法读取创建的任务")

        # 关闭连接
        conn.close()

        logger.info("操作完成")
        return 0

    except Exception as e:
        logger.error(f"任务创建失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
