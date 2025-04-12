# 工作流系统重构执行计划

## 1. 代码清理任务

### 1.1 删除冗余代码

首先，我们需要删除重复的执行代码，特别是以下文件中的重复函数：

#### 1.1.1 移除 `src/workflow/execution/workflow_execution.py` 中的 `execute_workflow` 函数

```python
# src/workflow/execution/workflow_execution.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行模块

提供工作流的执行记录功能，实际执行委托给flow_session模块。
"""

import logging
from typing import Any, Dict, List, Optional

from src.workflow.workflow_operations import get_workflow_by_id
from src.workflow.execution.execution_operations import save_execution as save_execution_to_storage


def get_executions_for_workflow(workflow_id: str) -> List[Dict[str, Any]]:
    """
    Get execution history for a workflow.

    Args:
        workflow_id (str): The ID of the workflow.

    Returns:
        List[Dict[str, Any]]: List of execution records.
    """
    # Import here to avoid circular imports
    from src.workflow.analytics.workflow_analytics import get_workflow_executions

    # This is essentially the same as get_workflow_executions but with a clearer name
    return get_workflow_executions(workflow_id)


def save_execution(execution_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save workflow execution data to persistent storage.

    Args:
        execution_data: Dictionary containing execution results

    Returns:
        Dict[str, Any]: The saved execution data, including generated session_id if created
    """
    try:
        # 获取执行ID和工作流ID
        execution_id = execution_data.get("execution_id")
        workflow_id = execution_data.get("workflow_id")

        # 记录日志
        logging.info(f"准备保存执行数据: {execution_id} for workflow {workflow_id}")
        logging.debug(f"执行数据内容: {execution_data}")

        # 调用存储功能
        success = save_execution_to_storage(execution_data)

        if success:
            return execution_data
        else:
            logging.error(f"保存执行数据失败: {execution_id}")
            return {}
    except Exception as e:
        logging.error(f"保存执行数据时发生错误: {str(e)}")
        return {}
```

#### 1.1.2 移除 `src/workflow/execution/execution_operations.py` 中的 `execute_workflow` 函数

