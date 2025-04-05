#!/usr/bin/env python
"""
Obsidian 文档同步工具

用于在标准Markdown文档和Obsidian知识库之间进行双向同步的简化工具。
使用.env配置文件定义目录路径和同步选项。
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Union, cast

import dotenv

# 添加项目根目录到模块搜索路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
dotenv.load_dotenv(os.path.join(project_root, ".env"))


# 从环境变量获取配置，处理可能包含注释的情况
def get_env(key, default):
    """获取环境变量并去除可能的注释"""
    value = os.getenv(key, default)
    if value and "#" in value:
        value = value.split("#")[0].strip()
    return value


# 配置源文档和Obsidian知识库路径
DOCS_SOURCE_DIR = os.path.join(project_root, get_env("DOCS_SOURCE_DIR", "docs"))
OBSIDIAN_VAULT_DIR = os.path.join(project_root, get_env("OBSIDIAN_VAULT_DIR", ".obsidian/vault"))
AUTO_SYNC = get_env("AUTO_SYNC_DOCS", "false").lower() == "true"
SYNC_INTERVAL = int(get_env("AUTO_SYNC_INTERVAL", "300"))

# 导入转换工具
try:
    from scripts.docs.utils.converter import MDToObsidian, ObsidianToMD
except ImportError:
    print("找不到转换工具模块，请确保converter.py文件存在")
    sys.exit(1)


def setup_logging() -> logging.Logger:
    """配置并返回日志记录器"""
    logging.basicConfig(
        level=getattr(logging, get_env("LOG_LEVEL", "INFO").upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    return logging.getLogger("obsidian_sync")


def ensure_dir_exists(directory: str) -> str:
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def sync_to_obsidian(file: Optional[str] = None, logger: Optional[logging.Logger] = None) -> bool:
    """
    将标准文档同步到Obsidian

    Args:
        file: 可选，指定要同步的单个文件的相对路径
        logger: 可选，日志记录器

    Returns:
        bool: 同步是否成功
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    converter = MDToObsidian()
    ensure_dir_exists(OBSIDIAN_VAULT_DIR)

    if file:
        # 同步单个文件
        source = os.path.join(DOCS_SOURCE_DIR, file)
        target = os.path.join(OBSIDIAN_VAULT_DIR, file)

        if not os.path.exists(source):
            logger.error(f"源文件不存在: {source}")
            return False

        return converter.convert_file(source, target, logger)

    # 同步整个目录
    success_count = 0
    error_count = 0

    for root, _, files in os.walk(DOCS_SOURCE_DIR):
        rel_path = os.path.relpath(root, DOCS_SOURCE_DIR)
        target_dir = (
            os.path.join(OBSIDIAN_VAULT_DIR, rel_path) if rel_path != "." else OBSIDIAN_VAULT_DIR
        )

        ensure_dir_exists(target_dir)

        for filename in files:
            if filename.endswith(".md"):
                source = os.path.join(root, filename)
                target = os.path.join(target_dir, filename)

                try:
                    if converter.convert_file(source, target, logger):
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"转换失败 {source}: {str(e)}")
                    error_count += 1

    logger.info(f"完成: 成功 {success_count} 个文件, 失败 {error_count} 个文件")
    return error_count == 0


