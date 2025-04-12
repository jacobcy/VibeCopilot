"""
路线图规划处理器

处理路线图的交互式规划功能。
"""

from typing import Dict, List, Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt

from src.roadmap import RoadmapService

console = Console()


def handle_plan_roadmap(
    service: RoadmapService,
    roadmap_id: Optional[str] = None,
    template: Optional[str] = None,
    from_file: Optional[str] = None,
    interactive: bool = False,
) -> Dict:
    """处理路线图规划"""
    try:
        roadmap = None

        # 1. 确定工作模式和起始点
        if roadmap_id:
            roadmap = service.get_roadmap(roadmap_id)
            if not roadmap:
                return {"success": False, "message": f"未找到路线图: {roadmap_id}"}

        # 2. 如果提供了YAML文件，导入它
        if from_file:
            result = service.import_from_yaml(from_file, roadmap_id) if roadmap_id else service.import_from_yaml(from_file)
            if result.get("success"):
                roadmap_id = result.get("roadmap_id")
                roadmap = service.get_roadmap(roadmap_id)
            else:
                return {"success": False, "message": f"导入失败: {result.get('error', '未知错误')}"}

        # 3. 如果没有现有路线图，创建新的
        if not roadmap:
            title = Prompt.ask("请输入路线图标题")
            description = Prompt.ask("请输入路线图描述", default="")

            result = service.create_roadmap(title=title, description=description)
            if result.get("success"):
                roadmap_id = result.get("roadmap_id")
                roadmap = service.get_roadmap(roadmap_id)
            else:
                return {"success": False, "message": f"创建路线图失败: {result.get('error', '未知错误')}"}

        # 4. 管理里程碑
        if Confirm.ask("是否添加或管理里程碑?", default=True):
            result = handle_manage_milestones(service, roadmap_id)
            if not result.get("success"):
                return result

        # 5. 管理任务
        if Confirm.ask("是否添加或管理任务?", default=True):
            result = handle_manage_tasks(service, roadmap_id)
            if not result.get("success"):
                return result

        # 6. 询问是否设为活动路线图
        if Confirm.ask("是否将此路线图设为活动路线图?", default=True):
            service.set_active_roadmap(roadmap_id)

        return {"success": True, "roadmap_id": roadmap_id, "roadmap": roadmap, "message": "路线图规划完成"}

    except Exception as e:
        return {"success": False, "message": f"规划过程中出错: {str(e)}"}


def handle_manage_milestones(service: RoadmapService, roadmap_id: str) -> Dict:
    """处理里程碑管理"""
    try:
        while True:
            # 显示现有里程碑
            roadmap = service.get_roadmap_details(roadmap_id)
            milestones = roadmap.get("milestones", [])

            console.print("\n[bold]里程碑管理[/bold]")
            if milestones:
                console.print("\n现有里程碑:")
                for i, ms in enumerate(milestones, 1):
                    status_style = "green" if ms.get("status") == "completed" else "yellow" if ms.get("status") == "in_progress" else "white"
                    console.print(f"{i}. [{status_style}]{ms.get('title')}[/{status_style}] ({ms.get('id')})")
            else:
                console.print("[yellow]暂无里程碑[/yellow]")

            # 显示选项
            console.print("\n选项:")
            console.print("1. 添加新里程碑")
            console.print("2. 修改里程碑")
            console.print("3. 删除里程碑")
            console.print("4. 返回上级菜单")

            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4"], default="1")

            if choice == "1":
                result = handle_add_milestone(service, roadmap_id)
            elif choice == "2":
                result = handle_edit_milestone(service, roadmap_id, milestones)
            elif choice == "3":
                result = handle_delete_milestone(service, roadmap_id, milestones)
            else:
                break

            if not result.get("success"):
                return result

        return {"success": True}

    except Exception as e:
        return {"success": False, "message": f"里程碑管理出错: {str(e)}"}


