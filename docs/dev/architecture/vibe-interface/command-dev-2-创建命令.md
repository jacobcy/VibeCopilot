# VibeCopilot 命令系统开发指南 - 创建命令篇

## 4. 创建新命令

### 4.1 命令基类

所有命令处理器都必须继承自`BaseCommand`类：

```python
from typing import Dict, Any

class BaseCommand:
    """命令处理器基类"""

    def __init__(self, name: str, description: str):
        """
        初始化命令处理器

        Args:
            name: 命令名称，与命令字符串匹配
            description: 命令描述，用于帮助信息
        """
        self.name = name
        self.description = description

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """
        验证命令参数

        Args:
            args: 命令参数字典

        Returns:
            bool: 参数是否有效
        """
        return True

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行命令

        Args:
            args: 命令参数字典

        Returns:
            Dict[str, Any]: 执行结果
        """
        if not self.validate_args(args):
            return {"success": False, "error": "参数验证失败"}

        try:
            return self._execute_impl(args)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        命令执行的具体实现（子类必须重写）

        Args:
            args: 命令参数字典

        Returns:
            Dict[str, Any]: 执行结果
        """
        raise NotImplementedError("子类必须实现此方法")
```

### 4.2 实现新命令

创建一个新的命令处理器需要以下步骤：

1. 在`src/cli/commands/`目录下创建新的Python模块
2. 定义一个继承自`BaseCommand`的命令类
3. 实现必要的方法
4. 在命令解析器中注册新命令

#### 示例：实现任务命令

```python
# src/cli/commands/task_command.py
import logging
from typing import Dict, Any

from src.cli.base_command import BaseCommand

class TaskCommand(BaseCommand):
    """任务管理命令处理器"""

    def __init__(self):
        super().__init__("task", "管理项目任务")

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """
        验证任务命令参数

        有效参数组合:
        1. --list: 列出任务
        2. --id=<任务ID> [--status=<状态>] [--assignee=<用户名>]: 更新任务
        """
        # 必须至少有一个参数
        if not args:
            return False

        # 检查必要参数组合
        if "list" in args:
            return True

        if "id" in args:
            return True

        return False

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务命令"""
        # 列出任务
        if "list" in args:
            return self._list_tasks(args)

        # 更新任务
        if "id" in args:
            return self._update_task(args)

        return {"success": False, "error": "无效的参数组合"}

    def _list_tasks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """列出任务"""
        logging.info("列出任务")

        # 这里添加实际列出任务的逻辑
        # ...

        return {
            "success": True,
            "message": "任务列表",
            "data": {
                "tasks": [
                    {"id": "T1.1", "title": "示例任务1", "status": "completed"},
                    {"id": "T2.1", "title": "示例任务2", "status": "in_progress"}
                ]
            }
        }

    def _update_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """更新任务"""
        task_id = args.get("id")
        status = args.get("status")
        assignee = args.get("assignee")

        logging.info(f"更新任务: ID={task_id}, 状态={status}, 负责人={assignee}")

        # 这里添加实际更新任务的逻辑
        # ...

        return {
            "success": True,
            "message": f"任务 {task_id} 已更新",
            "data": {
                "id": task_id,
                "status": status,
                "assignee": assignee
            }
        }
```

### 4.3 注册命令

在命令解析器中注册新命令：

```python
# src/cli/command_parser.py
from src.cli.commands.task_command import TaskCommand

def _register_default_commands(self):
    """注册默认命令处理器"""
    self.register_command(CheckCommand())
    self.register_command(UpdateCommand())
    self.register_command(TaskCommand())  # 注册新命令
    # 注册其他命令...
```
