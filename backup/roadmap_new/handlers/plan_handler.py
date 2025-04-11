"""
路线图规划命令处理程序

处理互动式路线图规划的命令逻辑。
"""

import os
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def handle_plan_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图规划命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    roadmap_id = args.get("id")
    template = args.get("template")
    from_file = args.get("from_file")
    interactive = args.get("interactive", False)

    # 如果没有指定路线图ID，尝试使用当前活动路线图
    if not roadmap_id:
        roadmap_id = service.active_roadmap_id

    # 检查是否可以找到有效的路线图
    if roadmap_id:
        # 检查路线图是否存在
        roadmap = service.get_roadmap(roadmap_id)
        if not roadmap:
            return {"status": "error", "message": f"找不到路线图: {roadmap_id}"}

    # 如果指定了从文件导入
    if from_file:
        if not os.path.exists(from_file):
            return {"status": "error", "message": f"指定的文件不存在: {from_file}"}

    # 执行规划操作
    try:
        # 如果指定了模板
        if template:
            # 使用模板创建计划
            result = service.create_plan_from_template(roadmap_id, template, interactive)
        # 如果指定了从文件导入
        elif from_file:
            # 从文件导入计划
            result = service.import_plan_from_file(roadmap_id, from_file, interactive)
        # 否则，进入交互式规划
        else:
            # 交互式创建路线图计划
            result = service.create_plan_interactive(roadmap_id)

        if result.get("success", False):
            # 获取创建的计划数据
            plan_data = result.get("data", {})
            plan_id = plan_data.get("plan_id")

            # 提示创建成功信息
            success_message = f"成功创建路线图计划 (ID: {plan_id})"

            # 如果有里程碑和任务信息，也显示出来
            milestone_count = len(plan_data.get("milestones", []))
            task_count = len(plan_data.get("tasks", []))

            if milestone_count > 0 or task_count > 0:
                success_message += f"\n创建了 {milestone_count} 个里程碑和 {task_count} 个任务"

            # 如果没有指定路线图ID但创建了新路线图
            if not roadmap_id and "roadmap_id" in plan_data:
                success_message += f"\n创建了新路线图 (ID: {plan_data['roadmap_id']})"

                # 询问是否设置为活动路线图
                if Confirm.ask("是否将新创建的路线图设为活动路线图?"):
                    service.switch_roadmap(plan_data["roadmap_id"])
                    success_message += "\n已将新路线图设为活动路线图"

            return {"status": "success", "message": success_message, "data": plan_data}
        else:
            return {"status": "error", "message": result.get("error", "创建路线图计划失败")}

    except Exception as e:
        return {"status": "error", "message": f"规划过程中发生错误: {str(e)}"}
