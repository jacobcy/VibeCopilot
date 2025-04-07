#!/usr/bin/env python
"""
数据库检查脚本

检查数据库文件状态和结构
"""

import logging
import os
import sqlite3
import sys
from pathlib import Path

# Import necessary modules for config loading
from dotenv import load_dotenv

from src.core.config import config_manager

# Load .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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

    # Ensure absolute path (important for scripts that might run from anywhere)
    if not os.path.isabs(db_path):
        logger.warning(f"Database path is relative: {db_path}. Converting to absolute using CWD.")
        db_path = os.path.abspath(db_path)

    return db_path


def main():
    """主函数"""
    try:
        # 获取数据库路径 (使用新函数)
        db_path = get_database_path_for_script()

        logger.info(f"检查数据库文件: {db_path}")

        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            logger.error(f"数据库文件不存在: {db_path}")
            # Try to initialize it? Or just report error? Report error for check script.
            return 1

        # 检查文件大小
        file_size = os.path.getsize(db_path)
        logger.info(f"数据库文件大小: {file_size} 字节")

        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取表列表
        logger.info("检查数据库表:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        if not tables:
            logger.warning("数据库中没有表")
            conn.close()  # Close connection before returning
            return 0

        # 输出表信息
        for table in tables:
            table_name = table[0]
            logger.info(f"表名: {table_name}")

            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            print(f"\n表 '{table_name}' 结构:")
            print("=" * 80)
            print(f"{'列名':<20} {'类型':<15} {'Null':<10} {'主键':<10} {'默认值':<20}")
            print("-" * 80)

            for col in columns:
                # Correctly unpack the tuple
                _col_id, name, type_, notnull, default_val, pk = col
                print(f"{name:<20} {type_:<15} {'否' if notnull else '是':<10} {'是' if pk else '否':<10} {str(default_val):<20}")

            # 获取行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"\n表 '{table_name}' 包含 {row_count} 行数据")

            # 如果有数据，显示前5行
            if row_count > 0:
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()

                    # 获取列名
                    column_names = [desc[0] for desc in cursor.description]

                    print("\n示例数据:")
                    print(", ".join(column_names))
                    print("-" * 80)

                    for row in rows:
                        # Ensure all elements are strings before joining
                        print(", ".join(str(cell) if cell is not None else "NULL" for cell in row))
                except Exception as select_e:
                    logger.error(f"无法获取表 '{table_name}' 的示例数据: {select_e}")

            print("=" * 80 + "\n")

        # 关闭连接
        conn.close()

        logger.info("数据库检查完成")
        return 0

    except ValueError as ve:
        logger.error(f"配置错误: {ve}")
        return 1
    except Exception as e:
        logger.error(f"检查数据库时出错: {e}", exc_info=True)
        # Ensure connection is closed even on error
        if "conn" in locals() and conn:
            conn.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
