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

# Import necessary modules for config loading
from dotenv import load_dotenv

from src.core.config import config_manager

# Load .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Reuse the helper function from check_db or define it here
def get_database_path_for_script() -> str:
    """获取脚本使用的数据库路径 (环境变量优先，其次配置)"""
    db_path = None
    # 1. 环境变量
    env_db_url = os.environ.get("DATABASE_URL")
    if env_db_url:
        if env_db_url.startswith("sqlite:///"):
            db_path = env_db_url[len("sqlite:///") :]
        else:
            logger.warning(f"DATABASE_URL format not recognized ({env_db_url}), falling back to config.")

    # 2. 配置文件
    if not db_path:
        db_path = config_manager.get("database.path")

    if not db_path:
        raise ValueError("Database path could not be determined from DATABASE_URL or config.")

    # Ensure absolute path
    if not os.path.isabs(db_path):
        logger.warning(f"Database path is relative: {db_path}. Converting to absolute using CWD.")
        db_path = os.path.abspath(db_path)

    return db_path


def main():
    """主函数"""
    try:
        # 获取数据库路径
        db_path = get_database_path_for_script()

        logger.info(f"使用数据库: {db_path}")

        # 生成任务ID
        task_id = str(uuid.uuid4())
        title = "直接插入的测试任务"
        desc = "使用SQLite3直接创建的任务"
        status = "open"  # Match model default?
        priority = "medium"  # Assuming priority is no longer used
        now_iso = datetime.now().isoformat()
        now_dt = datetime.now()  # For timezone aware fields if needed

        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 构造插入语句 - ** IMPORTANT: Match current Task model columns **
        # Check Task model for exact columns (e.g., no priority, added closed_at etc.)
        insert_sql = """
        INSERT INTO tasks
            (id, title, description, status, assignee, labels,
             created_at, updated_at, closed_at,
             roadmap_item_id, workflow_session_id, workflow_stage_instance_id,
             github_issue_number, linked_prs, linked_commits)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # 执行插入 - ** Match column order and types **
        cursor.execute(
            insert_sql,
            (
                task_id,  # id (string)
                title,  # title (string)
                desc,  # description (string or None)
                status,  # status (string)
                None,  # assignee (string or None)
                None,  # labels (JSON string or None, e.g., '[\"test\"]')
                now_dt,  # created_at (datetime)
                now_dt,  # updated_at (datetime)
                None,  # closed_at (datetime or None)
                None,  # roadmap_item_id (string or None)
                None,  # workflow_session_id (string or None)
                None,  # workflow_stage_instance_id (string or None)
                None,  # github_issue_number (integer or None)
                None,  # linked_prs (JSON string or None)
                None,  # linked_commits (JSON string or None)
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

    except ValueError as ve:
        logger.error(f"配置错误: {ve}")
        return 1
    except sqlite3.Error as sql_e:  # Catch specific sqlite errors
        logger.error(f"数据库操作失败: {sql_e}", exc_info=True)
        # Rollback might be needed if conn exists
        if "conn" in locals() and conn:
            try:
                conn.rollback()
                conn.close()
            except Exception as close_e:
                logger.error(f"关闭数据库连接时出错: {close_e}")
        return 1
    except Exception as e:
        logger.error(f"任务创建失败: {e}", exc_info=True)
        if "conn" in locals() and conn:
            try:
                conn.close()
            except Exception as close_e:
                logger.error(f"关闭数据库连接时出错: {close_e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
