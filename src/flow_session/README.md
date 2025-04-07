# 工作流会话管理 (Flow Session)

## 简介

工作流会话管理模块提供了对工作流实例的生命周期管理，包括创建、暂停、恢复、完成和终止工作流会话。会话管理使工作流能够保持状态和上下文，从而实现工作流的中断和恢复。

## 核心组件

- **FlowSessionManager**: 管理工作流会话的CRUD操作和状态转换
- **StageInstanceManager**: 管理阶段实例的CRUD操作和状态转换
- **FlowStatusIntegration**: 提供与状态系统的集成

## 命令行界面

工作流会话管理模块提供了一套命令行界面，可以通过以下方式使用：

```bash
# 列出所有会话
vc flow session list

# 查看特定会话详情
vc flow session show <session_id>

# 创建新会话
vc flow session create <workflow_id> --name="会话名称"

# 暂停会话
vc flow session pause <session_id>

# 恢复会话
vc flow session resume <session_id>

# 终止会话
vc flow session abort <session_id>

# 删除会话
vc flow session delete <session_id> --force
```

## 与工作流命令的集成

工作流会话管理与现有的工作流命令集成，允许在运行工作流时指定会话：

```bash
# 在新会话中运行工作流阶段
vc flow run workflow_name:stage_name

# 在现有会话中运行工作流阶段
vc flow run workflow_name:stage_name --session=<session_id>
```

## 程序化接口

除了命令行界面，工作流会话管理也提供了程序化接口，可以在Python代码中直接使用：

```python
from src.flow_session import FlowSessionManager
from src.db import get_session_factory, init_db

# 获取数据库会话
engine = init_db()
SessionFactory = get_session_factory(engine)

with SessionFactory() as session:
    # 创建会话管理器
    manager = FlowSessionManager(session)

    # 创建新会话
    flow_session = manager.create_session("workflow-id", "会话名称")

    # 查询会话
    session = manager.get_session("session-id")

    # 暂停会话
    manager.pause_session("session-id")

    # 恢复会话
    manager.resume_session("session-id")

    # 完成会话
    manager.complete_session("session-id")

    # 终止会话
    manager.abort_session("session-id")
```

## 集成点

工作流会话管理模块与以下组件集成：

1. **数据库**: 使用SQLAlchemy ORM持久化会话和阶段实例数据
2. **状态系统**: 通过FlowStatusIntegration与状态系统集成
3. **工作流执行**: 与工作流执行命令(flow run)集成，支持会话化执行
4. **命令行界面**: 通过CLI命令与主命令行界面集成

## 架构说明

工作流会话管理遵循仓储模式(Repository Pattern)和服务层模式(Service Layer Pattern)：

- **数据模型**(`src/models/db/flow_session.py`): 定义数据结构
- **仓储层**(`src/db/repositories/flow_session_repository.py`): 处理数据访问
- **服务层**(`src/flow_session/session_manager.py`等): 提供业务逻辑
- **接口层**(`src/flow_session/cli.py`): 提供用户接口

## 测试

测试可以通过以下命令运行：

```bash
# 运行所有Flow Session测试
python -m unittest discover -s src/flow_session/tests

# 运行特定测试文件
python -m unittest src/flow_session/tests/test_cli.py
```
