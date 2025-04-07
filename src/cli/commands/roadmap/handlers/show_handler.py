"""
Roadmap 'show' subcommand handler.
"""
import logging
from typing import Any, Dict, List, Optional

from rich.console import Console

# Assuming DB imports are needed here as well
from src.db import get_session_factory
from src.db.repositories.roadmap_repository import RoadmapRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository
from src.models.db.roadmap import Roadmap, Story
from src.models.db.task import Task

logger = logging.getLogger(__name__)
console = Console()


def handle_show_roadmap(args: Dict, is_agent_mode: bool = False) -> Dict[str, Any]:
    """处理 show 子命令 (集成 Task)"""
    roadmap_id = args.get("id")
    if not roadmap_id:
        return {"status": "error", "code": 400, "message": "缺少 Roadmap ID", "data": None}
    logger.info(f"显示路线图详情: {roadmap_id}")

    session_factory = get_session_factory()
    with session_factory() as session:
        roadmap_repo = RoadmapRepository(session)
        story_repo = StoryRepository(session)
        task_repo = TaskRepository(session)

        # Use relationship loading (adjust if needed based on actual repo methods)
        # roadmap = roadmap_repo.get_by_id_with_related(roadmap_id) # Assumes a method that loads relations
        roadmap: Optional[Roadmap] = roadmap_repo.get_by_id(roadmap_id)  # Get base roadmap first

        if not roadmap:
            return {
                "status": "error",
                "code": 404,
                "message": f"未找到 Roadmap ID: {roadmap_id}",
                "data": None,
            }

        roadmap_data = roadmap.to_dict()
        roadmap_data["stories"] = []  # Initialize stories list

        # Fetch stories explicitly or rely on relationship (let's fetch explicitly for clarity)
        stories: List[Story] = story_repo.get_by_roadmap(roadmap_id)

        # Prepare data structure for tasks under stories
        story_task_map: Dict[str, List[Dict]] = {}
        story_ids = [s.id for s in stories]

        if story_ids:
            # Fetch all tasks related to these stories in one go (more efficient)
            # Assuming search_tasks can filter by a list of roadmap_item_ids
            tasks_for_roadmap: List[Task] = task_repo.search_tasks(roadmap_item_id=story_ids)

            for task in tasks_for_roadmap:
                # Ensure task.roadmap_item_id is not None before using it as a key
                if task.roadmap_item_id:
                    if task.roadmap_item_id not in story_task_map:
                        story_task_map[task.roadmap_item_id] = []
                    story_task_map[task.roadmap_item_id].append(
                        {
                            "id": task.id,
                            "title": task.title,
                            "status": task.status,
                            "assignee": task.assignee,
                        }
                    )
                else:
                    logger.warning(f"Task {task.id} ('{task.title}') is missing roadmap_item_id link.")

        # Populate roadmap_data with stories and their tasks
        for story in stories:
            story_data = story.to_dict()
            story_data["tasks"] = story_task_map.get(story.id, [])
            roadmap_data["stories"].append(story_data)
            # Add Epic/Milestone info if needed
            story_data["epic_id"] = story.epic_id
            story_data["milestone_id"] = story.milestone_id

        # Console output (if not agent mode)
        if not is_agent_mode:
            console.print(f"[bold cyan]路线图: {roadmap.name}[/bold cyan] (ID: {roadmap.id})")
            console.print(f"状态: {roadmap.status}")
            if roadmap.description:
                console.print(f"描述: {roadmap.description}")
            console.print("--- Stories --- ")
            if not stories:
                console.print("[dim]此路线图下没有用户故事。[/dim]")
            else:
                for story in stories:
                    console.print(f"  [bold blue]Story: {story.title}[/bold blue] (ID: {story.id}, Status: {story.status})")
                    tasks = story_task_map.get(story.id, [])
                    if not tasks:
                        console.print("    [dim]- 无关联任务[/dim]")
                    else:
                        for task_summary in tasks:
                            assignee_str = f" ({task_summary['assignee']})" if task_summary["assignee"] else ""
                            console.print(f"    - [Task {task_summary['id'][:8]}] [{task_summary['status']}] {task_summary['title']}{assignee_str}")
                    console.print("")  # Spacer

        return {
            "status": "success",
            "code": 0,
            "message": f"成功获取路线图 {roadmap_id} 详情",
            "data": roadmap_data,
        }
