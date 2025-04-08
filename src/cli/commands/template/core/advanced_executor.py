"""
模板高级命令执行模块

提供执行模板生成、导入导出等高级命令的具体逻辑。
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from src.templates.core.template_manager import TemplateManager
from src.templates.generators import RegexTemplateGenerator
from src.workflow.workflow_template import load_templates_from_dir, parse_template_file

logger = logging.getLogger(__name__)
console = Console()


class TemplateAdvancedExecutor:
    """模板高级命令执行器"""

    def __init__(self, manager: TemplateManager):
        """
        初始化模板高级命令执行器

        Args:
            manager: 模板管理器实例
        """
        self.manager = manager

    def import_template(self, args: Dict) -> Dict[str, Any]:
        """导入模板"""
        file_path = args.get("file_path")
        overwrite = args.get("overwrite", False)
        recursive = args.get("recursive", False)

        if not file_path:
            return {"success": False, "error": "未提供文件路径"}

        try:
            path = Path(file_path)

            # 处理目录导入
            if path.is_dir() and recursive:
                templates = self.manager.load_templates_from_directory(str(path), overwrite=overwrite)
                return {"success": True, "message": f"成功导入 {len(templates)} 个模板", "data": templates}

            # 处理单文件导入
            template = self.manager.import_template_from_file(path, overwrite)
            if not template:
                return {"success": False, "error": f"导入模板失败: {file_path}"}

            return {"success": True, "message": f"成功导入模板: {template.id}", "data": template}
        except Exception as e:
            logger.exception("导入模板失败")
            return {"success": False, "error": f"导入模板失败: {str(e)}"}

    def generate_template(self, args: Dict) -> Dict[str, Any]:
        """生成模板内容"""
        template_id = args.get("id")
        output_file = args.get("output")
        variables_str = args.get("variables", "{}")

        if not template_id:
            return {"success": False, "error": "未提供模板ID"}

        if not output_file:
            return {"success": False, "error": "未提供输出文件路径"}

        try:
            # 获取模板
            template = self.manager.get_template(template_id)
            if not template:
                return {"success": False, "error": f"模板 {template_id} 不存在"}

            # 解析变量
            variables = {}
            if variables_str:
                if isinstance(variables_str, str):
                    try:
                        variables = json.loads(variables_str)
                    except json.JSONDecodeError:
                        return {"success": False, "error": "变量JSON格式无效"}
                else:
                    variables = variables_str

            # 选择生成器
            generator = RegexTemplateGenerator()

            # 生成内容
            content = generator.generate(template, variables)

            # 保存到文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            return {"success": True, "message": f"已生成文件: {output_file}", "data": {"file_path": output_file, "content_length": len(content)}}
        except Exception as e:
            logger.exception("生成模板内容失败")
            return {"success": False, "error": f"生成模板内容失败: {str(e)}"}

    def load_templates(self, args: Dict) -> Dict[str, Any]:
        """加载模板"""
        templates_dir = args.get("templates_dir")

        if not templates_dir:
            return {"success": False, "error": "未提供模板目录"}

        try:
            path = Path(templates_dir)
            if not path.exists() or not path.is_dir():
                return {"success": False, "error": f"目录不存在或不是有效目录: {templates_dir}"}

            # 加载模板
            templates = self.manager.load_templates_from_directory(templates_dir)

            return {"success": True, "message": f"成功加载 {len(templates)} 个模板", "data": templates}
        except Exception as e:
            logger.exception("加载模板失败")
            return {"success": False, "error": f"加载模板失败: {str(e)}"}

    def export_template(self, args: Dict) -> Dict[str, Any]:
        """导出模板"""
        template_id = args.get("id")
        output_path = args.get("output")
        format_type = args.get("format", "md")

        if not template_id:
            return {"success": False, "error": "未提供模板ID"}

        try:
            # 获取模板
            template = self.manager.get_template(template_id)
            if not template:
                return {"success": False, "error": f"模板 {template_id} 不存在"}

            # 导出模板
            content = self.manager.export_template(template_id, format_type)

            # 如果提供了输出路径，写入文件
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "message": f"已导出模板到: {output_path}", "data": {"file_path": output_path}}
            else:
                # 否则返回内容
                return {"success": True, "data": {"content": content}}
        except Exception as e:
            logger.exception("导出模板失败")
            return {"success": False, "error": f"导出模板失败: {str(e)}"}

    def init_templates(self, args: Dict) -> Dict[str, Any]:
        """初始化模板库"""
        force = args.get("force", False)
        source = args.get("source")

        try:
            # 确定源目录
            if source:
                source_dir = Path(source)
            else:
                # 使用默认模板目录
                source_dir = Path(__file__).parents[4] / "templates"

            if not source_dir.exists() or not source_dir.is_dir():
                return {"success": False, "error": f"模板源目录不存在: {source_dir}"}

            # 加载模板
            templates = self.manager.load_templates_from_directory(str(source_dir), overwrite=force)

            return {"success": True, "message": f"成功初始化 {len(templates)} 个模板", "data": templates}
        except Exception as e:
            logger.exception("初始化模板库失败")
            return {"success": False, "error": f"初始化模板库失败: {str(e)}"}
