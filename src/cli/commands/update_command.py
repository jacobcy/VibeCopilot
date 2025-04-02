"""
更新命令处理器
"""

import logging
from typing import Any, Dict

from scripts.github.roadmap.cli import RoadmapCLI
from src.cli.base_command import BaseCommand

logger = logging.getLogger(__name__)


class UpdateCommand(BaseCommand):
    """更新命令处理器"""

    def __init__(self):
        super().__init__("update", "更新任务状态")
        self.roadmap_cli = RoadmapCLI()

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """验证参数"""
        if args.get("type") != "task":
            return False
        if not args.get("id"):
            return False
        return True

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行更新命令"""
        if not self.validate_args(args):
            return {"success": False, "error": "参数无效"}

        task_id = args.get("id")
        new_status = args.get("status")

        try:
            # 更新roadmap中的任务
            roadmap_result = self.roadmap_cli.run(
                ["update", "--type", "task", "--id", task_id, "--status", new_status]
            )

            return self.format_response(
                {
                    "task_id": task_id,
                    "new_status": new_status,
                    "roadmap_sync": roadmap_result.get("success", False),
                }
            )
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return {"success": False, "error": f"更新任务失败: {e}"}