def handle_manage_tasks(service: RoadmapService, roadmap_id: str) -> Dict:
    """处理任务管理"""
    try:
        while True:
            # 显示现有任务
            roadmap = service.get_roadmap_details(roadmap_id)
            tasks = roadmap.get("tasks", [])
            milestones = roadmap.get("milestones", [])

            console.print("\n[bold]任务管理[/bold]")
            if tasks:
                console.print("\n现有任务:")
                for i, task in enumerate(tasks, 1):
                    status_style = "green" if task.get("status") == "completed" else "yellow" if task.get("status") == "in_progress" else "white"
                    console.print(f"{i}. [{status_style}]{task.get('title')}[/{status_style}] ({task.get('id')})")
            else:
                console.print("[yellow]暂无任务[/yellow]")

            # 显示选项
            console.print("\n选项:")
            console.print("1. 添加新任务")
            console.print("2. 修改任务")
            console.print("3. 删除任务")
            console.print("4. 返回上级菜单")

            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4"], default="1")

            if choice == "1":
                result = handle_add_task(service, roadmap_id, milestones)
            elif choice == "2":
                result = handle_edit_task(service, roadmap_id, tasks, milestones)
            elif choice == "3":
                result = handle_delete_task(service, roadmap_id, tasks)
            else:
                break

            if not result.get("success"):
                return result

        return {"success": True}

    except Exception as e:
        return {"success": False, "message": f"任务管理出错: {str(e)}"}


