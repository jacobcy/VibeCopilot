# 工作流系统迁移指南

本文档提供工作流系统从旧结构迁移到新结构的详细指南，包括迁移原因、执行步骤和验证方法。

## 迁移背景

工作流系统最初设计时存在以下问题：

1. **模型分散**：工作流相关模型分散在多个目录中
   - 部分在`src/workflow/models/`目录
   - 部分在`src/models/db/`目录

2. **命名和结构不一致**：
   - `src/models/db/workflow.py`中有`WorkflowStep`类
   - `src/models/db/flow_session.py`中有`StageInstance`类
   - 代码引用不存在的`Stage`类

3. **数据结构与设计文档不匹配**：
   - 开发计划文档中明确设计了包含`Stages`表的数据库结构
   - 但实际实现中缺少对应的`Stage`类

## 迁移目标

1. 统一数据模型位置和命名
2. 添加缺失的`Stage`和`Transition`模型
3. 明确各模型之间的关系
4. 保持现有功能正常工作

## 迁移内容

### 1. 新增的模型类

#### 1.1 Stage（阶段）

```python
# src/models/db/stage.py
class Stage(Base):
    """工作流阶段数据库模型，表示工作流中的一个阶段"""

    __tablename__ = "stages"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    checklist = Column(JSON, nullable=True)  # 阶段检查项列表
    deliverables = Column(JSON, nullable=True)  # 阶段交付物定义
    weight = Column(Integer, default=100)  # 阶段权重，用于排序
    estimated_time = Column(String, nullable=True)  # 预计完成时间
    is_end = Column(Boolean, default=False)  # 是否为结束阶段
    depends_on = Column(JSON, default=list)  # 依赖的阶段ID列表
    prerequisites = Column(JSON, nullable=True)  # 阶段前置条件
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    workflow = relationship("Workflow", back_populates="stages")
    instances = relationship("StageInstance", back_populates="stage")
    from_transitions = relationship("Transition", foreign_keys="[Transition.from_stage]", back_populates="from_stage_rel")
    to_transitions = relationship("Transition", foreign_keys="[Transition.to_stage]", back_populates="to_stage_rel")
```

#### 1.2 Transition（转换）

```python
# src/models/db/transition.py
class Transition(Base):
    """工作流转换数据库模型，表示阶段间的转换关系"""

    __tablename__ = "transitions"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"))
    from_stage = Column(String, ForeignKey("stages.id", ondelete="CASCADE"))
    to_stage = Column(String, ForeignKey("stages.id", ondelete="CASCADE"))
    condition = Column(Text, nullable=True)  # 转换条件
    description = Column(Text, nullable=True)  # 转换描述
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    workflow = relationship("Workflow", back_populates="transitions")
    from_stage_rel = relationship("Stage", foreign_keys=[from_stage], back_populates="from_transitions")
    to_stage_rel = relationship("Stage", foreign_keys=[to_stage], back_populates="to_transitions")
```

### 2. 迁移和重构的模型

#### 2.1 WorkflowDefinition（工作流定义）

从`flow_session.py`迁移到独立文件`workflow_definition.py`：

```python
# src/models/db/workflow_definition.py
class WorkflowDefinition(Base):
    """工作流定义实体模型"""

    __tablename__ = "workflow_definitions"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    stages = Column(JSON, nullable=False)  # 可用阶段列表，JSON格式
    source_rule = Column(String, nullable=True)  # 来源规则文件
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    sessions = relationship(
        "FlowSession", back_populates="workflow_definition", cascade="all, delete-orphan"
    )
```

#### 2.2 StageInstance（阶段实例）

更新`StageInstance`类，添加与`Stage`的关系：

```python
# src/models/db/flow_session.py
class StageInstance(Base):
    """阶段实例实体模型"""

    __tablename__ = "stage_instances"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("flow_sessions.id", ondelete="CASCADE"), nullable=False)
    stage_id = Column(String, ForeignKey("stages.id"), nullable=False)  # 阶段ID，引用Stage表
    name = Column(String, nullable=False)
    # ... 其他字段 ...

    # 关系
    session = relationship("FlowSession", back_populates="stage_instances")
    stage = relationship("Stage", back_populates="instances")
```

#### 2.3 Workflow（工作流）

更新`Workflow`类，添加与`Stage`和`Transition`的关系：

