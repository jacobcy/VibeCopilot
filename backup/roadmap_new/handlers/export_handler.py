"""
路线图导出命令处理程序

处理将路线图导出为YAML文件的命令逻辑。
"""

import os
from typing import Any, Dict, Optional

from rich.console import Console

console = Console()


def handle_export_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图导出命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    roadmap_id = args.get("id")
    output_path = args.get("output")
    milestone_id = args.get("milestone")
    template = args.get("template")

    if not output_path:
        return {"status": "error", "message": "必须提供输出文件路径"}

    # 如果没有指定路线图ID，使用当前活动路线图
    if not roadmap_id:
        roadmap_id = service.active_roadmap_id
        if not roadmap_id:
            return {"status": "error", "message": "未指定路线图ID，且未设置活动路线图。请使用--id指定或使用'roadmap switch <roadmap_id>'设置活动路线图。"}

    # 执行导出操作
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 调用路线图服务导出路线图
        result = service.export_roadmap(roadmap_id, output_path, milestone_id, template)

        if result.get("success", False):
            return {"status": "success", "message": f"路线图已成功导出到 {output_path}", "data": {"output_path": output_path}}
        else:
            return {"status": "error", "message": result.get("error", f"导出路线图失败: {roadmap_id}")}

    except Exception as e:
        return {"status": "error", "message": f"导出过程中发生错误: {str(e)}"}
