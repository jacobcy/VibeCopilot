# 工作流系统使用指南

本文档提供VibeCopilot工作流系统的使用方法，包括创建工作流、执行工作流和开发集成等方面的指导。

## 基本概念

### 工作流系统核心概念

1. **工作流定义（WorkflowDefinition）**：一个完整的流程定义，包含多个阶段和转换
2. **阶段（Stage）**：工作流中的一个步骤，包含任务和交付物
3. **转换（Transition）**：阶段之间的连接，定义从一个阶段到另一个阶段的条件
4. **会话（FlowSession）**：工作流的运行实例
5. **阶段实例（StageInstance）**：工作流会话中的阶段运行实例

## 命令行使用

### 1. 创建和管理工作流

#### 1.1 创建工作流

```bash
# 创建新工作流
vc flow create --name "需求分析流程" --desc "从用户需求到PRD文档的流程"
```

#### 1.2 添加阶段

```bash
# 添加工作流阶段
vc flow stage add --workflow "需求分析流程" --name "收集需求" --desc "收集用户需求" --order 1
vc flow stage add --workflow "需求分析流程" --name "分析需求" --desc "分析用户需求" --order 2
vc flow stage add --workflow "需求分析流程" --name "编写PRD" --desc "编写PRD文档" --order 3
```

#### 1.3 添加转换

```bash
# 添加阶段转换
vc flow transition add --workflow "需求分析流程" --from "收集需求" --to "分析需求"
vc flow transition add --workflow "需求分析流程" --from "分析需求" --to "编写PRD"
```

#### 1.4 查看工作流

```bash
# 查看工作流列表
vc flow list

# 查看工作流详情
vc flow show "需求分析流程"
```

### 2. 执行工作流

#### 2.1 启动工作流会话

```bash
# 启动新会话
vc flow run --workflow "需求分析流程" --name "产品A需求分析"

# 指定阶段启动
vc flow run --workflow "需求分析流程" --stage "收集需求" --name "产品A需求分析"
```

#### 2.2 查看会话状态

```bash
# 查看所有会话
vc flow session list

# 查看特定会话
vc flow session show "产品A需求分析"

# 查看当前会话
vc flow session current
```

#### 2.3 阶段操作

```bash
# 切换到下一阶段
vc flow next --session "产品A需求分析"

# 完成当前阶段
vc flow complete --session "产品A需求分析"

# 退回到上一阶段
vc flow back --session "产品A需求分析"
```

#### 2.4 上下文管理

```bash
# 查看会话上下文
vc flow context --session "产品A需求分析"

# 更新会话上下文
vc flow context update --session "产品A需求分析" --key "product_name" --value "产品A"
```

## 开发集成

### 1. 模型使用

#### 1.1 创建工作流

```python
from src.models.db import Stage, Transition, WorkflowDefinition
from src.db.repositories import StageRepository, TransitionRepository, WorkflowDefinitionRepository
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

def create_workflow(session: Session, name: str, description: str) -> WorkflowDefinition:
    # 创建工作流定义
    workflow_repo = WorkflowDefinitionRepository(session)
    workflow_data = {
        "id": f"wfd_{uuid.uuid4().hex[:8]}",
        "name": name,
        "description": description,
        "type": "custom",
        "stages_data": [],  # 初始为空，后续添加阶段定义
        "source_rule": None
    }
    workflow = workflow_repo.create(workflow_data)

    # 创建阶段
    stage_repo = StageRepository(session)
    stage1 = stage_repo.create({
        "id": f"stage_{uuid.uuid4().hex[:8]}",
        "workflow_id": workflow.id,
        "name": "第一阶段",
        "description": "开始阶段",
        "order_index": 0,
        "checklist": ["任务1", "任务2"],
        "is_end": False
    })

    stage2 = stage_repo.create({
        "id": f"stage_{uuid.uuid4().hex[:8]}",
        "workflow_id": workflow.id,
        "name": "第二阶段",
        "description": "中间阶段",
        "order_index": 1,
        "checklist": ["任务3", "任务4"],
        "is_end": False
    })

    stage3 = stage_repo.create({
        "id": f"stage_{uuid.uuid4().hex[:8]}",
        "workflow_id": workflow.id,
        "name": "第三阶段",
        "description": "结束阶段",
        "order_index": 2,
        "checklist": ["任务5", "任务6"],
        "is_end": True
    })

    # 创建转换
    transition_repo = TransitionRepository(session)
    transition_repo.create({
        "id": f"trans_{uuid.uuid4().hex[:8]}",
        "workflow_id": workflow.id,
        "from_stage": stage1.id,
        "to_stage": stage2.id,
        "condition": "",
        "description": "第一阶段到第二阶段的转换"
    })

    transition_repo.create({
        "id": f"trans_{uuid.uuid4().hex[:8]}",
        "workflow_id": workflow.id,
        "from_stage": stage2.id,
        "to_stage": stage3.id,
        "condition": "",
        "description": "第二阶段到第三阶段的转换"
    })

    return workflow
```

#### 1.2 执行工作流

