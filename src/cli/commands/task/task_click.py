"""
任务命令模块

处理任务相关的命令，包括创建、查询、更新和删除操作。
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

import click
import yaml
from rich.console import Console

from src.cli.decorators import pass_service
from src.models.db.task import Task
from src.services.task import TaskService

# 导入Click命令
from .core import comment_task, create_task, delete_task, link_task, list_tasks, show, update_task
from .core.comment import comment_task

console = Console()
logger = logging.getLogger(__name__)


class TaskYAMLFormatter:
    """任务YAML格式化器"""

    @staticmethod
    def format_value(value):
        """格式化值

        Args:
            value: 要格式化的值

        Returns:
            格式化后的值
        """
        if value is None:
            return "-"  # 统一使用'-'表示空值
        if isinstance(value, list) and not value:
            return "-"  # 空列表也用'-'表示
        return value

    def to_yaml(self, task: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
        """转换任务为YAML格式

        Args:
            task: 任务数据
            verbose: 是否显示详细信息

        Returns:
            格式化后的任务数据
        """
        # 基础字段
        data = {
            "id": task.get("id"),
            "title": task.get("title"),
            "status": task.get("status"),
            "assignee": self.format_value(task.get("assignee")),
        }

        # 详细信息
        if verbose:
            data.update(
                {
                    "description": self.format_value(task.get("description")),
                    "labels": self.format_value(task.get("labels")),
                    "story_id": self.format_value(task.get("story_id")),
                    "created_at": str(task.get("created_at", "-")),
                    "updated_at": str(task.get("updated_at", "-")),
                }
            )

        return data


def setup_yaml_formatter():
    """设置YAML格式化器"""

    def none_presenter(dumper, _):
        """处理None值"""
        return dumper.represent_scalar("tag:yaml.org,2002:null", "-")

    yaml.add_representer(type(None), none_presenter)


# 初始化YAML格式化器
setup_yaml_formatter()
_formatter = TaskYAMLFormatter()


def format_output(data: Union[Dict, List], format: str = "yaml", verbose: bool = False) -> str:
    """格式化输出数据

    Args:
        data: 要格式化的数据
        format: 输出格式 (yaml/json)
        verbose: 是否显示详细信息

    Returns:
        格式化后的字符串
    """
    if isinstance(data, list):
        formatted_data = [_formatter.to_yaml(item, verbose) for item in data]
    else:
        formatted_data = _formatter.to_yaml(data, verbose)

    if format == "json":
        return json.dumps(formatted_data, indent=2, ensure_ascii=False)
    return yaml.dump(formatted_data, allow_unicode=True, sort_keys=False)


@click.group(help="任务管理命令 (类似 GitHub issue)")
def task():
    """任务管理命令组"""
    pass


# 注册所有Click命令
task.add_command(list_tasks)
task.add_command(create_task)
task.add_command(show)
task.add_command(update_task)
task.add_command(delete_task)
task.add_command(comment_task)
task.add_command(link_task)