```python
# src/workflow/execution/execution_operations.py 的修改版本，移除 execute_workflow 函数
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行操作

提供工作流执行相关的功能，包括执行历史获取、保存等。
"""

import datetime
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from src.core.config import get_config
from src.utils.file_utils import ensure_directory_exists, read_json_file, write_json_file

logger = logging.getLogger(__name__)


def save_execution(execution_data: Dict[str, Any]) -> bool:
    """
    保存工作流执行数据到持久化存储

    Args:
        execution_data: 执行数据

    Returns:
        bool: 是否保存成功
    """
    execution_id = execution_data.get("execution_id")
    workflow_id = execution_data.get("workflow_id")

    logger.info(f"保存工作流执行数据: 执行ID:{execution_id}, 工作流ID:{workflow_id}")

    try:
        # 获取存储目录
        config = get_config()
        data_dir = config.get("paths.data_dir", "data")
        if not os.path.isabs(data_dir):
            # 如果是相对路径，转换为绝对路径
            data_dir = os.path.abspath(data_dir)

        executions_dir = os.path.join(data_dir, "workflow_executions")
        ensure_directory_exists(executions_dir)

        # 生成文件名
        filename = f"{execution_id}.json"
        file_path = os.path.join(executions_dir, filename)

        # 保存数据到文件
        write_json_file(file_path, execution_data)

        logger.info(f"已保存执行数据到: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存执行数据失败: {str(e)}")
        return False


def get_workflow_executions(workflow_id: str) -> List[Dict[str, Any]]:
    """
    获取工作流的执行历史记录

    Args:
        workflow_id: 工作流ID

    Returns:
        List[Dict[str, Any]]: 执行历史记录列表
    """
    config = get_config()
    # 获取data_dir路径，确保配置正确访问
    data_dir = config.get("paths.data_dir", ".")
    executions_dir = os.path.join(data_dir, "workflow_executions")

    if not os.path.exists(executions_dir):
        return []

    executions = []

    # 查找匹配工作流ID的执行记录
    for filename in os.listdir(executions_dir):
        if filename.startswith(f"{workflow_id}_") and filename.endswith(".json"):
            execution_path = os.path.join(executions_dir, filename)
            try:
                execution_data = read_json_file(execution_path)
                executions.append(execution_data)
            except Exception as e:
                logger.error(f"读取执行文件 {filename} 出错: {str(e)}")

    # 按执行时间排序（从新到旧）
    executions.sort(key=lambda x: x.get("start_time", ""), reverse=True)

    return executions


def get_executions_for_workflow(workflow_id: str) -> List[Dict[str, Any]]:
    """
    获取工作流的所有执行记录

    这是更推荐使用的新API，相比get_workflow_executions函数增加了日志记录

    Args:
        workflow_id: 工作流ID

    Returns:
        List[Dict[str, Any]]: 执行记录列表
    """
    logger.info(f"获取工作流执行历史: 工作流ID:{workflow_id}")
    return get_workflow_executions(workflow_id)


def get_execution_by_id(execution_id: str) -> Optional[Dict[str, Any]]:
    """
    通过执行ID获取执行记录

    Args:
        execution_id: 执行ID

    Returns:
        Optional[Dict[str, Any]]: 执行记录或None
    """
    config = get_config()
    data_dir = config.get("paths.data_dir", ".")
    executions_dir = os.path.join(data_dir, "workflow_executions")

    if not os.path.exists(executions_dir):
        return None

    # 遍历所有执行记录文件
    for filename in os.listdir(executions_dir):
        if filename.endswith(".json"):
            execution_path = os.path.join(executions_dir, filename)
            try:
                execution_data = read_json_file(execution_path)
                if execution_data.get("execution_id") == execution_id:
                    return execution_data
            except Exception as e:
                logger.error(f"读取执行文件 {filename} 出错: {str(e)}")

    return None


def update_execution_status(execution_id: str, status: str, messages: List[str] = None) -> bool:
    """
    更新执行状态

    Args:
        execution_id: 执行ID
        status: 新状态
        messages: 要添加的消息列表

    Returns:
        bool: 更新是否成功
    """
    execution = get_execution_by_id(execution_id)
    if not execution:
        logger.error(f"找不到执行记录: {execution_id}")
        return False

    execution["status"] = status
    if messages:
        if "messages" not in execution:
            execution["messages"] = []
        execution["messages"].extend(messages)

    # 更新结束时间（如果是终态）
    if status in ["completed", "failed", "aborted"]:
        execution["end_time"] = datetime.datetime.now().isoformat()

    return save_execution(execution)
```

#### 1.1.3 更新 `src/workflow/__init__.py` 移除相关导入和导出

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流系统

提供工作流的创建、读取、更新、删除等管理功能，
以及工作流的进度跟踪等功能。
"""

from src.workflow.flow_cmd.workflow_creator import create_workflow_from_rule, create_workflow_from_template_with_vars

from src.workflow.workflow_advanced_operations import (
    calculate_progress_statistics,
    # 移除 execute_workflow
    get_executions_for_workflow,
    get_workflow_context,
    get_workflow_executions,
    get_workflow_fuzzy,
    save_execution,
)
from src.workflow.workflow_operations import (
    create_workflow,
    delete_workflow,
    get_workflow,
    get_workflow_by_id,
    get_workflow_by_name,
    get_workflow_by_type,
    get_workflow_file_path,
    get_workflows_directory,
    list_workflows,
    update_workflow,
)
from src.workflow.workflow_template import (
    create_workflow_from_template,
    create_workflow_template,
    delete_workflow_template,
    get_workflow_template,
    list_workflow_templates,
    update_workflow_template,
)

__all__ = [
    "list_workflows",
    "get_workflow",
    "get_workflow_by_id",
    "get_workflow_by_name",
    "get_workflow_by_type",
    "create_workflow",
    "update_workflow",
    "delete_workflow",
    "get_workflows_directory",
    "get_workflow_file_path",
    # 移除 "execute_workflow",
    "get_workflow_executions",
    "get_executions_for_workflow",
    "save_execution",
    "calculate_progress_statistics",
    "get_workflow_context",
    "get_workflow_fuzzy",
    "create_workflow_from_rule",
    "create_workflow_from_template_with_vars",
    "list_workflow_templates",
    "get_workflow_template",
    "create_workflow_template",
    "update_workflow_template",
    "delete_workflow_template",
    "create_workflow_from_template",
]
```

#### 1.1.4 更新 `src/workflow/workflow_advanced_operations.py` 移除相关导入

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流高级操作

导入点，集成了工作流的多个高级功能模块。
"""

