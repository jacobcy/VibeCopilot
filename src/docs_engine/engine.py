"""
文档引擎核心模块

提供统一的文档处理、解析和转换功能，不依赖于特定的文档系统（如Obsidian或Docusaurus）。
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.docs_engine.config_manager import ConfigManager
from src.docs_engine.converters.link_converter import LinkConverter
from src.docs_engine.templates.template_manager import TemplateManager


class DocumentEngine:
    """文档引擎核心类，提供与文档系统无关的文档处理功能"""

    def __init__(self, base_dir: str, config_file: Optional[str] = None):
        """
        初始化文档引擎

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

        # 初始化组件
        self._init_components()

    def _setup_logging(self):
        """配置日志系统"""
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_dir / "docs_engine.log"), logging.StreamHandler()],
        )

        self.logger = logging.getLogger("docs_engine")

    def _init_components(self):
        """初始化各个组件"""
        # 获取配置
        templates_config = self.config["templates"]

        # 初始化目录
        self.templates_dir = Path(templates_config["template_dir"])

        # 确保目录存在
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.link_converter = LinkConverter(str(self.base_dir))
        self.template_manager = TemplateManager(str(self.templates_dir))

    def generate_new_document(
        self, template: str, output_path: str, variables: Dict[str, Any] = None
    ) -> bool:
        """
        使用模板生成新文档

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

        return success

    def convert_links(self, content: str, source_type: str, target_type: str) -> str:
        """
        转换文档中的链接格式

        Args:
            content: 文档内容
            source_type: 源格式（如'obsidian', 'markdown'）
            target_type: 目标格式（如'docusaurus', 'markdown'）

        Returns:
            转换后的内容
        """
        return self.link_converter.convert(content, source_type, target_type)

    def validate_links(self, content: str, base_path: Optional[str] = None) -> List[Dict[str, str]]:
        """
        验证文档中的链接

        Args:
            content: 文档内容
            base_path: 基础路径（用于解析相对链接）

        Returns:
            无效链接列表
        """
        return self.link_converter.validate_links(content, base_path)

    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        从文档中提取元数据

        Args:
            content: 文档内容

        Returns:
            元数据字典
        """
        import re

        import yaml

        # 查找YAML前置内容
        yaml_match = re.match(r"^---\s*(.*?)\s*---", content, re.DOTALL)

        if yaml_match:
            try:
                # 解析YAML
                yaml_content = yaml_match.group(1)
                metadata = yaml.safe_load(yaml_content)
                return metadata if isinstance(metadata, dict) else {}
            except Exception as e:
                self.logger.warning(f"解析元数据失败: {str(e)}")

        return {}

    def add_metadata(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        向文档添加元数据

        Args:
            content: 文档内容
            metadata: 要添加的元数据

        Returns:
            添加了元数据的文档内容
        """
        import re

        import yaml

        # 删除现有的YAML前置内容
        content_without_yaml = re.sub(r"^---\s*.*?\s*---\n?", "", content, flags=re.DOTALL)

        # 生成新的YAML前置内容
        yaml_content = yaml.dump(metadata, allow_unicode=True, sort_keys=False)

        # 添加新的YAML前置内容
        return f"---\n{yaml_content}---\n\n{content_without_yaml.lstrip()}"


def create_document_engine(base_dir: str, config_file: Optional[str] = None) -> DocumentEngine:
    """
    创建文档引擎实例

    Args:
        base_dir: 项目根目录
        config_file: 可选的配置文件路径

    Returns:
        文档引擎实例
    """
    return DocumentEngine(base_dir, config_file)
