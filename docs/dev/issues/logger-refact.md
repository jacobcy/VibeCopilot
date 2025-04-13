# 工作流相关模块中的日志替换工作

首先，我发现以下几个需要处理的问题：

1. 有些模块还在使用旧的日志方式：

```python
import logging
logger = logging.getLogger(__name__)
```

2. 日志目录结构尚未创建
3. 缺少日志配置的初始化逻辑

让我们按照以下步骤进行处理：

1. 首先创建日志目录结构：

```bash
mkdir -p logs/workflow/{session,stage,execution}
```

2. 让我们搜索所有使用旧日志方式的文件：

Ran tool

Ran tool
我们需要创建一个日志初始化模块，来统一管理所有日志配置。让我创建这个模块：

```python:src/core/log_init.py
"""
日志初始化模块

提供统一的日志配置管理，包括通用日志和工作流日志的初始化。
"""

import logging.config
import os
from typing import Optional

import yaml

from src.core.logger import setup_logger, setup_workflow_logger
from src.workflow.logger import workflow_logger


def init_logging(config_path: Optional[str] = None) -> None:
    """
    初始化日志系统

    Args:
        config_path: 日志配置文件路径，如果不指定则使用默认配置
    """
    # 创建日志目录
    _ensure_log_dirs()

    # 加载配置
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        # 使用默认配置
        _setup_default_logging()


def _ensure_log_dirs() -> None:
    """确保所有需要的日志目录存在"""
    dirs = [
        "logs",
        "logs/workflow",
        "logs/workflow/session",
        "logs/workflow/stage",
        "logs/workflow/execution"
    ]

    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)


def _setup_default_logging() -> None:
    """设置默认的日志配置"""
    # 设置根日志记录器
    root_logger = setup_logger(
        name="root",
        log_file="logs/app.log",
        format_str="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    root_logger.setLevel(logging.INFO)

    # 设置工作流日志记录器
    workflow_root_logger = setup_workflow_logger(
        name="workflow",
        log_file="logs/workflow/workflow.log"
    )
    workflow_root_logger.setLevel(logging.INFO)


def get_logger(name: str, is_workflow: bool = False) -> logging.Logger:
    """
    获取日志记录器的统一接口

    Args:
        name: 日志记录器名称
        is_workflow: 是否是工作流日志

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    if is_workflow:
        return workflow_logger.get_logger(name)
    else:
        return setup_logger(name)
```
现在，让我们修改主程序入口，确保在程序启动时初始化日志系统：

```python:src/main.py
"""
VibeCopilot主程序入口

提供程序的初始化和启动功能。
"""

import os
from typing import Optional

from src.core.log_init import init_logging, get_logger
from src.db import init_db

# 初始化日志系统
config_path = os.path.join('config', 'logging.yaml')
init_logging(config_path)

# 获取主程序日志记录器
logger = get_logger(__name__)


def init_app() -> None:
    """初始化应用程序"""
    try:
        # 初始化数据库
        init_db()
        logger.info("数据库初始化成功")

        # 其他初始化操作...

    except Exception as e:
        logger.error(f"应用程序初始化失败: {str(e)}")
        raise


def main() -> None:
    """主程序入口"""
    try:
        # 初始化应用
        init_app()
        logger.info("VibeCopilot启动成功")

        # 主程序逻辑...

    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        raise


if __name__ == "__main__":
    main()
```
现在，我们需要修改工作流相关模块，使用新的日志系统。让我们从一个关键模块开始：

