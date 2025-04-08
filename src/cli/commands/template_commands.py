"""
模板命令模块

提供与模板相关的命令处理
"""

import argparse
import json
import logging
from pathlib import Path

from src.db import get_session_factory
from src.templates.core.template_manager import TemplateManager
from src.templates.generators import RegexTemplateGenerator

logger = logging.getLogger(__name__)


def add_template_commands(subparsers):
    """添加模板管理命令"""
    template_parser = subparsers.add_parser("template", help="模板管理命令")
    template_subparsers = template_parser.add_subparsers(dest="template_command", help="模板子命令")

    # 列出模板
    list_parser = template_subparsers.add_parser("list", help="列出所有模板")
    list_parser.add_argument("--type", "-t", help="按类型筛选模板")
    list_parser.set_defaults(func=list_templates)

    # 查看模板
    show_parser = template_subparsers.add_parser("show", help="查看模板详情")
    show_parser.add_argument("template_id", help="模板ID")
    show_parser.set_defaults(func=show_template)

    # 生成模板
    generate_parser = template_subparsers.add_parser("generate", help="生成模板文件")
    generate_parser.add_argument("template_id", help="模板ID")
    generate_parser.add_argument("output_file", help="输出文件路径")
    generate_parser.add_argument("--vars", "-v", dest="variables", help="模板变量JSON字符串")
    generate_parser.set_defaults(func=generate_template)

    # 创建模板
    create_parser = template_subparsers.add_parser("create", help="创建模板")
    create_parser.add_argument("--name", required=True, help="模板名称")
    create_parser.add_argument("--type", required=True, help="模板类型", dest="template_type")
    create_parser.add_argument("--content", help="模板内容")
    create_parser.add_argument("--desc", help="模板描述", dest="description")

    # 更新模板
    update_parser = template_subparsers.add_parser("update", help="更新模板")
    update_parser.add_argument("id", help="模板ID")
    update_parser.add_argument("--name", help="模板名称")
    update_parser.add_argument("--content", help="模板内容")
    update_parser.add_argument("--desc", help="模板描述", dest="description")

    # 删除模板
    delete_parser = template_subparsers.add_parser("delete", help="删除模板")
    delete_parser.add_argument("id", help="模板ID")
    delete_parser.add_argument("--force", action="store_true", help="强制删除，不提示确认")

    # 导入模板
    import_parser = template_subparsers.add_parser("import", help="导入模板")
    import_parser.add_argument("file_path", help="模板文件路径")
    import_parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的模板")
    import_parser.add_argument("--recursive", action="store_true", help="递归导入目录下的所有模板")

    # 导出模板
    export_parser = template_subparsers.add_parser("export", help="导出模板")
    export_parser.add_argument("id", help="模板ID")
    export_parser.add_argument("--output", help="输出文件路径")
    export_parser.add_argument("--format", choices=["md", "json"], default="md", help="输出格式")

    # 初始化模板库
    init_parser = template_subparsers.add_parser("init", help="初始化模板库")
    init_parser.add_argument("--force", action="store_true", help="强制执行，覆盖已有数据")
    init_parser.add_argument("--source", help="指定模板源目录")


def handle_template_command(args):
    """处理模板命令"""
    from src.templates.commands.template.main import execute_template_command

    # 将命名空间转换为dict以便传递
    args_dict = vars(args)

    # 子命令名称转换
    if hasattr(args, "template_command"):
        args_dict["subcommand"] = args.template_command

    # 执行模板命令
    execute_template_command(argparse.Namespace(**args_dict))


def generate_template(args):
    """
    生成模板文件
    """
    template_id = args.template_id
    output_file = args.output_file

    # 获取变量
    variables = {}
    if hasattr(args, "variables") and args.variables:
        try:
            # 确保变量是有效的JSON字符串
            if isinstance(args.variables, str):
                variables = json.loads(args.variables)
            else:
                variables = args.variables

            logger.debug(f"模板变量: {json.dumps(variables, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            logger.error(f"变量JSON格式不正确: {str(e)}")
            print(f"错误: 变量JSON格式不正确 - {str(e)}")
            return

    # 获取模板
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 获取模板
        template = template_manager.get_template(template_id)
        if not template:
            print(f"错误: 模板 {template_id} 不存在")
            return

        # 选择生成器
        generator = RegexTemplateGenerator()

        # 生成内容
        try:
            content = generator.generate(template, variables)

            # 保存到文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"已生成文件: {output_file}")
        except Exception as e:
            logger.exception(f"生成内容失败: {str(e)}")
            print(f"生成内容错误: {str(e)}")

    except Exception as e:
        logger.exception("生成模板失败")
        print(f"错误: {str(e)}")
    finally:
        session.close()


def list_templates(args):
    """
    列出模板
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 获取模板列表
        if hasattr(args, "type") and args.type:
            templates = template_manager.get_templates_by_type(args.type)
        else:
            templates = template_manager.get_all_templates()

        # 打印模板列表
        if not templates:
            print("没有找到模板")
            return

        print(f"找到 {len(templates)} 个模板:")
        for template in templates:
            print(f"ID: {template.id}")
            print(f"名称: {template.name}")
            print(f"类型: {template.type}")
            print(f"描述: {template.description[:50]}..." if len(template.description) > 50 else f"描述: {template.description}")
            print("-" * 30)

    except Exception as e:
        logger.exception("列出模板失败")
        print(f"错误: {str(e)}")
    finally:
        session.close()


def show_template(args):
    """
    显示模板详情
    """
    template_id = args.template_id

    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 获取模板
        template = template_manager.get_template(template_id)
        if not template:
            print(f"错误: 模板 {template_id} 不存在")
            return

        # 打印模板详情
        print(f"ID: {template.id}")
        print(f"名称: {template.name}")
        print(f"类型: {template.type}")
        print(f"描述: {template.description}")

        if hasattr(template, "metadata") and template.metadata:
            print("\n元数据:")
            print(f"作者: {template.metadata.author}")
            print(f"版本: {template.metadata.version}")
            if template.metadata.tags:
                print(f"标签: {', '.join(template.metadata.tags)}")

        if hasattr(template, "variables") and template.variables:
            print("\n变量:")
            for var in template.variables:
                required_mark = "*" if getattr(var, "required", True) else ""
                default_value = f" (默认值: {var.default})" if hasattr(var, "default") and var.default is not None else ""
                print(f"  {var.name}{required_mark}: {var.description}{default_value}")

        print("\n内容:")
        print("-" * 40)
        if len(template.content) > 1000:
            print(template.content[:1000] + "...\n[内容过长，已截断]")
        else:
            print(template.content)
        print("-" * 40)

    except Exception as e:
        logger.exception("显示模板详情失败")
        print(f"错误: {str(e)}")
    finally:
        session.close()
