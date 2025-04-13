# 工作流记录系统开发方案

## 1. 概述

根据模块架构设计和职责分离原则，我们需要将工作流操作记录功能从workflow模块中拆分出来，创建一个专门的`src/log`模块，专注于记录工作流操作，但不参与实际执行。这样可以进一步明确workflow模块只负责工作流定义管理，而执行记录和日志则由专门的模块处理。

## 2. 设计目标

1. **职责分离**：将日志记录功能从workflow模块中完全分离
2. **统一接口**：提供统一的日志记录和检索接口
3. **灵活存储**：支持文件系统和数据库两种存储方式
4. **无侵入性**：不改变现有功能的使用方式
5. **可扩展性**：支持未来扩展到不同类型的日志

## 3. 架构设计

### 3.1 模块结构

```
src/log/
├── __init__.py                  # 模块入口
├── config.py                    # 配置管理
├── models/                      # 数据模型
│   ├── __init__.py
│   ├── workflow_log.py          # 工作流日志模型
│   └── operation_log.py         # 操作日志模型
├── storage/                     # 存储实现
│   ├── __init__.py
│   ├── base_storage.py          # 存储基类
│   ├── file_storage.py          # 文件存储实现
│   └── db_storage.py            # 数据库存储实现
├── service/                     # 服务层
│   ├── __init__.py
│   ├── workflow_log_service.py  # 工作流日志服务
│   └── log_formatter.py         # 日志格式化工具
└── adapters/                    # 适配器
    ├── __init__.py
    └── workflow_logger.py       # 工作流日志适配器
```

### 3.2 核心组件

#### 3.2.1 LogService

中心服务类，统一管理所有日志操作，提供给其他模块使用：

```python
class LogService:
    def __init__(self, storage_type="file", config=None):
        self.config = config or load_default_config()
        self.storage = create_storage(storage_type, self.config)
        self.workflow_logger = WorkflowLogger(self.storage)

    def log_workflow_execution(self, execution_data):
        """记录工作流执行日志"""
        return self.workflow_logger.log_execution(execution_data)

    def log_workflow_operation(self, operation_type, workflow_id, data=None):
        """记录工作流操作日志"""
        return self.workflow_logger.log_operation(operation_type, workflow_id, data)

    def get_workflow_executions(self, workflow_id=None, filters=None):
        """获取工作流执行记录"""
        return self.workflow_logger.get_executions(workflow_id, filters)
```

#### 3.2.2 存储实现

设计存储接口和多种实现：

```python
class BaseLogStorage:
    """日志存储基类"""
    def save_log(self, log_type, log_data):
        """保存日志"""
        raise NotImplementedError

    def get_logs(self, log_type, filters=None):
        """获取日志"""
        raise NotImplementedError

    def get_log_by_id(self, log_type, log_id):
        """根据ID获取日志"""
        raise NotImplementedError
```

文件存储实现：

```python
class FileLogStorage(BaseLogStorage):
    def __init__(self, config):
        self.base_dir = config.get("log_dir", "data/logs")

    def save_log(self, log_type, log_data):
        # 保存到JSON文件

    def get_logs(self, log_type, filters=None):
        # 从JSON文件读取
```

数据库存储实现：

```python
class DatabaseLogStorage(BaseLogStorage):
    def __init__(self, config):
        self.session_factory = get_session_factory()
        self.session = self.session_factory()

    def save_log(self, log_type, log_data):
        # 保存到数据库

    def get_logs(self, log_type, filters=None):
        # 从数据库查询
```

#### 3.2.3 日志模型

工作流执行日志模型：

```python
class WorkflowExecutionLog:
    """工作流执行日志模型"""
    def __init__(self, execution_id, workflow_id, status, start_time=None,
                 end_time=None, context=None, messages=None):
        self.execution_id = execution_id
        self.workflow_id = workflow_id  # 工作流定义ID，引用WorkflowDefinition
        self.status = status
        self.start_time = start_time or datetime.now().isoformat()
        self.end_time = end_time
        self.context = context or {}
        self.messages = messages or []

    def to_dict(self):
        """转换为字典"""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "context": self.context,
            "messages": self.messages
        }
```

工作流操作日志模型：

```python
class WorkflowOperationLog:
    """工作流操作日志模型"""
    def __init__(self, operation_id, operation_type, workflow_id,
                 timestamp=None, user=None, data=None):
        self.operation_id = operation_id
        self.operation_type = operation_type  # CREATE, UPDATE, DELETE, etc.
        self.workflow_id = workflow_id  # 工作流定义ID，引用WorkflowDefinition
        self.timestamp = timestamp or datetime.now().isoformat()
        self.user = user
        self.data = data or {}

    def to_dict(self):
        """转换为字典"""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "workflow_id": self.workflow_id,
            "timestamp": self.timestamp,
            "user": self.user,
            "data": self.data
        }
```

