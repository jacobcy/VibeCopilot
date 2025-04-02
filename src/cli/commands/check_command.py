"""
检查命令处理器
"""

import logging
from typing import Any, Dict

from scripts.github.roadmap.cli import RoadmapCLI
from src.cli.base_command import BaseCommand

logger = logging.getLogger(__name__)


class CheckCommand(BaseCommand):
    """检查命令处理器"""

    def __init__(self):
        super().__init__("check", "检查项目状态")
        self.roadmap_cli = RoadmapCLI()

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行检查命令"""
        try:
            # 检查路线图状态
            roadmap_result = self.roadmap_cli.handle_check_command(None)

            return self.format_response({"roadmap": roadmap_result})
        except Exception as e:
            logger.error(f"处理check命令失败: {e}")
            return {"success": False, "error": f"处理命令失败: {e}"}