# 从各个子模块导入公共API
from src.workflow.analytics.workflow_analytics import calculate_progress_statistics, get_workflow_executions
# 移除 execute_workflow 导入，保留其他函数
from src.workflow.execution.workflow_execution import get_executions_for_workflow, save_execution
from src.workflow.search.workflow_search import get_workflow_context, get_workflow_fuzzy

# 公共API
__all__ = [
    # 工作流分析功能
    "calculate_progress_statistics",
    "get_workflow_executions",
    # 工作流执行功能 - 移除 execute_workflow
    "get_executions_for_workflow",
    "save_execution",
    # 工作流搜索功能
    "get_workflow_fuzzy",
    "get_workflow_context",
]
```

### 1.2 完善 FlowService 作为模块间连接点

现有的 `FlowService` 代码已经设计良好，但我们需要确保它正确地连接 `workflow` 和 `flow_session` 模块，而不是混合职责。

主要确认点：

1. `FlowService` 应该清晰区分工作流定义管理和会话管理的方法
2. 不应包含执行逻辑，而是委托给专门的模块

## 2. 测试与验证

在实施代码更改后，需要进行以下测试：

### 2.1 单元测试

1. 测试 `workflow` 模块的核心功能，确保删除执行代码后其他功能仍正常工作
2. 测试 `flow_session` 模块的会话管理功能，特别是确保它能接管执行职责
3. 测试 `status` 模块的状态同步功能

### 2.2 集成测试

1. 测试通过 `FlowService` 创建工作流定义和会话的完整流程
2. 测试工作流状态变更是否正确反映在 `status` 模块中

## 3. 文档更新

### 3.1 架构文档

更新架构文档，明确说明三个核心模块的职责：

1. `workflow` 模块：工作流定义管理
2. `flow_session` 模块：工作流会话和执行状态管理
3. `status` 模块：状态观测和同步

### 3.2 API文档

更新API文档，特别是：

1. 明确哪些函数已被移除或替换
2. 推荐使用哪些新的API进行工作流执行

## 4. 长期改进建议

为了进一步优化系统架构，我们建议：

1. **数据库迁移**：根据 `dev-plan.md` 中的描述，实现从文件系统到数据库的迁移
2. **接口统一**：使用 `FlowService` 作为统一的服务层接口，避免直接调用底层模块
3. **事件驱动**：实现更完善的事件驱动架构，使状态变更能更自然地在模块间传播
4. **测试覆盖**：增加测试覆盖率，确保系统的稳定性和可靠性

## 5. 执行时间表

| 任务                               | 预计时间  | 优先级 |
|----------------------------------|---------|-------|
| 删除冗余执行代码                      | 1小时    | 高    |
| 更新导入和导出                        | 1小时    | 高    |
| 验证和测试修改                        | 2小时    | 高    |
| 更新文档                            | 2小时    | 中    |
| 实现长期改进                         | 进行中    | 低    |
