"""
路线图创建命令处理程序

处理创建新路线图的命令逻辑。
"""

from typing import Any, Dict


def handle_create_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图创建命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    name = args.get("name")
    description = args.get("description")

    if not name:
        return {"status": "error", "message": "必须提供路线图名称"}

    # 创建路线图
    result = service.create_roadmap(name, description)

    if result.get("success", False):
        roadmap_id = result.get("roadmap_id")
        return {
            "status": "success",
            "message": f"成功创建路线图 '{name}'，ID: {roadmap_id}",
            "data": {"roadmap_id": roadmap_id, "name": name, "description": description},
        }
    else:
        return {"status": "error", "message": result.get("error", f"创建路线图 '{name}' 失败"), "data": None}
