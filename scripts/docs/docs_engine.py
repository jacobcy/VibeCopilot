"""
文档引擎主模块 - 整合所有文档处理功能.

提供统一的接口来管理Obsidian与Docusaurus之间的文档转换与同步.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .config.config_manager import ConfigManager
from .converters.index_generator import IndexGenerator
from .converters.link_converter import LinkConverter
from .sync.docusaurus_sync import DocusaurusSync
from .sync.file_watcher import FileWatcher
from .templates.template_manager import TemplateManager


class DocsEngine:
    """文档引擎核心类，整合所有文档处理功能."""

    def __init__(self, base_dir: str, config_file: Optional[str] = None):
        """
        初始化文档引擎.

        Args:
            base_dir: 项目根目录
            config_file: 可选的配置文件路径
        """
        self.base_dir = Path(base_dir)

        # 配置日志
        self._setup_logging()

        # 初始化配置管理器
        self.config_manager = ConfigManager(base_dir)
        self.config = self.config_manager.get_config()

        # 初始化各个组件
        self._init_components()

        # 自动同步
        if self.config["sync"]["sync_on_startup"]:
            self.sync_all()

    def _setup_logging(self):
        """配置日志系统."""
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_dir / "docs_engine.log"), logging.StreamHandler()],
        )

        self.logger = logging.getLogger("docs_engine")

    def _init_components(self):
        """初始化各个组件."""
        # 获取配置
        obsidian_config = self.config["obsidian"]
        docusaurus_config = self.config["docusaurus"]
        templates_config = self.config["templates"]

        # 初始化目录
        self.obsidian_dir = Path(obsidian_config["vault_dir"])
        self.docusaurus_dir = Path(docusaurus_config["content_dir"])
        self.templates_dir = Path(templates_config["template_dir"])

        # 确保目录存在
        self.obsidian_dir.mkdir(parents=True, exist_ok=True)
        self.docusaurus_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.link_converter = LinkConverter(str(self.obsidian_dir))
        self.index_generator = IndexGenerator(str(self.docusaurus_dir))
        self.sync_manager = DocusaurusSync(
            str(self.obsidian_dir),
            str(self.docusaurus_dir),
            obsidian_config.get("exclude_patterns", []),
        )
        self.template_manager = TemplateManager(str(self.templates_dir))

        # 如果配置了自动同步，启动文件监控
        if self.config["sync"]["watch_for_changes"]:
            self._start_file_watcher()

    def _start_file_watcher(self):
        """启动文件监控."""
        self.file_watcher = FileWatcher(
            str(self.obsidian_dir),
            self._handle_file_change,
            self.config["obsidian"].get("exclude_patterns", []),
        )
        self.file_watcher.start()

    def _handle_file_change(self, rel_path: str, event_type: str):
        """
        处理文件变更.

        Args:
            rel_path: 相对文件路径
            event_type: 事件类型
        """
        self.logger.info(f"检测到文件变更: {rel_path} ({event_type})")

        # 同步变更
        if event_type == "deleted":
            # 删除文件
            dst_path = self.docusaurus_dir / rel_path
            if dst_path.exists():
                dst_path.unlink()
                self.logger.info(f"已删除: {dst_path}")
        else:
            # 添加或更新文件
            self.sync_manager.sync_file(rel_path)

        # 生成受影响目录的索引
        parent_dir = Path(rel_path).parent
        self.index_generator.generate_index_for_directory(self.docusaurus_dir / parent_dir)

    def sync_all(self) -> Dict[str, int]:
        """
        同步所有文档.

        Returns:
            同步统计信息
        """
        self.logger.info("开始全量同步...")

        # 备份
        if self.config["sync"]["backup_before_sync"]:
            self._backup_docusaurus()

        # 执行同步
        stats = self.sync_manager.sync_all()

        self.logger.info(f"同步完成: 添加 {stats['added']}，更新 {stats['updated']}，删除 {stats['deleted']}")

        return stats

    def _backup_docusaurus(self):
        """备份Docusaurus文档目录."""
        import shutil
        from datetime import datetime

        backup_dir = self.base_dir / "backups" / f"docs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            if self.docusaurus_dir.exists():
                shutil.copytree(self.docusaurus_dir, backup_dir)
                self.logger.info(f"已创建备份: {backup_dir}")
        except Exception as e:
            self.logger.error(f"创建备份失败: {str(e)}")

    def generate_new_document(
        self, template: str, output_path: str, variables: Dict[str, Any] = None
    ) -> bool:
        """
        使用模板生成新文档.

        Args:
            template: 模板名称
            output_path: 输出路径
            variables: 变量字典

        Returns:
            是否成功
        """
        # 使用默认模板
        if not template:
            template = self.config["templates"]["default_template"]

        # 生成文档
        success = self.template_manager.create_document(template, output_path, variables)

        if success:
            self.logger.info(f"已创建文档: {output_path}")

            # 自动同步
            if self.config["sync"]["auto_sync"]:
                rel_path = os.path.relpath(output_path, self.obsidian_dir)
                self.sync_manager.sync_file(rel_path)

        return success

    def generate_obsidian_config(self) -> bool:
        """
        生成Obsidian配置.

        Returns:
            是否成功
        """
        return self.config_manager.generate_obsidian_config()

    def generate_docusaurus_sidebar(self) -> Dict[str, Any]:
        """
        生成Docusaurus侧边栏配置.

        Returns:
            侧边栏配置
        """
        return self.config_manager.generate_docusaurus_sidebar()

    def validate_links(self, file_path: Optional[str] = None) -> Dict[str, List]:
        """
        验证文档链接.

        Args:
            file_path: 要验证的文件路径，如果为None则验证所有文件

        Returns:
            无效链接信息
        """
        broken_links = {}

        if file_path:
            # 验证单个文件
            path = Path(file_path)
            if path.exists() and path.is_file():
                content = path.read_text(encoding="utf-8")
                invalid_links = self.link_converter.validate_links(content, str(path))

                if invalid_links:
                    broken_links[str(path)] = invalid_links
        else:
            # 验证所有文件
            for md_file in self.obsidian_dir.glob("**/*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    invalid_links = self.link_converter.validate_links(content, str(md_file))

                    if invalid_links:
                        broken_links[str(md_file)] = invalid_links
                except Exception as e:
                    self.logger.error(f"验证文件链接失败: {md_file} - {str(e)}")

        return broken_links

    def stop(self):
        """停止文档引擎."""
        # 停止文件监控
        if hasattr(self, "file_watcher") and self.file_watcher.is_running():
            self.file_watcher.stop()

        self.logger.info("文档引擎已停止")


# 工厂函数，便于创建实例
def create_docs_engine(base_dir: str, config_file: Optional[str] = None) -> DocsEngine:
    """
    创建文档引擎实例.

    Args:
        base_dir: 项目根目录
        config_file: 可选的配置文件路径

    Returns:
        文档引擎实例
    """
    return DocsEngine(base_dir, config_file)
