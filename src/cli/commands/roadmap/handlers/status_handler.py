"""
Roadmap 'status' subcommand handler.
"""
import logging
from typing import Any, Dict, Optional

from rich.console import Console
from rich.table import Table

# Assuming DB imports are needed here as well
from src.db import get_session_factory
from src.db.repositories.roadmap_repository import RoadmapRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository
from src.models.db.roadmap import Roadmap
from src.models.db.story import Story
from src.models.db.task import Task

logger = logging.getLogger(__name__)
console = Console()


def handle_roadmap_status(args: Dict, is_agent_mode: bool = False) -> Dict[str, Any]:
    """处理 status 子命令 (集成 Task 统计)"""
    roadmap_id = args.get("id")
    if not roadmap_id:
        return {"status": "error", "code": 400, "message": "缺少 Roadmap ID", "data": None}
    logger.info(f"获取路线图状态: {roadmap_id}")

    session_factory = get_session_factory()
    with session_factory() as session:
        roadmap_repo = RoadmapRepository(session)
        story_repo = StoryRepository(session)
        task_repo = TaskRepository(session)

        roadmap: Optional[Roadmap] = roadmap_repo.get_by_id(roadmap_id)
        if not roadmap:
            return {
                "status": "error",
                "code": 404,
                "message": f"未找到 Roadmap ID: {roadmap_id}",
                "data": None,
            }

        # Get basic stats (Milestone, Epic, Story) from repo method
        stats = roadmap_repo.get_stats(roadmap_id)  # Uses updated get_stats
        if stats.get("error"):
            return {"status": "error", "code": 404, "message": stats["error"], "data": None}

        # --- Get Task specific stats ---
        total_tasks = 0
        tasks_by_status: Dict[str, int] = {}
        stories = story_repo.get_by_roadmap(roadmap_id)
        story_ids = [s.id for s in stories]

        if story_ids:
            # Assuming search_tasks can filter by a list of roadmap_item_ids
            tasks_for_roadmap = task_repo.search_tasks(roadmap_item_id=story_ids)
            total_tasks = len(tasks_for_roadmap)
            for task in tasks_for_roadmap:
                tasks_by_status[task.status] = tasks_by_status.get(task.status, 0) + 1
        # -------------------------------

        status_data = {
            "roadmap_id": roadmap_id,
            "roadmap_name": roadmap.name,
            "milestone_count": stats.get("milestone_count", 0),
            "epic_count": stats.get("epic_count", 0),
            "story_count": stats.get("story_count", 0),
            "task_count": total_tasks,  # Add task count
            "progress": {
                "milestone_percentage": stats.get("milestone_progress", 0.0),
                "story_percentage": stats.get("story_progress", 0.0),
                # Calculate task progress if needed (e.g., based on 'done'/'closed' status)
                "task_percentage": 0.0,  # Placeholder
                "overall_percentage": stats.get("overall_progress", 0.0),  # Maybe recalculate using tasks?
            },
            "tasks_by_status": tasks_by_status,  # Add detailed task status breakdown
        }

        # Calculate task progress
        completed_task_statuses = ["done", "closed"]  # Define what counts as completed
        completed_tasks_count = sum(tasks_by_status.get(s, 0) for s in completed_task_statuses)
        if total_tasks > 0:
            status_data["progress"]["task_percentage"] = round((completed_tasks_count / total_tasks) * 100, 2)
        # Recalculate overall progress (example: average of story and task progress)
        if total_tasks > 0 or status_data["progress"]["story_percentage"] > 0:
            # Avoid division by zero if no stories and no tasks
            denominator = (1 if status_data["progress"]["story_percentage"] > 0 else 0) + (1 if total_tasks > 0 else 0)
            if denominator > 0:
                status_data["progress"]["overall_percentage"] = round(
                    (status_data["progress"]["story_percentage"] + status_data["progress"]["task_percentage"]) / denominator,
                    2,
                )
            else:
                status_data["progress"]["overall_percentage"] = 0.0
        else:
            status_data["progress"]["overall_percentage"] = 0.0

        # Console output (if not agent mode)
        if not is_agent_mode:
            console.print(f"[bold cyan]路线图状态: {roadmap.name}[/bold cyan] (ID: {roadmap.id})")
            table = Table(show_header=False, box=None)
            table.add_column("Metric", style="bold blue")
            table.add_column("Value")
            table.add_row("Milestones", str(status_data["milestone_count"]))
            table.add_row("Epics", str(status_data["epic_count"]))
            table.add_row("Stories", str(status_data["story_count"]))
            table.add_row("Tasks", str(status_data["task_count"]))
            table.add_row("Story Progress", f"{status_data['progress']['story_percentage']:.1f}%")
            table.add_row("Task Progress", f"{status_data['progress']['task_percentage']:.1f}%")
            table.add_row("Overall Progress", f"{status_data['progress']['overall_percentage']:.1f}%")
            console.print(table)

            if status_data["tasks_by_status"]:
                console.print("--- Tasks by Status --- ")
                status_table = Table(box=None)
                status_table.add_column("Status", style="magenta")
                status_table.add_column("Count", style="dim", justify="right")
                for status, count in sorted(status_data["tasks_by_status"].items()):
                    status_table.add_row(status, str(count))
                console.print(status_table)

        return {
            "status": "success",
            "code": 0,
            "message": f"成功获取路线图 {roadmap_id} 状态",
            "data": status_data,
        }