```python:src/workflow/service/flow_service.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流服务模块

提供统一的工作流服务接口，集成会话管理和工作流操作功能。
使用组件化设计，将不同职责委托给专门的服务组件。
"""

from typing import Any, Dict, List, Optional

from src.core.log_init import get_logger
from src.db import get_session_factory
from src.flow_session.session.manager import FlowSessionManager
from src.flow_session.stage.manager import StageInstanceManager
from src.workflow.operations import (
    create_workflow,
    delete_workflow,
    get_workflow,
    get_workflow_by_name,
    get_workflow_by_type,
    list_workflows,
    update_workflow,
    validate_workflow_files,
)
from src.workflow.service.components import BaseService, ExecutionService, SessionService, StageService, WorkflowDefinitionService

# 获取工作流日志记录器
logger = get_logger("workflow.service", is_workflow=True)


class FlowService(BaseService):
    """工作流服务类，提供统一的工作流操作接口"""

    def __init__(self, verbose=False):
        """初始化工作流服务

        Args:
            verbose: 是否显示详细日志
        """
        super().__init__(verbose)

        # 初始化子服务
        self.session_service = SessionService(self.session_manager, verbose)
        self.stage_service = StageService(self.stage_manager, verbose)
        self.execution_service = ExecutionService(self.session_manager, verbose)
        self.workflow_service = WorkflowDefinitionService(verbose)

    def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新的工作流定义

        Args:
            workflow_data: 工作流定义数据

        Returns:
            创建的工作流数据
        """
        logger.info(f"创建新工作流: {workflow_data.get('name', 'unnamed')}")
        return self.workflow_service.create_workflow(workflow_data)

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流数据或None
        """
        logger.debug(f"获取工作流: {workflow_id}")
        return self.workflow_service.get_workflow(workflow_id)

    def list_workflows(self, workflow_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出工作流定义

        Args:
            workflow_type: 工作流类型过滤

        Returns:
            工作流列表
        """
        logger.debug(f"列出工作流 (类型={workflow_type})")
        return self.workflow_service.list_workflows(workflow_type)

    def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新工作流定义

        Args:
            workflow_id: 工作流ID
            workflow_data: 更新数据

        Returns:
            更新后的工作流数据或None
        """
        logger.info(f"更新工作流: {workflow_id}")
        return self.workflow_service.update_workflow(workflow_id, workflow_data)

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        删除工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            是否删除成功
        """
        logger.info(f"删除工作流: {workflow_id}")
        return self.workflow_service.delete_workflow(workflow_id)

    def execute_workflow(
        self,
        workflow_id: str,
        session_name: Optional[str] = None,
        stage_id: Optional[str] = None,
        auto_advance: bool = False
    ) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            workflow_id: 工作流ID
            session_name: 会话名称
            stage_id: 起始阶段ID
            auto_advance: 是否自动推进

        Returns:
            执行结果
        """
        logger.info(f"执行工作流: {workflow_id} (session={session_name}, stage={stage_id})")
        return self.execution_service.execute_workflow(workflow_id, session_name=session_name)

    def resume_workflow_execution(
        self, session_id: str, stage_id: Optional[str] = None, auto_advance: bool = False
    ) -> Dict[str, Any]:
        """
        恢复工作流执行

        Args:
            session_id: 会话ID
            stage_id: 阶段ID
            auto_advance: 是否自动推进

        Returns:
            执行结果
        """
        logger.info(f"恢复工作流执行: session={session_id}, stage={stage_id}")
        return self.execution_service.resume_execution(session_id, stage_id)
```
让我总结一下我们的日志系统改造计划：

1. **已完成的工作**：

- 创建了日志目录结构
- 创建了统一的日志配置文件
- 实现了工作流专用日志适配器
- 创建了日志初始化模块
- 修改了主程序入口
- 更新了部分工作流模块

2. **待完成的工作**：

a) 修改其他工作流相关模块：
```python
# 需要修改的关键模块：
- src/workflow/service/components/*.py
- src/workflow/operations/*.py
- src/workflow/execution/*.py
- src/flow_session/*.py
```

b) 更新日志配置：
```yaml
# 需要添加的日志配置：
- 日志轮转设置
- 不同级别日志分文件存储
- 错误日志单独存储
```

c) 创建日志工具：
```python
# 需要开发的工具：
- 日志查询接口
- 日志分析工具
- 日志监控告警
```

3. **迁移指南**：

对于需要修改的模块，按照以下步骤进行：

```python
# 1. 删除旧的日志导入
- import logging
- logger = logging.getLogger(__name__)

# 2. 添加新的日志导入
from src.core.log_init import get_logger

# 3. 获取日志记录器
# 对于工作流相关模块：
logger = get_logger("module_name", is_workflow=True)

# 对于普通模块：
logger = get_logger("module_name")

# 4. 更新日志调用
# 旧代码：
logger.debug("Some message")

# 新代码：
logger.debug("Some message", extra={
    "workflow_id": workflow_id,
    "session_id": session_id,
    # 其他上下文信息...
})
```

4. **使用建议**：

```python
# 1. 日志级别使用规范
logger.debug()  # 用于详细的调试信息
logger.info()   # 用于重要的状态变更
logger.warning()  # 用于潜在问题警告
logger.error()    # 用于错误但不影响运行
logger.critical() # 用于致命错误

# 2. 上下文信息使用
logger.info("创建工作流", extra={
    "workflow_id": workflow_id,
    "workflow_type": workflow_type,
    "creator": user_id
})

# 3. 结构化日志
logger.info("工作流状态变更", extra={
    "workflow_id": workflow_id,
    "old_status": old_status,
    "new_status": new_status,
    "trigger": trigger_event
})
```

5. **注意事项**：

- 确保在使用日志前初始化日志系统
- 工作流相关模块必须使用工作流日志记录器
- 重要操作必须记录日志
- 敏感信息不要记录到日志
- 定期清理旧日志文件