### 3.3 数据库模型

使用SQLAlchemy ORM定义数据库模型：

```python
from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class WorkflowExecutionLogModel(Base):
    __tablename__ = "workflow_execution_logs"

    execution_id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflow_definitions.id"), index=True)
    status = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    context = Column(JSON)
    messages = Column(JSON)

    def to_dict(self):
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "context": self.context,
            "messages": self.messages
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            status=data["status"],
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            context=data.get("context", {}),
            messages=data.get("messages", [])
        )
```

## 4. 迁移方案

### 4.1 代码迁移步骤

1. 创建新的src/log模块结构
2. 从workflow/execution模块中提取日志相关功能
3. 实现LogService和相关组件
4. 更新workflow模块，使用LogService替代原有日志功能
5. 确保向后兼容性，保持API不变

### 4.2 数据迁移

1. 写入双向兼容层，同时写入旧文件结构和新日志系统
2. 实现数据迁移工具，将现有日志数据迁移到新系统
3. 添加迁移检查工具，验证迁移的完整性

### 4.3 接口适配

原有接口如`get_workflow_executions`将被保留，但实现将委托给新的LogService：

```python
# 原接口保持不变，但实现委托给LogService
def get_workflow_executions(workflow_id):
    from src.log import log_service
    return log_service.get_workflow_executions(workflow_id)
```

## 5. 实现细节

### 5.1 主要API定义

#### LogService API

```python
# 记录工作流执行开始
execution_log = log_service.start_workflow_execution(workflow_id, context=context)

# 更新工作流执行状态
log_service.update_workflow_execution(execution_id, status="completed", messages=["执行完成"])

# 获取工作流执行记录
executions = log_service.get_workflow_executions(workflow_id)

# 记录工作流操作
log_service.log_workflow_operation("CREATE", workflow_id, data=workflow_data)
```

#### WorkflowLogger API

```python
# 记录执行日志
logger.log_execution(execution_data)

# 记录操作日志
logger.log_operation("UPDATE", workflow_id, data={"name": "新名称"})

# 获取执行记录
executions = logger.get_executions(workflow_id)

# 获取操作记录
operations = logger.get_operations(workflow_id)
```

### 5.2 文件存储结构

```
data/
├── logs/
│   ├── workflow_executions/         # 工作流执行日志
│   │   ├── <execution_id>.json      # 按执行ID存储
│   │   └── ...
│   └── workflow_operations/         # 工作流操作日志
│       ├── <operation_id>.json      # 按操作ID存储
│       └── ...
```

### 5.3 数据库结构

```sql
CREATE TABLE workflow_execution_logs (
    execution_id TEXT PRIMARY KEY,
    workflow_id TEXT,
    status TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    context JSON,
    messages JSON
);

CREATE TABLE workflow_operation_logs (
    operation_id TEXT PRIMARY KEY,
    operation_type TEXT,
    workflow_id TEXT,
    timestamp TIMESTAMP,
    user TEXT,
    data JSON
);
```

## 6. 测试策略

### 6.1 单元测试

1. 测试LogService各个API
2. 测试不同存储实现
3. 测试日志模型和格式化

### 6.2 集成测试

1. 测试日志系统与workflow模块的集成
2. 测试数据持久化和检索

### 6.3 迁移测试

1. 测试从旧结构迁移到新结构
2. 验证数据完整性

## 7. 实施计划

### 阶段1：基础结构设计

1. 创建src/log模块基础结构
2. 实现核心接口和模型
3. 实现文件存储系统

### 阶段2：日志服务实现

1. 实现LogService完整功能
2. 实现WorkflowLogger适配器
3. 添加配置管理和初始化

### 阶段3：数据库存储实现

1. 实现数据库模型
2. 实现数据库存储
3. 添加存储类型切换功能

### 阶段4：迁移与集成

1. 与workflow模块集成
2. 实现数据迁移工具
3. 确保向后兼容性

### 阶段5：测试与文档

1. 编写单元测试和集成测试
2. 更新文档
3. 性能测试与优化

## 8. 总结

通过建立独立的日志模块，我们可以实现以下目标：

1. 明确职责分离，workflow模块专注于工作流定义管理
2. 提供统一的日志记录和查询接口
3. 灵活支持不同的存储方式
4. 为未来的扩展和功能增强奠定基础

该方案符合模块架构文档中的职责分离原则，进一步优化了系统架构，并为未来的数据库迁移做好了准备。
