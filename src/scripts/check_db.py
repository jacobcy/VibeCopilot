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

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        # 获取数据库路径
        home_dir = os.path.expanduser("~")
        default_db_path = os.path.join(home_dir, ".vibecopilot", "vibecopilot.db")

        logger.info(f"检查数据库文件: {default_db_path}")

        # 检查数据库文件是否存在
        if not os.path.exists(default_db_path):
            logger.error(f"数据库文件不存在: {default_db_path}")
            return 1

        # 检查文件大小
        file_size = os.path.getsize(default_db_path)
        logger.info(f"数据库文件大小: {file_size} 字节")

        # 连接数据库
        conn = sqlite3.connect(default_db_path)
        cursor = conn.cursor()

        # 获取表列表
        logger.info("检查数据库表:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        if not tables:
            logger.warning("数据库中没有表")
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
                col_id, name, type_, notnull, default_val, pk = col
                print(
                    f"{name:<20} {type_:<15} {'否' if notnull else '是':<10} {'是' if pk else '否':<10} {str(default_val):<20}"
                )

            # 获取行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"\n表 '{table_name}' 包含 {row_count} 行数据")

            # 如果有数据，显示前5行
            if row_count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                rows = cursor.fetchall()

                # 获取列名
                column_names = [desc[0] for desc in cursor.description]

                print("\n示例数据:")
                print(", ".join(column_names))
                print("-" * 80)

                for row in rows:
                    print(", ".join(str(cell) for cell in row))

            print("=" * 80 + "\n")

        # 关闭连接
        conn.close()

        logger.info("数据库检查完成")
        return 0

    except Exception as e:
        logger.error(f"检查数据库时出错: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
