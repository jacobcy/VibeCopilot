"""
数据库命令模块

提供与数据库相关的命令处理
"""

import argparse
import logging
from pathlib import Path

from src.db import get_session_factory
from src.models.db.init_db import init_db

logger = logging.getLogger(__name__)


def add_db_commands(subparsers):
    """添加数据库管理命令"""
    db_parser = subparsers.add_parser("db", help="数据库管理命令")
    db_subparsers = db_parser.add_subparsers(dest="db_command", help="数据库子命令")

    # 初始化数据库
    init_parser = db_subparsers.add_parser("init", help="初始化数据库")
    init_parser.add_argument("--force", "-f", action="store_true", help="强制重新初始化数据库")
    init_parser.add_argument("--templates", "-t", action="store_true", help="同时导入模板")
    init_parser.set_defaults(func=init_db_command)


def handle_db_command(args):
    """处理数据库相关命令"""
    if args.db_command == "init":
        # 初始化数据库
        templates_only = getattr(args, "templates", False)
        force = getattr(args, "force", False)

        try:
            if templates_only:
                # 只初始化模板
                from src.templates.core.template_loader import load_templates_from_dir

                session_factory = get_session_factory()
                session = session_factory()
                try:
                    # 从默认位置加载模板
                    templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
                    if not templates_dir.exists():
                        logger.error(f"模板目录不存在: {templates_dir}")
                        return 1

                    count = load_templates_from_dir(session, templates_dir, force)
                    logger.info(f"已导入 {count} 个模板")
                finally:
                    session.close()
            else:
                # 初始化全部数据库
                init_db()
                logger.info("数据库初始化完成")

                # 自动导入模板
                session_factory = get_session_factory()
                session = session_factory()
                try:
                    # 从默认位置加载模板
                    templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
                    if templates_dir.exists():
                        from src.templates.core.template_loader import load_templates_from_dir

                        count = load_templates_from_dir(session, templates_dir, force)
                        logger.info(f"已导入 {count} 个模板")
                finally:
                    session.close()

            return 0
        except Exception as e:
            logger.exception("数据库初始化失败")
            logger.error(f"错误: {str(e)}")
            return 1
    else:
        logger.error(f"未知的数据库命令: {args.db_command}")
        return 1


def init_db_command(args):
    """
    初始化数据库
    """
    force = args.force
    templates = args.templates

    try:
        init_db(force=force, init_templates=templates)
        print("数据库初始化成功")
    except Exception as e:
        logger.exception("数据库初始化失败")
        print(f"错误: {str(e)}")
