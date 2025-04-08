"""
模板命令执行模块

提供执行模板命令的具体逻辑。
"""

import logging
from typing import Any, Dict, Optional

from rich.console import Console
from rich.table import Table

from src.cli.commands.template.core.advanced_executor import TemplateAdvancedExecutor
from src.templates.core.template_manager import TemplateManager

logger = logging.getLogger(__name__)
console = Console()


class TemplateCommandExecutor:
    """模板命令执行器"""

    def __init__(self, manager: TemplateManager):
        """
        初始化模板命令执行器

        Args:
            manager: 模板管理器实例
        """
        self.manager = manager
        self.advanced_executor = TemplateAdvancedExecutor(manager)

    def execute_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行模板命令

        Args:
            args: 命令参数字典

        Returns:
            执行结果
        """
        # 获取操作类型
        template_action = args.get("template_action")

        # 根据操作类型执行相应命令
        if template_action == "list":
            return self._list_templates(args)
        elif template_action == "show":
            return self._show_template(args)
        elif template_action == "import":
            return self.advanced_executor.import_template(args)
        elif template_action == "create":
            return self._create_template(args)
        elif template_action == "update":
            return self._update_template(args)
        elif template_action == "delete":
            return self._delete_template(args)
        elif template_action == "generate":
            return self.advanced_executor.generate_template(args)
        elif template_action == "load":
            return self.advanced_executor.load_templates(args)
        elif template_action == "export":
            return self.advanced_executor.export_template(args)
        elif template_action == "init":
            return self.advanced_executor.init_templates(args)
        else:
            logger.error(f"未知的模板操作: {template_action}")
            return {"success": False, "error": f"未知的模板操作: {template_action}"}

    def _list_templates(self, args: Dict) -> Dict[str, Any]:
        """列出模板"""
        template_type = args.get("template_type")
        verbose = args.get("verbose", False)

        try:
            # 获取模板列表
            if template_type:
                templates = self.manager.get_templates_by_type(template_type)
            else:
                templates = self.manager.get_all_templates()

            # 格式化输出
            result = {"success": True, "message": f"找到 {len(templates)} 个模板", "data": templates}

            if verbose:
                # 详细信息
                table = Table(title="模板列表")
                table.add_column("ID", style="cyan")
                table.add_column("名称", style="green")
                table.add_column("类型", style="blue")
                table.add_column("描述")

                for t in templates:
                    desc = t.description[:50] + "..." if len(t.description) > 50 else t.description
                    table.add_row(t.id, t.name, t.type, desc)

                console.print(table)
                result["table"] = True  # 标记已经输出表格

            return result
        except Exception as e:
            logger.exception("列出模板失败")
            return {"success": False, "error": f"列出模板失败: {str(e)}"}

    def _show_template(self, args: Dict) -> Dict[str, Any]:
        """显示模板详情"""
        template_id = args.get("id")
        format_type = args.get("format", "text")

        if not template_id:
            return {"success": False, "error": "未提供模板ID"}

        try:
            # 获取模板
            template = self.manager.get_template(template_id)
            if not template:
                return {"success": False, "error": f"模板 {template_id} 不存在"}

            # 格式化输出
            if format_type == "json":
                return {"success": True, "data": template.dict()}
            else:
                result = {"success": True, "data": template}

                # 详细文本输出
                console.print(f"[bold cyan]ID:[/bold cyan] {template.id}")
                console.print(f"[bold green]名称:[/bold green] {template.name}")
                console.print(f"[bold blue]类型:[/bold blue] {template.type}")
                console.print(f"[bold]描述:[/bold] {template.description}")

                if hasattr(template, "metadata") and template.metadata:
                    console.print("[bold]元数据:[/bold]")
                    console.print(f"  作者: {template.metadata.author}")
                    console.print(f"  版本: {template.metadata.version}")
                    if template.metadata.tags:
                        console.print(f"  标签: {', '.join(template.metadata.tags)}")

                if hasattr(template, "variables") and template.variables:
                    console.print("[bold]变量:[/bold]")
                    for var in template.variables:
                        required_mark = "*" if getattr(var, "required", True) else ""
                        default_val = f" (默认值: {var.default})" if hasattr(var, "default") and var.default is not None else ""
                        console.print(f"  {var.name}{required_mark}: {var.type}{default_val}")
                        if hasattr(var, "description") and var.description:
                            console.print(f"    {var.description}")

                console.print("[bold]内容:[/bold]")
                content_preview = template.content[:500] + "..." if len(template.content) > 500 else template.content
                console.print(content_preview)

                result["formatted"] = True  # 标记已经格式化输出
                return result

        except Exception as e:
            logger.exception("显示模板详情失败")
            return {"success": False, "error": f"显示模板详情失败: {str(e)}"}

    def _create_template(self, args: Dict) -> Dict[str, Any]:
        """创建模板"""
        name = args.get("name")
        template_type = args.get("template_type")
        description = args.get("description", "")

        if not name or not template_type:
            return {"success": False, "error": "模板名称和类型是必需的"}

        try:
            # 创建模板对象
            from src.models.template import Template, TemplateMetadata

            template = Template(
                id=None,  # 自动生成
                name=name,
                type=template_type,
                description=description,
                content="",  # 内容可以后续更新
                metadata=TemplateMetadata(author="命令行创建", version="1.0.0", tags=[template_type]),
            )

            # 添加模板
            created_template = self.manager.add_template(template)
            return {"success": True, "message": f"成功创建模板: {created_template.id}", "data": created_template}
        except Exception as e:
            logger.exception("创建模板失败")
            return {"success": False, "error": f"创建模板失败: {str(e)}"}

    def _update_template(self, args: Dict) -> Dict[str, Any]:
        """更新模板"""
        template_id = args.get("id")
        name = args.get("name")

        if not template_id:
            return {"success": False, "error": "未提供模板ID"}

        if not name:
            return {"success": False, "error": "未提供任何要更新的内容"}

        try:
            # 检查模板是否存在
            template = self.manager.get_template(template_id)
            if not template:
                return {"success": False, "error": f"模板 {template_id} 不存在"}

            # 更新模板名称
            update_data = {"name": name}
            updated = self.manager.update_template(template_id, update_data)

            return {"success": True, "message": f"成功更新模板: {template_id}", "data": updated}
        except Exception as e:
            logger.exception("更新模板失败")
            return {"success": False, "error": f"更新模板失败: {str(e)}"}

    def _delete_template(self, args: Dict) -> Dict[str, Any]:
        """删除模板"""
        template_id = args.get("id")
        force = args.get("force", False)

        if not template_id:
            return {"success": False, "error": "未提供模板ID"}

        try:
            # 检查模板是否存在
            template = self.manager.get_template(template_id)
            if not template:
                return {"success": False, "error": f"模板 {template_id} 不存在"}

            # 如果没有强制选项，询问确认
            if not force:
                return {"success": True, "message": f"请使用 --force 选项确认删除模板 {template_id}", "data": template}

            # 删除模板
            success = self.manager.delete_template(template_id)
            if not success:
                return {"success": False, "error": f"删除模板失败: {template_id}"}

            return {"success": True, "message": f"成功删除模板: {template_id}"}
        except Exception as e:
            logger.exception("删除模板失败")
            return {"success": False, "error": f"删除模板失败: {str(e)}"}