def sync_to_docs(file: Optional[str] = None, logger: Optional[logging.Logger] = None) -> bool:
    """
    将Obsidian文档同步回标准文档

    Args:
        file: 可选，指定要同步的单个文件的相对路径
        logger: 可选，日志记录器

    Returns:
        bool: 同步是否成功
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    converter = ObsidianToMD()

    if file:
        # 同步单个文件
        source = os.path.join(OBSIDIAN_VAULT_DIR, file)
        target = os.path.join(DOCS_SOURCE_DIR, file)

        if not os.path.exists(source):
            logger.error(f"源文件不存在: {source}")
            return False

        return converter.convert_file(source, target, logger)

    # 同步整个目录
    success_count = 0
    error_count = 0

    for root, _, files in os.walk(OBSIDIAN_VAULT_DIR):
        rel_path = os.path.relpath(root, OBSIDIAN_VAULT_DIR)
        target_dir = os.path.join(DOCS_SOURCE_DIR, rel_path) if rel_path != "." else DOCS_SOURCE_DIR

        ensure_dir_exists(target_dir)

        for filename in files:
            if filename.endswith(".md"):
                source = os.path.join(root, filename)
                target = os.path.join(target_dir, filename)

                try:
                    if converter.convert_file(source, target, logger):
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"转换失败 {source}: {str(e)}")
                    error_count += 1

    logger.info(f"完成: 成功 {success_count} 个文件, 失败 {error_count} 个文件")
    return error_count == 0


def watch_changes(logger: Optional[logging.Logger] = None) -> None:
    """
    监控文档变化并自动同步

    Args:
        logger: 日志记录器
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        logger.error("未安装watchdog模块，无法监控文件变更。请运行: pip install watchdog")
        return

    class DocsChangeHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if not event.is_directory and str(event.src_path).endswith(".md"):
                rel_path = os.path.relpath(str(event.src_path), DOCS_SOURCE_DIR)
                logger.info(f"检测到文档变更: {rel_path}")
                sync_to_obsidian(rel_path, logger)

    class ObsidianChangeHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if not event.is_directory and str(event.src_path).endswith(".md"):
                rel_path = os.path.relpath(str(event.src_path), OBSIDIAN_VAULT_DIR)
                logger.info(f"检测到Obsidian变更: {rel_path}")
                sync_to_docs(rel_path, logger)

    # 设置观察者
    docs_observer = Observer()
    obsidian_observer = Observer()

    # 添加事件处理器
    docs_observer.schedule(DocsChangeHandler(), DOCS_SOURCE_DIR, recursive=True)
    obsidian_observer.schedule(ObsidianChangeHandler(), OBSIDIAN_VAULT_DIR, recursive=True)

    # 启动观察者
    docs_observer.start()
    obsidian_observer.start()

    try:
        logger.info(f"开始监控文档变更 (间隔: {SYNC_INTERVAL}秒, 按Ctrl+C停止)...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("停止监控")
        docs_observer.stop()
        obsidian_observer.stop()

    docs_observer.join()
    obsidian_observer.join()


def main():
    """主函数"""
    logger = setup_logging()

    # 显示配置信息
    logger.info(f"标准文档目录: {DOCS_SOURCE_DIR}")
    logger.info(f"Obsidian知识库目录: {OBSIDIAN_VAULT_DIR}")
    logger.info("注意: 同步仅在标准Markdown文档和Obsidian知识库之间进行，不涉及Docusaurus生成的网站文件")

    # 确保目录存在
    ensure_dir_exists(DOCS_SOURCE_DIR)
    ensure_dir_exists(OBSIDIAN_VAULT_DIR)

    # 简单的命令行参数处理
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "to-obsidian":
            logger.info("正在将标准文档同步到Obsidian...")
            sync_to_obsidian(logger=logger)

        elif command == "to-docs":
            logger.info("正在将Obsidian文档同步回标准文档...")
            sync_to_docs(logger=logger)

        elif command == "watch":
            if AUTO_SYNC:
                logger.info(f"自动同步已启用，间隔为 {SYNC_INTERVAL} 秒")
            watch_changes(logger)

        else:
            logger.error(f"未知命令: {command}")
            print("\n用法: python sync.py [命令]")
            print("可用命令:")
            print("  to-obsidian  - 将标准Markdown文档同步到Obsidian")
            print("  to-docs      - 将Obsidian文档同步回标准Markdown")
            print("  watch        - 监控文件变化并自动同步")
    else:
        print("\n用法: python sync.py [命令]")
        print("可用命令:")
        print("  to-obsidian  - 将标准Markdown文档同步到Obsidian")
        print("  to-docs      - 将Obsidian文档同步回标准Markdown")
        print("  watch        - 监控文件变化并自动同步")


if __name__ == "__main__":
    main()
