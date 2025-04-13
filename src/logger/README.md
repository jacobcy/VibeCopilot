# 日志服务模块 (src/log)

本模块提供 VibeCopilot 的日志记录功能，支持多种类型的日志记录并提供多种输出方式。

## 模块特点

- **双重持久化**：同时支持文件日志和数据库日志
- **支持多种日志类型**：工作流日志、操作日志、任务日志、性能指标、错误日志和审计日志
- **结构化日志**：所有日志以JSON格式记录，便于分析和处理
- **关联查询**：通过ID关联，支持工作流-操作-任务三级日志关系查询
- **可靠性设计**：数据库记录失败时不影响文件日志，确保日志不丢失

## 模块结构

```
src/log/
├── README.md             # 本文档
├── __init__.py           # 模块入口
├── log_service.py        # 日志服务实现
├── example_usage.py      # 使用示例
└── test_logging.py       # 测试用例
```

## 日志类型说明

本模块支持多种类型的日志记录：

1. **工作流日志**：记录工作流的开始和完成
2. **操作日志**：记录工作流中的操作步骤
3. **任务日志**：记录操作中的具体任务结果
4. **性能指标**：记录系统性能数据
5. **错误日志**：记录系统错误信息
6. **审计日志**：记录用户操作和系统变更

## 使用方法

### 基本使用

```python
from src.logger import log_workflow_start, log_workflow_complete

# 记录工作流开始
log_workflow_start(
    workflow_id="workflow-123",
    workflow_name="数据处理流程",
    trigger_info={"source": "user", "user_id": "user-123"}
)

# 处理完成后记录结果
log_workflow_complete(
    workflow_id="workflow-123",
    status="completed",
    result={"processed_items": 100, "success": True}
)
```

### 记录操作和任务

```python
from src.logger import log_operation_start, log_operation_complete, log_task_result

# 记录操作开始
log_operation_start(
    operation_id="op-123",
    workflow_id="workflow-123",
    operation_name="数据清洗",
    parameters={"dataset": "sales-2023", "method": "normalization"}
)

# 记录任务结果
log_task_result(
    task_id="task-456",
    operation_id="op-123",
    workflow_id="workflow-123",
    task_name="清洗商品数据",
    status="completed",
    result={"processed_items": 50, "errors": 0}
)

# 记录操作完成
log_operation_complete(
    operation_id="op-123",
    workflow_id="workflow-123",
    status="completed",
    result={"total_processed": 50, "duration_seconds": 5.2}
)
```

### 记录性能指标

```python
from src.logger import log_performance_metric

# 记录性能指标
log_performance_metric(
    metric_name="data_processing_time",
    value=3.45,  # 秒
    context={"data_size": "5MB", "method": "batch"},
    workflow_id="workflow-123",
    operation_id="op-123"
)
```

### 记录错误

```python
from src.logger import log_error
import traceback

try:
    # 可能出错的代码
    result = process_data(invalid_data)
except Exception as e:
    # 记录错误
    log_error(
        error_message=str(e),
        error_type=type(e).__name__,
        stack_trace=traceback.format_exc(),
        workflow_id="workflow-123",
        operation_id="op-123",
        context={"data_id": "invalid-data-001"}
    )
```

### 记录审计信息

```python
from src.logger import log_audit

# 记录审计信息
log_audit(
    user_id="user-123",
    action="DELETE_RECORD",
    resource_type="customer",
    resource_id="cust-456",
    details={"reason": "应用户要求删除个人数据"},
    workflow_id="workflow-123"
)
```

### 查询日志

```python
from src.logger import get_workflow_logs, get_workflow_operations, get_operation_tasks

# 获取最近的工作流日志
recent_workflows = get_workflow_logs(limit=10)

# 获取特定工作流的所有操作
operations = get_workflow_operations("workflow-123")

# 获取特定操作的所有任务
tasks = get_operation_tasks("op-123")
```

## 日志存储

### 文件日志

- 日志文件存储在项目根目录的 `logs` 目录下
- 文件名格式：`vibe-log-YYYY-MM-DD.log`
- 日志格式：标准JSON，每行一条记录

### 数据库日志

- 日志记录在SQLite数据库中
- 表结构：
  - `workflow_logs`: 工作流日志
  - `operation_logs`: 操作日志
  - `task_logs`: 任务日志
  - `performance_logs`: 性能指标
  - `error_logs`: 错误日志
  - `audit_logs`: 审计日志

## 开发和维护

### 添加新的日志类型

1. 在 `src/models/db/log.py` 中添加新的数据库模型
2. 在 `src/db/repositories/log_repository.py` 中添加对应的仓库类
3. 在 `src/db/specific_managers/log_manager.py` 中添加管理方法
4. 在 `src/log/log_service.py` 中添加新的日志函数
5. 在 `src/log/__init__.py` 中导出新函数
6. 更新测试用例 `test_logging.py`

### 日志级别控制

可以通过环境变量控制日志级别：

```bash
export LOG_LEVEL=DEBUG     # 开发环境
export LOG_LEVEL=INFO      # 生产环境
export LOG_LEVEL=WARNING   # 只记录警告和错误
```

### 解决常见问题

- **日志文件权限问题**：确保应用有写入logs目录的权限
- **数据库连接问题**：如果数据库连接失败，系统会降级为只使用文件日志
- **日志格式解析错误**：检查日志数据是否包含非法字符

## 示例

参见 `example_usage.py` 文件，展示了完整的日志使用场景。

## 注意事项

1. 日志中不应包含敏感信息（如密码、认证令牌等）
2. 避免在循环中过度记录日志，以免产生大量重复信息
3. 对于大型对象，应只记录关键信息而不是完整对象
4. 代码中的异常应尽量被捕获并使用 `log_error` 记录，而不是让异常继续传播