def handle_add_milestone(service: RoadmapService, roadmap_id: str) -> Dict:
    """处理添加里程碑"""
    try:
        title = Prompt.ask("里程碑标题")
        description = Prompt.ask("里程碑描述", default="")
        start_date = Prompt.ask("开始日期 (YYYY-MM-DD)", default="")
        end_date = Prompt.ask("结束日期 (YYYY-MM-DD)", default="")
        status = Prompt.ask("状态", choices=["not_started", "in_progress", "completed"], default="not_started")

        result = service.create_milestone(
            roadmap_id=roadmap_id,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )

        if result.get("success"):
            return {"success": True, "message": f"已添加里程碑: {title}"}
        else:
            return {"success": False, "message": f"添加里程碑失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"添加里程碑出错: {str(e)}"}


def handle_edit_milestone(service: RoadmapService, roadmap_id: str, milestones: List[Dict]) -> Dict:
    """处理编辑里程碑"""
    try:
        if not milestones:
            return {"success": True, "message": "暂无里程碑可修改"}

        idx = Prompt.ask("请选择要修改的里程碑序号", choices=[str(i) for i in range(1, len(milestones) + 1)])
        milestone = milestones[int(idx) - 1]

        title = Prompt.ask("里程碑标题", default=milestone.get("title", ""))
        description = Prompt.ask("里程碑描述", default=milestone.get("description", ""))
        start_date = Prompt.ask("开始日期 (YYYY-MM-DD)", default=milestone.get("start_date", ""))
        end_date = Prompt.ask("结束日期 (YYYY-MM-DD)", default=milestone.get("end_date", ""))
        status = Prompt.ask("状态", choices=["not_started", "in_progress", "completed"], default=milestone.get("status", "not_started"))

        result = service.update_milestone(
            milestone_id=milestone.get("id"),
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )

        if result.get("success"):
            return {"success": True, "message": f"已更新里程碑: {title}"}
        else:
            return {"success": False, "message": f"更新里程碑失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"编辑里程碑出错: {str(e)}"}


def handle_delete_milestone(service: RoadmapService, roadmap_id: str, milestones: List[Dict]) -> Dict:
    """处理删除里程碑"""
    try:
        if not milestones:
            return {"success": True, "message": "暂无里程碑可删除"}

        idx = Prompt.ask("请选择要删除的里程碑序号", choices=[str(i) for i in range(1, len(milestones) + 1)])
        milestone = milestones[int(idx) - 1]

        if Confirm.ask(f"确定要删除里程碑 '{milestone.get('title')}' 吗?"):
            result = service.delete_milestone(milestone.get("id"))

            if result.get("success"):
                return {"success": True, "message": f"已删除里程碑: {milestone.get('title')}"}
            else:
                return {"success": False, "message": f"删除里程碑失败: {result.get('error', '未知错误')}"}
        else:
            return {"success": True, "message": "已取消删除"}

    except Exception as e:
        return {"success": False, "message": f"删除里程碑出错: {str(e)}"}


def handle_add_task(service: RoadmapService, roadmap_id: str, milestones: List[Dict]) -> Dict:
    """处理添加任务"""
    try:
        title = Prompt.ask("任务标题")
        description = Prompt.ask("任务描述", default="")

        # 选择里程碑
        milestone_id = None
        if milestones:
            console.print("\n选择关联的里程碑:")
            for i, ms in enumerate(milestones, 1):
                console.print(f"{i}. {ms.get('title')} ({ms.get('id')})")

            idx = Prompt.ask("请选择里程碑序号 (0表示不关联)", choices=[str(i) for i in range(0, len(milestones) + 1)])
            if idx != "0":
                milestone_id = milestones[int(idx) - 1].get("id")

        status = Prompt.ask("状态", choices=["not_started", "in_progress", "completed"], default="not_started")
        priority = Prompt.ask("优先级", choices=["low", "medium", "high"], default="medium")
        assignee = Prompt.ask("负责人", default="")

        result = service.create_task(
            roadmap_id=roadmap_id,
            title=title,
            description=description,
            milestone_id=milestone_id,
            status=status,
            priority=priority,
            assignee=assignee,
        )

        if result.get("success"):
            return {"success": True, "message": f"已添加任务: {title}"}
        else:
            return {"success": False, "message": f"添加任务失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"添加任务出错: {str(e)}"}


def handle_edit_task(service: RoadmapService, roadmap_id: str, tasks: List[Dict], milestones: List[Dict]) -> Dict:
    """处理编辑任务"""
    try:
        if not tasks:
            return {"success": True, "message": "暂无任务可修改"}

        idx = Prompt.ask("请选择要修改的任务序号", choices=[str(i) for i in range(1, len(tasks) + 1)])
        task = tasks[int(idx) - 1]

        title = Prompt.ask("任务标题", default=task.get("title", ""))
        description = Prompt.ask("任务描述", default=task.get("description", ""))

        # 选择里程碑
        milestone_id = task.get("milestone_id")
        if milestones:
            console.print("\n选择关联的里程碑:")
            for i, ms in enumerate(milestones, 1):
                console.print(f"{i}. {ms.get('title')} ({ms.get('id')})")

            current_milestone_idx = next((i for i, ms in enumerate(milestones, 1) if ms.get("id") == milestone_id), 0)
            idx = Prompt.ask("请选择里程碑序号 (0表示不关联)", choices=[str(i) for i in range(0, len(milestones) + 1)], default=str(current_milestone_idx))
            milestone_id = milestones[int(idx) - 1].get("id") if idx != "0" else None

        status = Prompt.ask("状态", choices=["not_started", "in_progress", "completed"], default=task.get("status", "not_started"))
        priority = Prompt.ask("优先级", choices=["low", "medium", "high"], default=task.get("priority", "medium"))
        assignee = Prompt.ask("负责人", default=task.get("assignee", ""))

        result = service.update_task(
            task_id=task.get("id"),
            title=title,
            description=description,
            milestone_id=milestone_id,
            status=status,
            priority=priority,
            assignee=assignee,
        )

        if result.get("success"):
            return {"success": True, "message": f"已更新任务: {title}"}
        else:
            return {"success": False, "message": f"更新任务失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"编辑任务出错: {str(e)}"}


def handle_delete_task(service: RoadmapService, roadmap_id: str, tasks: List[Dict]) -> Dict:
    """处理删除任务"""
    try:
        if not tasks:
            return {"success": True, "message": "暂无任务可删除"}

        idx = Prompt.ask("请选择要删除的任务序号", choices=[str(i) for i in range(1, len(tasks) + 1)])
        task = tasks[int(idx) - 1]

        if Confirm.ask(f"确定要删除任务 '{task.get('title')}' 吗?"):
            result = service.delete_task(task.get("id"))

            if result.get("success"):
                return {"success": True, "message": f"已删除任务: {task.get('title')}"}
            else:
                return {"success": False, "message": f"删除任务失败: {result.get('error', '未知错误')}"}
        else:
            return {"success": True, "message": "已取消删除"}

    except Exception as e:
        return {"success": False, "message": f"删除任务出错: {str(e)}"}
