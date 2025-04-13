"""
模板导出服务模块

负责管理模板导出的业务逻辑，协调数据库和文件导出操作
"""

import logging
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from src.db import TemplateRepository, TemplateVariableRepository
from src.templates.exporters.template_exporter import batch_export_templates, export_template_to_file

logger = logging.getLogger(__name__)


class TemplateExportService:
    """模板导出服务"""

    def __init__(
        self,
        session: Session,
        template_repo: TemplateRepository,
        variable_repo: TemplateVariableRepository,
    ):
        """
        初始化模板导出服务

        Args:
            session: 数据库会话
            template_repo: 模板仓库
            variable_repo: 模板变量仓库
        """
        self.session = session
        self.template_repo = template_repo
        self.variable_repo = variable_repo

    def export_template(self, template_id: str, output_path: str, format: str = "markdown") -> Optional[str]:
        """
        导出单个模板到文件

        Args:
            template_id: 模板ID
            output_path: 输出文件路径
            format: 输出格式，支持markdown和json

        Returns:
            导出的文件路径，失败则返回None
        """
        try:
            # 获取模板
            template = self.template_repo.get_template_by_id(template_id)
            if not template:
                logger.error(f"模板不存在: {template_id}")
                return None

            # 导出模板
            return export_template_to_file(template, output_path, format)

        except Exception as e:
            logger.error(f"导出模板失败: {str(e)}")
            return None

    def export_templates_by_type(self, template_type: str, output_dir: str, format: str = "markdown") -> List[str]:
        """
        按类型导出模板

        Args:
            template_type: 模板类型
            output_dir: 输出目录
            format: 输出格式，支持markdown和json

        Returns:
            导出的文件路径列表
        """
        try:
            # 获取指定类型的模板
            templates = self.template_repo.get_by_type(template_type)

            # 导出模板
            return batch_export_templates(templates, output_dir, format)

        except Exception as e:
            logger.error(f"导出模板失败: {str(e)}")
            return []

    def export_all_templates(self, output_dir: str, format: str = "markdown") -> List[str]:
        """
        导出所有模板

        Args:
            output_dir: 输出目录
            format: 输出格式，支持markdown和json

        Returns:
            导出的文件路径列表
        """
        try:
            # 获取所有模板
            templates = self.template_repo.get_all()

            # 导出模板
            return batch_export_templates(templates, output_dir, format)

        except Exception as e:
            logger.error(f"导出所有模板失败: {str(e)}")
            return []

    def export_templates_by_ids(self, template_ids: List[str], output_dir: str, format: str = "markdown") -> List[str]:
        """
        按ID列表导出模板

        Args:
            template_ids: 模板ID列表
            output_dir: 输出目录
            format: 输出格式，支持markdown和json

        Returns:
            导出的文件路径列表
        """
        exported_files = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for template_id in template_ids:
            try:
                # 构建输出文件路径
                extension = ".md" if format.lower() == "markdown" else ".json"
                output_path = output_dir / f"{template_id}{extension}"

                # 导出单个模板
                exported_file = self.export_template(template_id, str(output_path), format)
                if exported_file:
                    exported_files.append(exported_file)

            except Exception as e:
                logger.error(f"导出模板 {template_id} 失败: {str(e)}")

        return exported_files
