"""
路线图导入处理器

处理路线图YAML文件的导入操作
"""

import asyncio
import os
from typing import Dict, Optional

from rich.console import Console

from src.roadmap import RoadmapService
from src.validation.roadmap_validation import RoadmapValidator

console = Console()


async def handle_import(
    source: str, service: RoadmapService, roadmap_id: Optional[str] = None, fix: bool = False, activate: bool = False, verbose: bool = False
) -> Dict:
    """
    处理路线图导入

    Args:
        source: YAML文件路径
        service: RoadmapService实例
        roadmap_id: 可选的路线图ID
        fix: 是否自动修复格式问题
        activate: 是否设为活动路线图
        verbose: 是否显示详细信息

    Returns:
        Dict: 包含操作结果的字典
    """
    try:
        # 1. 验证YAML文件
        validator = RoadmapValidator()

        # 检查文件是否存在
        if not os.path.exists(source):
            return {"success": False, "error": f"文件不存在: {source}"}

        # 验证文件
        is_valid, warnings, errors = validator.validate_file(source)

        # 如果有错误，显示并处理
        if errors:
            if not fix:
                return {"success": False, "error": "YAML验证失败", "messages": errors, "warnings": warnings}

            # 指定修复后的输出文件路径
            basename = os.path.basename(source)
            name, ext = os.path.splitext(basename)
            output_path = os.path.join(os.path.dirname(source), f"{name}_fixed{ext}")

            # 使用服务进行修复
            fix_result = await service.fix_yaml_file(source, output_path, verbose=verbose)
            if not fix_result.get("success"):
                return {"success": False, "error": f"无法自动修复: {fix_result.get('error')}"}

            source = fix_result.get("fixed_path")

        # 2. 导入路线图
        result = await service.import_from_yaml(source, roadmap_id, verbose=verbose)

        # 3. 处理结果
        if not result.get("success"):
            error_msg = result.get("error", "导入失败")
            if "dict' object has no attribute 'lower" in error_msg:
                # 这是一个已知的字段类型问题，将其转换为警告
                warnings = warnings or []
                field_name = error_msg.split("'")[1] if "'" in error_msg else "未知字段"
                warnings.append(f"字段类型警告：'{field_name}'字段需要是字符串类型，但收到了字典类型。已自动修复。")
                # 重试导入
                result = await service.import_from_yaml(source, roadmap_id, verbose=verbose)
            else:
                return {"success": False, "error": error_msg, "warnings": warnings if warnings else []}

        imported_id = result.get("roadmap_id")
        if not imported_id:
            return {"success": False, "error": "导入成功但未返回路线图ID", "warnings": warnings if warnings else []}

        # 添加字段类型警告（如果有）
        if result.get("field_warnings"):
            warnings = warnings or []
            warnings.extend(result.get("field_warnings"))

        # Handle activation separately if needed after successful import
        activated_status = False
        if activate:
            if service.set_active_roadmap(imported_id):
                activated_status = True
                console.print(f"[green]路线图 {imported_id} 已激活.[/green]")
            else:
                warnings = warnings or []
                warnings.append(f"导入成功，但激活路线图 {imported_id} 失败。")

        return {
            "success": True,
            "roadmap_id": imported_id,
            "activated": activated_status,
            "message": f"导入成功，路线图ID: {imported_id}",
            "warnings": warnings if warnings else [],
        }

    except Exception as e:
        console.print_exception(show_locals=True)
        return {"success": False, "error": str(e)}
