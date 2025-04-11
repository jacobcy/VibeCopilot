"""
路线图导入命令处理程序

处理从YAML文件导入路线图的命令逻辑。
"""

import os
from typing import Any, Dict, Optional

from rich.console import Console

console = Console()


def handle_import_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图导入命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    source_path = args.get("source")
    roadmap_id = args.get("roadmap_id")
    fix = args.get("fix", False)
    activate = args.get("activate", False)

    if not source_path:
        return {"status": "error", "message": "必须提供源文件路径"}

    if not os.path.exists(source_path):
        return {"status": "error", "message": f"源文件不存在: {source_path}"}

    # 执行导入操作
    try:
        # 导入前先验证文件格式
        validate_result = service.validate_roadmap_file(source_path, fix)

        if not validate_result.get("success", False):
            return {"status": "error", "message": f"YAML文件格式无效: {validate_result.get('error', '未知错误')}"}

        # 导入路线图
        import_result = service.import_roadmap(source_path, roadmap_id, fix)

        if import_result.get("success", False):
            # 获取导入的路线图ID
            imported_id = import_result.get("roadmap_id")

            # 如果需要激活导入的路线图
            if activate and imported_id:
                service.switch_roadmap(imported_id)

            return {"status": "success", "message": f"路线图已成功导入，ID: {imported_id}", "data": {"roadmap_id": imported_id, "is_active": activate}}
        else:
            return {"status": "error", "message": import_result.get("error", "导入路线图失败")}

    except Exception as e:
        return {"status": "error", "message": f"导入过程中发生错误: {str(e)}"}
