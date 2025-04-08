"""
模板命令定义

提供模板相关的命令定义和注册
"""

import argparse
from typing import Any, Dict


def add_template_list_parser(subparsers: Any) -> None:
    """添加模板列表命令解析器"""
    parser = subparsers.add_parser("list", help="列出所有模板", description="列出所有可用的模板")
    parser.add_argument("--type", "-t", help="按类型筛选模板", dest="template_type")
    parser.add_argument("--tags", help="按标签筛选模板", dest="tags", nargs="+")
    parser.add_argument("--format", "-f", choices=["table", "json", "short"], default="table", help="输出格式")
    parser.set_defaults(func="template_list")


def add_template_show_parser(subparsers: Any) -> None:
    """添加模板查看命令解析器"""
    parser = subparsers.add_parser("show", help="查看模板详情", description="显示指定模板的详细信息")
    parser.add_argument("template_id", help="模板ID")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="输出格式")
    parser.set_defaults(func="template_show")


def add_template_import_parser(subparsers: Any) -> None:
    """添加模板导入命令解析器"""
    parser = subparsers.add_parser("import", help="导入模板", description="从文件导入模板")
    parser.add_argument("file_path", help="模板文件路径")
    parser.add_argument("--overwrite", "-o", action="store_true", help="是否覆盖已存在的模板")
    parser.set_defaults(func="template_import")


def add_template_create_parser(subparsers: Any) -> None:
    """添加模板创建命令解析器"""
    parser = subparsers.add_parser("create", help="创建模板", description="创建新模板")
    parser.add_argument("--name", "-n", required=True, help="模板名称")
    parser.add_argument("--type", "-t", choices=["rule", "doc", "flow", "roadmap"], required=True, help="模板类型")
    parser.add_argument("--description", "-d", help="模板描述")
    parser.add_argument("--content", "-c", help="模板内容")
    parser.add_argument("--file", "-f", help="从文件读取模板内容")
    parser.set_defaults(func="template_create")


def add_template_update_parser(subparsers: Any) -> None:
    """添加模板更新命令解析器"""
    parser = subparsers.add_parser("update", help="更新模板", description="更新已存在的模板")
    parser.add_argument("template_id", help="模板ID")
    parser.add_argument("--name", "-n", help="模板名称")
    parser.add_argument("--description", "-d", help="模板描述")
    parser.add_argument("--content", "-c", help="模板内容")
    parser.add_argument("--file", "-f", help="从文件读取模板内容")
    parser.set_defaults(func="template_update")


def add_template_delete_parser(subparsers: Any) -> None:
    """添加模板删除命令解析器"""
    parser = subparsers.add_parser("delete", help="删除模板", description="删除指定模板")
    parser.add_argument("template_id", help="模板ID")
    parser.add_argument("--confirm", "-y", action="store_true", help="确认删除，不提示")
    parser.set_defaults(func="template_delete")


def add_template_generate_parser(subparsers: Any) -> None:
    """添加模板生成命令解析器"""
    parser = subparsers.add_parser("generate", help="生成内容", description="根据模板生成内容")
    parser.add_argument("template_id", help="模板ID")
    parser.add_argument("--vars", "-v", help='变量JSON字符串，格式：\'{"key1": "value1", "key2": "value2"}\'', dest="variables")
    parser.add_argument("--vars-file", help="包含变量的JSON文件路径", dest="variables_file")
    parser.add_argument("--output", "-o", help="输出文件路径，不指定则输出到控制台")
    parser.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown", help="输出格式")
    parser.add_argument("--generator", "-g", choices=["regex", "llm"], default="regex", help="生成器类型，regex为本地正则生成，llm为云端AI生成")
    parser.add_argument("--temperature", "-t", type=float, default=0.7, help="LLM温度参数（仅在使用LLM生成器时有效）")
    parser.set_defaults(func="template_generate")


def add_template_load_parser(subparsers: Any) -> None:
    """添加模板加载命令解析器"""
    parser = subparsers.add_parser("load", help="加载模板", description="从目录加载模板")
    parser.add_argument("--dir", "-d", help="模板目录路径，默认为项目的templates目录", dest="templates_dir")
    parser.add_argument("--overwrite", "-o", action="store_true", help="是否覆盖已存在的模板")
    parser.set_defaults(func="template_load")


def add_template_export_parser(subparsers: Any) -> None:
    """添加模板导出命令解析器"""
    parser = subparsers.add_parser("export", help="导出模板", description="导出模板到文件")
    parser.add_argument("template_id", help="模板ID")
    parser.add_argument("--output", "-o", help="输出文件路径，默认为模板ID.md")
    parser.add_argument("--format", "-f", choices=["md", "json"], default="md", help="输出格式")
    parser.set_defaults(func="template_export")


def register_template_commands(subparsers: Any) -> Dict[str, str]:
    """
    注册模板相关的命令

    Args:
        subparsers: 命令行子解析器

    Returns:
        命令名称到处理函数名称的映射
    """
    template_parser = subparsers.add_parser("template", help="模板管理命令", description="管理和使用模板")
    template_subparsers = template_parser.add_subparsers(dest="template_command", help="模板子命令")
    template_subparsers.required = True

    # 添加子命令
    add_template_list_parser(template_subparsers)
    add_template_show_parser(template_subparsers)
    add_template_import_parser(template_subparsers)
    add_template_create_parser(template_subparsers)
    add_template_update_parser(template_subparsers)
    add_template_delete_parser(template_subparsers)
    add_template_generate_parser(template_subparsers)
    add_template_load_parser(template_subparsers)
    add_template_export_parser(template_subparsers)

    # 返回命令到处理函数的映射
    return {
        "template_list": "handle_template_list",
        "template_show": "handle_template_show",
        "template_import": "handle_template_import",
        "template_create": "handle_template_create",
        "template_update": "handle_template_update",
        "template_delete": "handle_template_delete",
        "template_generate": "handle_template_generate",
        "template_load": "handle_template_load",
        "template_export": "handle_template_export",
    }
