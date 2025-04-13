"""
模板导出器

负责将模板导出为不同格式或复制到指定位置。
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.templates.core.exceptions import TemplateExportError
from src.templates.core.template_types import TemplateData


def export_template_to_file(template: Dict[str, Any], output_path: Union[str, Path]) -> Path:
    """将模板导出为文件

    Args:
        template: 模板数据
        output_path: 输出路径

    Returns:
        导出文件的路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        if isinstance(template.get("content"), str):
            f.write(template["content"])
        else:
            f.write(str(template))

    return output_path


def export_template_to_markdown(template: Dict[str, Any], output_path: Union[str, Path]) -> Path:
    """将模板导出为Markdown格式

    Args:
        template: 模板数据
        output_path: 输出路径

    Returns:
        导出文件的路径
    """
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path.with_suffix(".md")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 构建Markdown内容
    md_content = [
        f"# {template.get('name', 'Unnamed Template')}",
        "",
        template.get("description", ""),
        "",
        "## Template Content",
        "```",
        template.get("content", ""),
        "```",
    ]

    if template.get("variables"):
        md_content.extend(
            [
                "",
                "## Variables",
                "",
            ]
        )
        for var in template.get("variables", []):
            md_content.extend(
                [
                    f"- **{var.get('name')}**",
                    f"  - Type: {var.get('type')}",
                    f"  - Description: {var.get('description', '')}",
                    f"  - Required: {var.get('required', True)}",
                    "",
                ]
            )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    return output_path


def batch_export_templates(templates: List[Dict[str, Any]], output_dir: Union[str, Path], format: str = "md") -> List[Path]:
    """批量导出模板

    Args:
        templates: 模板列表
        output_dir: 输出目录
        format: 输出格式，支持 'md' 或 'raw'

    Returns:
        导出文件路径列表
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exported_files = []
    for template in templates:
        name = template.get("name", f"template_{len(exported_files)}")
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip()

        if format.lower() == "md":
            output_path = output_dir / f"{safe_name}.md"
            exported_files.append(export_template_to_markdown(template, output_path))
        else:
            output_path = output_dir / safe_name
            exported_files.append(export_template_to_file(template, output_path))

    return exported_files


class TemplateExporter:
    """模板导出器类

    负责将模板导出为不同格式或复制到指定位置。
    """

    def __init__(self, template_dir: Union[str, Path]):
        """初始化模板导出器

        Args:
            template_dir: 模板根目录
        """
        self.template_dir = Path(template_dir)
        if not self.template_dir.exists():
            raise TemplateExportError(f"模板目录不存在: {template_dir}")

    def export_template(
        self,
        template_name: str,
        export_path: Union[str, Path],
        variables: Optional[Dict] = None,
    ) -> Path:
        """导出模板到指定位置

        Args:
            template_name: 模板名称
            export_path: 导出目标路径
            variables: 模板变量

        Returns:
            导出后的路径

        Raises:
            TemplateExportError: 导出失败时抛出
        """
        template_path = self.template_dir / template_name
        if not template_path.exists():
            raise TemplateExportError(f"模板不存在: {template_name}")

        export_path = Path(export_path)
        try:
            # 如果目标是文件，确保父目录存在
            if export_path.suffix:
                export_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # 如果目标是目录，确保目录存在
                export_path.mkdir(parents=True, exist_ok=True)

            # 复制模板
            if template_path.is_file():
                shutil.copy2(template_path, export_path)
            else:
                shutil.copytree(template_path, export_path, dirs_exist_ok=True)

            # TODO: 如果提供了变量，处理模板变量替换

            return export_path

        except Exception as e:
            raise TemplateExportError(f"导出模板失败: {str(e)}")

    def list_exportable_templates(self) -> List[TemplateData]:
        """列出可导出的模板

        Returns:
            可导出的模板列表
        """
        templates = []
        for item in self.template_dir.glob("**/*"):
            if item.is_file() and not item.name.startswith("."):
                rel_path = item.relative_to(self.template_dir)
                templates.append(
                    TemplateData(
                        name=str(rel_path),
                        path=str(item),
                        type="file" if item.is_file() else "directory",
                    )
                )
        return templates

    def validate_export_path(self, export_path: Union[str, Path]) -> bool:
        """验证导出路径是否有效

        Args:
            export_path: 要验证的导出路径

        Returns:
            路径是否有效
        """
        try:
            export_path = Path(export_path)
            # 检查父目录是否存在或可创建
            if not export_path.parent.exists():
                export_path.parent.mkdir(parents=True, exist_ok=True)
            # 检查是否有写入权限
            return os.access(export_path.parent, os.W_OK)
        except Exception:
            return False