```python
# src/models/db/workflow.py
class Workflow(Base):
    """工作流数据库模型，定义一个完整的流程"""

    __tablename__ = "workflows"

    # ... 现有字段 ...

    # 关系
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.order")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    stages = relationship("Stage", back_populates="workflow", cascade="all, delete-orphan")
    transitions = relationship("Transition", back_populates="workflow", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            # ... 现有字段 ...
            "stages": [stage.to_dict() for stage in self.stages] if self.stages else [],
            "transitions": [transition.to_dict() for transition in self.transitions] if self.transitions else [],
        }
```

## 数据迁移

### 1. 数据迁移脚本

使用`src/scripts/migrate_workflow_structure.py`脚本，将现有数据转换为新结构：

1. 从`WorkflowDefinition.stages`字段（JSON）中提取数据，创建`Stage`表记录
2. 根据`Stage`顺序创建`Transition`表记录
3. 从`WorkflowStep`中提取数据，创建`Stage`记录

### 2. 执行迁移步骤

1. 创建数据表：
   ```sql
   CREATE TABLE IF NOT EXISTS stages (
     id VARCHAR NOT NULL,
     workflow_id VARCHAR,
     name VARCHAR NOT NULL,
     description TEXT,
     order_index INTEGER NOT NULL,
     checklist JSON,
     deliverables JSON,
     weight INTEGER DEFAULT 100,
     estimated_time VARCHAR,
     is_end BOOLEAN DEFAULT false,
     depends_on JSON DEFAULT '[]'::jsonb,
     prerequisites JSON,
     created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
     updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
     PRIMARY KEY (id),
     FOREIGN KEY(workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
   );

   CREATE TABLE IF NOT EXISTS transitions (
     id VARCHAR NOT NULL,
     workflow_id VARCHAR,
     from_stage VARCHAR,
     to_stage VARCHAR,
     condition TEXT,
     description TEXT,
     created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
     updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
     PRIMARY KEY (id),
     FOREIGN KEY(workflow_id) REFERENCES workflows (id) ON DELETE CASCADE,
     FOREIGN KEY(from_stage) REFERENCES stages (id) ON DELETE CASCADE,
     FOREIGN KEY(to_stage) REFERENCES stages (id) ON DELETE CASCADE
   );
   ```

2. 运行迁移脚本：
   ```bash
   cd /Users/jacobcy/Public/VibeCopilot
   python src/scripts/migrate_workflow_structure.py
   ```

3. 验证数据迁移：
   ```sql
   SELECT COUNT(*) FROM stages;
   SELECT COUNT(*) FROM transitions;
   ```

## 代码迁移

### 1. 导入更新

更新相关导入语句，例如：

```python
# 旧的导入
from src.models.db.flow_session import FlowSession, StageInstance, WorkflowDefinition

# 新的导入
from src.models.db.flow_session import FlowSession, StageInstance
from src.models.db.workflow_definition import WorkflowDefinition
from src.models.db.stage import Stage
```

### 2. 仓库类更新

```python
# 新增仓库类导入
from src.db.repositories.stage_repository import StageRepository
from src.db.repositories.transition_repository import TransitionRepository
```

## 迁移后验证

### 1. 功能测试清单

- [ ] 创建工作流定义
- [ ] 创建工作流会话
- [ ] 启动和完成阶段
- [ ] 工作流状态查询
- [ ] 下一阶段建议功能
- [ ] 会话上下文管理

### 2. 验证SQL查询

```sql
-- 验证Stage和Workflow关系
SELECT w.name AS workflow_name, s.name AS stage_name
FROM workflows w
JOIN stages s ON w.id = s.workflow_id;

-- 验证Stage和Transition关系
SELECT s1.name AS from_stage, s2.name AS to_stage, t.condition
FROM transitions t
JOIN stages s1 ON t.from_stage = s1.id
JOIN stages s2 ON t.to_stage = s2.id;

-- 验证StageInstance关系
SELECT s.name AS stage_name, si.name AS instance_name, si.status
FROM stage_instances si
JOIN stages s ON si.stage_id = s.id;
```

## 问题排查

### 1. 常见问题

1. **外键约束错误**：确保先创建主表，再创建从表
2. **数据不一致**：检查数据迁移脚本是否正确处理所有边缘情况
3. **代码引用错误**：全局搜索旧的导入和模型引用，更新为新的路径

### 2. 回滚计划

如遇严重问题，可回滚迁移：

1. 备份新表中的数据（如有必要）
2. 恢复原始代码
3. 恢复数据库架构
