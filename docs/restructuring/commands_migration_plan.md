# 路线图命令迁移计划

## 概述

将 `adapters/roadmap_sync/commands` 中的命令迁移到核心模块 `src/cli/commands` 中，使项目架构更加合理和一致。

## 迁移步骤

### 1. 创建新的命令文件

在 `src/cli/commands` 目录下创建一个新的文件 `roadmap_commands.py`，将在其中实现所有路线图相关命令。

### 2. 修改命令实现

需要进行以下调整：

- 继承 `src.cli.base_command.BaseCommand` 而非原来的 `CommandBase`
- 更新导入路径，使用项目的标准导入结构
- 调整命令参数处理方式，使其符合核心CLI系统的标准
- 确保命令能正确使用核心服务和适配器

### 3. 注册新命令

在 `src/cli/commands/__init__.py` 中注册新命令，使其可被CLI系统发现和使用。

### 4. 更新依赖关系

- 识别并修正不合理的依赖关系
- 确保命令只依赖核心模块和适当的服务层

### 5. 删除原始命令

完成迁移和测试后，删除 `adapters/roadmap_sync/commands` 目录中的原始命令。

## 迁移实施

### 步骤1: 分析原有命令

对 `adapters/roadmap_sync/commands` 中的每个命令进行分析：

- CheckCommand: 检查路线图状态
- UpdateCommand: 更新路线图元素状态
- StoryCommand: 管理故事
- TaskCommand: 管理任务
- PlanCommand: 创建计划
- SyncCommand: 同步路线图数据

### 步骤2: 创建新的命令实现

在 `src/cli/commands/roadmap_commands.py` 中实现相应的命令类：

```python
"""
路线图命令模块

提供路线图、故事、任务等相关命令的实现。
"""

from typing import Any, Dict, List, Optional

from src.cli.base_command import BaseCommand
from src.services.roadmap_service import RoadmapService


class RoadmapCheckCommand(BaseCommand):
    """检查路线图状态命令"""

    def __init__(self):
        """初始化检查路线图命令"""
        super().__init__(name="roadmap-check", description="检查路线图状态")
        self.roadmap_service = RoadmapService()
        # 注册参数
        self.register_args(
            required=[],
            optional={
                "type": "roadmap",  # 检查类型，默认为roadmap
                "id": None,        # 资源ID
                "update": False,    # 是否更新
            },
        )

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行检查命令

        Args:
            args: 命令参数

        Returns:
            Dict[str, Any]: 检查结果
        """
        check_type = args.get("type", "roadmap")
        resource_id = args.get("id")
        update = args.get("update", False)

        result = self.roadmap_service.check_roadmap(
            check_type=check_type,
            resource_id=resource_id,
            update=update
        )

        return {
            "action": "roadmap-check",
            "type": check_type,
            "result": result
        }

    def get_examples(self) -> List[Dict[str, str]]:
        """获取命令示例

        Returns:
            List[Dict[str, str]]: 命令示例列表
        """
        return [
            {"description": "检查整体路线图状态", "command": "/roadmap-check"},
            {"description": "检查特定里程碑状态", "command": "/roadmap-check --type=milestone --id=M2"},
            {"description": "检查任务状态并更新", "command": "/roadmap-check --type=task --id=T2.1 --update=true"},
        ]


class RoadmapUpdateCommand(BaseCommand):
    """更新路线图元素状态命令"""

    def __init__(self):
        """初始化更新命令"""
        super().__init__(name="roadmap-update", description="更新路线图元素状态")
        self.roadmap_service = RoadmapService()
        # 注册参数
        self.register_args(
            required=["id"],
            optional={
                "type": "task",     # 资源类型，默认为task
                "status": None,     # 新状态
                "github": False,    # 是否同步到GitHub
            },
        )

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行更新命令

        Args:
            args: 命令参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        resource_id = args.get("id")
        resource_type = args.get("type", "task")
        status = args.get("status")
        sync_github = args.get("github", False)

        if not resource_id:
            raise ValueError("更新命令需要指定id参数")

        result = self.roadmap_service.update_roadmap_element(
            element_id=resource_id,
            element_type=resource_type,
            status=status,
            sync_github=sync_github
        )

        return {
            "action": "roadmap-update",
            "id": resource_id,
            "type": resource_type,
            "result": result
        }

    def get_examples(self) -> List[Dict[str, str]]:
        """获取命令示例

        Returns:
            List[Dict[str, str]]: 命令示例列表
        """
        return [
            {"description": "更新任务状态", "command": "/roadmap-update --id=T2.1 --status=completed"},
            {"description": "更新里程碑状态并同步到GitHub", "command": "/roadmap-update --id=M2 --type=milestone --status=completed --github=true"},
        ]

# 实现其他命令...
class RoadmapStoryCommand(BaseCommand):
    """故事管理命令"""
    pass

class RoadmapTaskCommand(BaseCommand):
    """任务管理命令"""
    pass

class RoadmapPlanCommand(BaseCommand):
    """计划创建命令"""
    pass

class RoadmapSyncCommand(BaseCommand):
    """同步路线图数据命令"""
    pass
```

