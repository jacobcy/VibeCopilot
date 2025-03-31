#!/usr/bin/env python
"""
Obsidian 文档同步工具

该脚本提供简单的命令行界面，用于在Obsidian和项目文档之间同步内容。
可用于单次同步或启动持续监控模式。
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# 添加项目根目录到模块搜索路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入文档引擎
try:
    from scripts.docs.utils.md_utils import batch_fix_documents, fix_document
    from src.docs_engine.docs_engine import create_docs_engine
except ModuleNotFoundError as e:
    print(f"错误: 无法导入模块 - {e}")
    print(f"当前Python路径: {sys.path}")
    print(f"项目根目录: {project_root}")
    print(f"当前工作目录: {os.getcwd()}")
    sys.exit(1)


def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    return logging.getLogger("obsidian_sync")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Obsidian 文档同步工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 同步所有文档
  python scripts/docs/obsidian/sync.py --sync-all

  # 监控文档变更
  python scripts/docs/obsidian/sync.py --watch

  # 验证链接
  python scripts/docs/obsidian/sync.py --validate

  # 修复文档链接
  python scripts/docs/obsidian/sync.py --fix-links

  # 创建新文档
  python scripts/docs/obsidian/sync.py --create-doc "新文档.md" --title "文档标题" --category "分类"
""",
    )

    parser.add_argument("--sync-all", action="store_true", help="同步所有文档")
    parser.add_argument("--sync-file", help="同步单个文件")
    parser.add_argument("--watch", action="store_true", help="监控文档变更")
    parser.add_argument("--validate", action="store_true", help="验证文档链接")
    parser.add_argument("--fix-links", action="store_true", help="修复文档中的链接")
    parser.add_argument("--create-doc", help="创建新文档的路径")
    parser.add_argument("--template", default="default", help="文档模板名称")
    parser.add_argument("--title", help="文档标题")
    parser.add_argument("--description", help="文档描述")
    parser.add_argument("--category", help="文档分类")
    parser.add_argument("--config", help="自定义配置文件路径")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    logger = setup_logging()

    try:
        # 创建文档引擎实例
        engine = create_docs_engine(str(project_root), args.config)
        logger.info("已初始化文档引擎")

        # 处理命令
        if args.sync_all:
            logger.info("开始全量同步文档...")
            stats = engine.sync_all()
            logger.info(f"同步完成: 添加 {stats['added']}，更新 {stats['updated']}，删除 {stats['deleted']}")

        elif args.sync_file:
            logger.info(f"同步文件: {args.sync_file}")
            rel_path = os.path.relpath(args.sync_file, engine.obsidian_dir)
            success = engine.sync_manager.sync_file(rel_path)
            logger.info(f"文件同步{'成功' if success else '失败'}")

        elif args.watch:
            logger.info("开始监控文档变更 (按Ctrl+C停止)...")
            try:
                # 启动文件监控
                if not hasattr(engine, "file_watcher") or not engine.file_watcher.is_running():
                    engine._start_file_watcher()

                # 保持运行直到用户中断
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("停止监控")

        elif args.fix_links:
            logger.info("修复文档链接...")
            # 使用批量修复功能处理所有文档
            count = batch_fix_documents(engine.obsidian_dir, logger)
            logger.info(f"修复完成: 已修复 {count} 个文件")

        elif args.validate:
            logger.info("验证文档链接...")
            broken_links = engine.validate_links()

            if broken_links:
                logger.warning(f"发现 {sum(len(links) for links in broken_links.values())} 个无效链接:")

                for file_path, links in broken_links.items():
                    logger.warning(f"\n文件: {file_path}")
                    for link in links:
                        logger.warning(f"  无效链接: {link['text']} (目标: {link['target']})")
            else:
                logger.info("未发现无效链接")

        elif args.create_doc:
            # 准备变量
            variables = {}
            if args.title:
                variables["title"] = args.title
            if args.description:
                variables["description"] = args.description
            if args.category:
                variables["category"] = args.category

            # 确保文件路径是绝对路径
            doc_path = args.create_doc
            if not os.path.isabs(doc_path):
                doc_path = os.path.join(engine.obsidian_dir, doc_path)

            logger.info(f"创建文档: {doc_path}")
            success = engine.generate_new_document(
                template=args.template, output_path=doc_path, variables=variables
            )

            logger.info(f"文档创建{'成功' if success else '失败'}")

    except Exception as e:
        logger.error(f"错误: {str(e)}")
        return 1
    finally:
        # 确保停止引擎
        if "engine" in locals():
            engine.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
