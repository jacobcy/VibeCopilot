# 工作流会话管理 (Flow Session)

## 简介

工作流会话管理模块提供了对工作流实例的生命周期管理，包括创建、暂停、恢复、完成和终止工作流会话。会话管理使工作流能够保持状态和上下文，从而实现工作流的中断和恢复。

## 核心组件

- **FlowSessionManager**: 管理工作流会话的CRUD操作和状态转换
- **StageInstanceManager**: 管理阶段实例的CRUD操作和状态转换
- **FlowStatusIntegration**: 提供与状态系统的集成
- **StageInstance**: 工作流阶段的状态表示
- **SessionStatus/StageStatus**: 会话和阶段状态定义

### 状态系统

工作流状态系统定义了以下状态：

```python
# 会话和阶段共用的状态
PENDING   # 待处理
ACTIVE    # 执行中
COMPLETED # 已完成
FAILED    # 执行失败
PAUSED    # 已暂停
```

### 日志系统

工作流会话管理使用分层的日志系统：

```python
# 日志分类
workflow.session.integration  # 会话集成日志
workflow.session.operations  # 会话操作日志
workflow.stage.integration   # 阶段集成日志
workflow.stage.operations   # 阶段操作日志

# 日志级别
INFO     # 重要操作记录
DEBUG    # 详细执行信息
WARNING  # 潜在问题警告
ERROR    # 操作失败信息
```

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

# 查看会话日志
vc flow session logs <session_id> [--level=INFO]
```

## 与工作流命令的集成

工作流会话管理与现有的工作流命令集成，允许在运行工作流时指定会话：

```bash
# 在新会话中运行工作流阶段
vc flow run workflow_name:stage_name

# 在现有会话中运行工作流阶段
vc flow run workflow_name:stage_name --session=<session_id>

# 显示工作流执行进度
vc flow status <session_id>
```

## 程序化接口

除了命令行界面，工作流会话管理也提供了程序化接口，可以在Python代码中直接使用：

```python
from src.flow_session import FlowSessionManager, StageManager
from src.flow_session.status.status import SessionStatus, StageStatus
from src.db import get_session_factory, init_db

# 获取数据库会话
engine = init_db()
SessionFactory = get_session_factory(engine)

with SessionFactory() as session:
    # 创建会话管理器
    session_manager = FlowSessionManager(session)
    stage_manager = StageManager(session)

    # 创建新会话
    flow_session = session_manager.create_session(
        workflow_id="workflow-id",
        name="会话名称",
        metadata={"key": "value"}
    )

    # 创建阶段实例
    stage = stage_manager.create_stage(
        session_id=flow_session.id,
        stage_type="task",
        config={"timeout": 3600}
    )

    # 更新阶段状态
    stage_manager.update_stage_status(
        stage.id,
        StageStatus.ACTIVE,
        metadata={"progress": 50}
    )

    # 获取会话进度
    progress = session_manager.get_session_progress(flow_session.id)
```

## 集成点

工作流会话管理模块与以下组件集成：

1. **数据库**: 使用SQLAlchemy ORM持久化会话和阶段实例数据
2. **状态系统**: 通过FlowStatusIntegration与状态系统集成
3. **日志系统**: 使用分层日志记录会话和阶段的操作
4. **工作流执行**: 与工作流执行命令(flow run)集成，支持会话化执行
5. **命令行界面**: 通过CLI命令与主命令行界面集成

## 架构说明

工作流会话管理遵循仓储模式(Repository Pattern)和服务层模式(Service Layer Pattern)：

```
src/flow_session/
├── session/                 # 会话管理
│   ├── manager.py          # 会话管理器
│   └── repository.py       # 会话数据访问
├── stage/                   # 阶段管理
│   ├── manager.py          # 阶段管理器
│   ├── stage.py            # 阶段实例定义
│   └── repository.py       # 阶段数据访问
├── status/                  # 状态定义
│   └── status.py           # 状态枚举
└── cli/                    # 命令行接口
    └── commands.py         # 命令实现
```

## 测试

测试可以通过以下命令运行：

```bash
# 运行所有Flow Session测试
python -m unittest discover -s src/flow_session/tests

# 运行特定测试文件
python -m unittest src/flow_session/tests/test_cli.py

# 运行带覆盖率报告的测试
coverage run -m unittest discover -s src/flow_session/tests
coverage report
```

## 日志查看

可以通过以下方式查看会话日志：

```bash
# 查看特定会话的日志
tail -f logs/workflow/session/<session_id>.log

# 查看所有会话的操作日志
tail -f logs/workflow/session/operations.log

# 查看会话集成日志
tail -f logs/workflow/session/integration.log
```
