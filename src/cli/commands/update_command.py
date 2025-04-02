"""
更新命令处理模块
"""

import logging
from typing import Any, Dict, List

from src.cli.base_command import BaseCommand

logger = logging.getLogger(__name__)


class UpdateCommand(BaseCommand):
    """更新命令处理器"""

    def __init__(self):
        """初始化更新命令"""
        super().__init__(name="update", description="更新开发状态或任务状态")
        # 注册参数
        self.register_args(
            required=["status"],
            optional={"type": "task", "id": None, "comment": None, "notify": False},
        )

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行更新命令

        Args:
            args: 命令参数
                - status: 要更新的状态
                - type: 更新类型（可选）
                - id: 任务ID（可选）
                - comment: 状态更新说明（可选）
                - notify: 是否通知相关人员（可选）

        Returns:
            Dict[str, Any]: 执行结果
        """
        status = args["status"]
        update_type = args.get("type", "task")  # 默认更新任务状态
        task_id = args.get("id")
        comment = args.get("comment")
        notify = args.get("notify", False)

        # 模拟更新操作
        logger.info(f"更新{update_type} {task_id or '当前任务'} 状态为: {status}")

        # 返回更新结果
        return {
            "type": update_type,
            "id": task_id,
            "status": status,
            "comment": comment,
            "notified": notify,
            "message": f"已更新{update_type}状态为: {status}",
        }

    def get_examples(self) -> List[Dict[str, str]]:
        """获取命令示例

        Returns:
            List[Dict[str, str]]: 命令示例列表
        """
        return [
            {
                "description": "更新任务状态",
                "command": "/update --status=completed --type=task --id=T2.1",
            },
            {
                "description": "更新里程碑状态",
                "command": "/update --status=in_progress --type=milestone --id=M2",
            },
            {
                "description": "更新当前任务状态并添加说明",
                "command": '/update --status=blocked --comment="等待依赖完成"',
            },
            {
                "description": "更新状态并通知团队",
                "command": "/update --status=completed --id=T2.1 --notify",
            },
        ]