### 步骤3: 创建服务层

在 `src/services` 目录下创建 `roadmap_service.py`：

```python
"""
路线图服务模块

提供路线图管理的核心业务逻辑，作为命令与适配器之间的桥梁。
"""

from typing import Any, Dict, List, Optional

from adapters.roadmap_sync.connector import RoadmapConnector
from adapters.github_project.roadmap.generator import RoadmapGenerator
from adapters.github_project.roadmap.processor import RoadmapProcessor


class RoadmapService:
    """路线图服务类，处理路线图相关的核心业务逻辑"""

    def __init__(self):
        """初始化路线图服务"""
        self.roadmap_connector = RoadmapConnector()
        self.roadmap_processor = RoadmapProcessor()

    def check_roadmap(self, check_type: str = "roadmap", resource_id: Optional[str] = None, update: bool = False) -> Dict[str, Any]:
        """检查路线图状态

        Args:
            check_type: 检查类型
            resource_id: 资源ID
            update: 是否更新

        Returns:
            Dict[str, Any]: 检查结果
        """
        # 实现检查逻辑
        roadmap_data = self.roadmap_connector.get_markdown_data()

        # 处理不同类型的检查
        if check_type == "roadmap":
            return self._check_entire_roadmap(roadmap_data, update)
        elif check_type == "milestone":
            return self._check_milestone(roadmap_data, resource_id, update)
        elif check_type == "task":
            return self._check_task(roadmap_data, resource_id, update)
        else:
            raise ValueError(f"不支持的检查类型: {check_type}")

    def update_roadmap_element(self, element_id: str, element_type: str = "task", status: Optional[str] = None, sync_github: bool = False) -> Dict[str, Any]:
        """更新路线图元素状态

        Args:
            element_id: 元素ID
            element_type: 元素类型
            status: 新状态
            sync_github: 是否同步到GitHub

        Returns:
            Dict[str, Any]: 更新结果
        """
        # 实现更新逻辑
        # ...

        # 如果需要同步到GitHub
        if sync_github:
            # 调用GitHub同步功能
            pass

        return {"updated": True, "id": element_id, "type": element_type, "status": status}

    # 实现其他方法...

    def _check_entire_roadmap(self, roadmap_data: Dict[str, Any], update: bool) -> Dict[str, Any]:
        """检查整个路线图状态"""
        # 实现检查逻辑
        return {
            "milestones": len(roadmap_data.get("milestones", [])),
            "tasks": len(roadmap_data.get("tasks", [])),
            # ...其他路线图统计信息
        }

    def _check_milestone(self, roadmap_data: Dict[str, Any], milestone_id: Optional[str], update: bool) -> Dict[str, Any]:
        """检查特定里程碑状态"""
        # 实现检查逻辑
        if not milestone_id:
            raise ValueError("检查里程碑需要指定id参数")

        # ...里程碑检查逻辑
        return {"milestone_id": milestone_id, "checked": True}

    def _check_task(self, roadmap_data: Dict[str, Any], task_id: Optional[str], update: bool) -> Dict[str, Any]:
        """检查特定任务状态"""
        # 实现检查逻辑
        if not task_id:
            raise ValueError("检查任务需要指定id参数")

        # ...任务检查逻辑
        return {"task_id": task_id, "checked": True}
```

### 步骤4: 更新命令注册

修改 `src/cli/commands/__init__.py`：

```python
"""
命令处理模块

所有命令实现需要在此导入，方便统一管理
"""

# 导入所有命令处理器
from src.cli.commands.db import DatabaseCommand
from src.cli.commands.rule_command import RuleCommand
from src.cli.commands.roadmap_commands import (
    RoadmapCheckCommand,
    RoadmapUpdateCommand,
    RoadmapStoryCommand,
    RoadmapTaskCommand,
    RoadmapPlanCommand,
    RoadmapSyncCommand
)

# 暴露所有命令处理器类
__all__ = [
    "DatabaseCommand",
    "RuleCommand",
    "RoadmapCheckCommand",
    "RoadmapUpdateCommand",
    "RoadmapStoryCommand",
    "RoadmapTaskCommand",
    "RoadmapPlanCommand",
    "RoadmapSyncCommand"
]
```

## 后续工作

迁移完成后，需要：

1. 测试所有迁移后的命令，确保功能正常
2. 删除 `adapters/roadmap_sync/commands` 中的原始命令
3. 更新相关文档，反映新的命令结构

## 最终架构

迁移后，命令系统架构将更加清晰：

- `src/cli/commands`: 包含所有用户可用的命令
- `src/services`: 包含核心业务逻辑，作为命令与适配器之间的桥梁
- `adapters`: 包含系统与外部服务的集成代码，不再包含直接的用户命令

这种架构符合依赖规则：高层模块（命令）依赖核心服务，核心服务依赖适配器，而不是反过来。
