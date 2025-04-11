"""
路线图验证命令处理程序

处理验证路线图YAML文件格式的命令逻辑。
"""

import os
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.syntax import Syntax

console = Console()


def handle_validate_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图验证命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    source_path = args.get("source")
    fix = args.get("fix", False)
    output_path = args.get("output")
    template_path = args.get("template")
    verbose = args.get("verbose", False)

    if not source_path:
        return {"status": "error", "message": "必须提供要验证的YAML文件路径"}

    if not os.path.exists(source_path):
        return {"status": "error", "message": f"源文件不存在: {source_path}"}

    # 如果指定了模板，检查模板是否存在
    if template_path and not os.path.exists(template_path):
        return {"status": "error", "message": f"模板文件不存在: {template_path}"}

    # 如果需要自动修复并输出到新文件，但没有指定输出路径
    if fix and not output_path:
        output_path = source_path

    # 执行验证操作
    try:
        # 调用路线图服务验证YAML文件
        validate_result = service.validate_roadmap_file(source_path, fix, output_path, template_path)

        if not validate_result.get("success", False):
            issues = validate_result.get("issues", [])
            error_message = validate_result.get("error", "未知错误")

            # 显示格式化的错误信息
            msg = f"YAML文件格式无效: {error_message}"
            if issues:
                msg += "\n\n验证问题:"
                for issue in issues:
                    msg += f"\n- {issue}"

            return {"status": "error", "message": msg, "data": {"issues": issues, "error": error_message}}

        # 验证成功
        fixed = validate_result.get("fixed", False)
        warnings = validate_result.get("warnings", [])
        output_file = validate_result.get("output_file")

        # 构建成功消息
        success_msg = "YAML文件格式有效"
        if fixed:
            success_msg += f"，已自动修复并保存到 {output_file}"

        # 如果有警告，显示警告信息
        if warnings:
            warning_msg = "\n\n警告:"
            for warning in warnings:
                warning_msg += f"\n- {warning}"
            success_msg += warning_msg

        # 如果需要详细输出
        if verbose:
            schema_info = validate_result.get("schema_info", {})
            if schema_info:
                schema_msg = "\n\n架构信息:"
                for key, value in schema_info.items():
                    schema_msg += f"\n- {key}: {value}"
                success_msg += schema_msg

        return {"status": "success", "message": success_msg, "data": {"fixed": fixed, "warnings": warnings, "output_file": output_file}}

    except Exception as e:
        return {"status": "error", "message": f"验证过程中发生错误: {str(e)}"}