```python
from src.models.db import FlowSession, StageInstance, WorkflowDefinition
from src.db.repositories import FlowSessionRepository, StageInstanceRepository, WorkflowDefinitionRepository, StageRepository
from datetime import datetime
import uuid

def execute_workflow(session: Session, workflow_id: str, session_name: str) -> FlowSession:
    # 创建工作流会话
    session_repo = FlowSessionRepository(session)
    flow_session = session_repo.create({
        "id": f"session_{uuid.uuid4().hex[:8]}",
        "workflow_id": workflow_id,
        "name": session_name,
        "status": "ACTIVE",
        "context": {}
    })

    # 获取工作流定义
    workflow_repo = WorkflowDefinitionRepository(session)
    workflow = workflow_repo.get_by_id(workflow_id)

    # 获取工作流的第一个阶段
    stage_repo = StageRepository(session)
    stages = stage_repo.get_by_workflow_id(workflow_id)
    first_stage = min(stages, key=lambda s: s.order_index)

    # 创建第一个阶段实例
    stage_instance_repo = StageInstanceRepository(session)
    stage_instance = stage_instance_repo.create({
        "id": f"si_{uuid.uuid4().hex[:8]}",
        "session_id": flow_session.id,
        "stage_id": first_stage.id,
        "name": first_stage.name,
        "status": "ACTIVE",
        "started_at": datetime.utcnow(),
        "completed_items": [],
        "context": {},
        "deliverables": {}
    })

    # 更新会话当前阶段
    flow_session.current_stage_id = first_stage.id
    session.commit()

    return flow_session
```

### 2. 扩展工作流系统

#### 2.1 添加自定义阶段类型

创建特定领域的阶段类型：

```python
# 在Stage模型中添加type字段
type = Column(String, nullable=True)  # 阶段类型：requirements, design, develop, test 等

# 根据类型加载不同的默认配置
def load_stage_config(stage_type: str) -> Dict[str, Any]:
    """根据阶段类型加载配置"""
    if stage_type == "requirements":
        return {
            "checklist": [
                "收集需求",
                "分析需求",
                "确定优先级",
                "创建需求文档"
            ],
            "deliverables": [
                "需求文档",
                "用户故事"
            ]
        }
    elif stage_type == "design":
        return {
            "checklist": [
                "创建线框图",
                "设计UI",
                "评审设计"
            ],
            "deliverables": [
                "UI设计稿",
                "原型图"
            ]
        }
    # 其他类型...
    return {"checklist": [], "deliverables": []}
```

#### 2.2 添加自定义转换条件

实现复杂的转换条件评估：

```python
def evaluate_transition_condition(transition: Transition, context: Dict[str, Any]) -> bool:
    """评估转换条件是否满足

    Args:
        transition: 转换对象
        context: 上下文数据

    Returns:
        条件是否满足
    """
    if not transition.condition:
        return True

    try:
        # 简单的条件格式：key=value
        conditions = [c.strip() for c in transition.condition.split(',')]
        for condition in conditions:
            if '=' in condition:
                key, value = condition.split('=')
                key = key.strip()
                value = value.strip()

                if key not in context:
                    return False

                if str(context[key]) != value:
                    return False

        return True
    except Exception as e:
        logger.error(f"条件评估错误: {str(e)}")
        return False
```

## 最佳实践

### 1. 工作流设计原则

1. **单一职责**：每个阶段应专注于一个明确的目标
2. **明确定义交付物**：每个阶段应明确定义预期交付物
3. **合理设置检查项**：为每个阶段设置清晰的检查项列表
4. **设计适当粒度**：阶段不宜过大或过小，保持合适粒度
5. **明确转换条件**：阶段间转换条件应明确可执行

### 2. 性能优化

1. **批量操作**：处理大量阶段或转换时，使用批量操作
2. **惰性加载**：适当使用SQLAlchemy的惰性加载功能
3. **缓存热点数据**：缓存频繁访问的工作流定义
4. **分页查询**：查询大量数据时使用分页
5. **异步处理**：长时间操作使用异步处理

### 3. 安全考虑

1. **权限控制**：实施适当的访问控制机制
2. **输入验证**：验证所有用户输入
3. **审计日志**：记录关键操作的审计日志
4. **数据隔离**：确保不同工作流会话之间的数据隔离

## 故障排除

### 常见问题

1. **会话状态异常**：检查当前阶段是否存在及其状态
2. **转换失败**：检查转换条件和源/目标阶段是否存在
3. **数据不一致**：检查事务是否正确提交
4. **性能问题**：检查数据库查询优化和索引

### 诊断命令

```bash
# 验证工作流结构
vc flow validate <workflow_id>

# 检查会话状态
vc flow session debug <session_id>

# 显示详细日志
vc flow --verbose <command>
```

## 后续开发计划

1. **可视化编辑器**：提供工作流可视化设计界面
2. **条件表达式**：支持更复杂的转换条件表达式
3. **并行阶段**：支持并行执行的阶段
4. **子工作流**：支持工作流嵌套
5. **版本控制**：工作流定义的版本管理
