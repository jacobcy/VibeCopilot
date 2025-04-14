# 实体关系模型说明

本文档描述了VibeCopilot中Story、Task和Session之间的关系模型及其数据结构，以便开发人员和用户更好地理解系统设计。

## 核心实体关系

### 实体关系概述

1. **Story → Task → Session**: 数据模型采用单向关联机制，遵循"从大到小"的自然工作流向：
   - 一个Story可以包含多个Task
   - 一个Task可以关联多个Session
   - 每个Session只专注于一个Task

2. **关系方向**:
   - Task引用Story (`Task.story_id`)
   - Session引用Task (`Session.task_id`)
   - 关系维护在"多"的一方，简化查询和维护

## 实体数据结构

### Story实体

```python
class Story:
    """故事实体模型，代表开发中的用户故事或功能点"""

    id: str              # 唯一标识符
    title: str           # 故事标题
    description: str     # 详细描述
    epic_id: str         # 所属Epic
    status: str          # 状态：draft, planned, in_progress, completed
    priority: str        # 优先级：low, medium, high, critical
    tasks: List[Task]    # 相关联的任务列表（反向关系）
```

### Task实体

```python
class Task:
    """任务实体模型，代表具体的工作项"""

    id: str              # 唯一标识符
    title: str           # 任务标题
    description: str     # 详细描述
    status: str          # 状态：todo, in_progress, done
    priority: str        # 优先级：low, medium, high
    estimated_hours: int # 估计工时
    is_completed: bool   # 是否完成
    story_id: str        # 关联的故事ID（可选）
    assignee: str        # 负责人
    labels: List[str]    # 标签列表
    created_at: str      # 创建时间
    updated_at: str      # 更新时间
    completed_at: str    # 完成时间

    # 关系
    story: Story                    # 所属故事（外键关系）
    flow_sessions: List[FlowSession] # 关联的工作流会话（反向关系）
```

### FlowSession实体

```python
class FlowSession:
    """工作流会话实体模型，代表执行工作流的实例"""

    id: str              # 唯一标识符
    workflow_id: str     # 关联的工作流定义ID
    name: str            # 会话名称
    status: str          # 状态：ACTIVE, PAUSED, COMPLETED, ABORTED
    created_at: datetime # 创建时间
    updated_at: datetime # 更新时间
    current_stage_id: str # 当前阶段ID
    completed_stages: List[str] # 已完成阶段ID列表
    context: Dict        # 会话上下文数据
    task_id: str         # 关联的任务ID

    # 关系
    task: Task                      # 关联的任务（外键关系）
    workflow_definition: WorkflowDefinition  # 工作流定义
    stage_instances: List[StageInstance]    # 阶段实例
```

## 关联关系的使用场景

### 1. Story → Task关系

- **自然工作分解**：故事是需求层面的功能点，分解为具体的工作任务
- **工作跟踪**：通过故事了解相关任务的完成进度
- **路线图整合**：任务通过故事关联到更大的史诗(Epic)和路线图

### 2. Task → Session关系

- **专注原则**：每个会话专注于完成一个特定任务
- **工作流跟踪**：一个任务可能需要多次不同类型的工作流程才能完成
- **进度可视化**：通过查看任务关联的会话，了解具体工作进度和方法

## 查询模式

### 查询Task关联的Story

```python
# 获取任务关联的故事
task = task_repository.get_by_id("task_123")
story = task.story  # 直接通过关系获取

# 获取故事下的所有任务
story = story_repository.get_by_id("story_456")
tasks = task_repository.get_by_story_id(story.id)
```

### 查询Session关联的Task

```python
# 获取会话关联的任务
session = session_repository.get_by_id("session_789")
task = session.task  # 直接通过关系获取

# 获取任务的所有会话
task = task_repository.get_by_id("task_123")
sessions = session_repository.get_by_task_id(task.id)
```

## 命令行使用示例

```bash
# 创建关联到故事的任务
vc task create --title "实现登录功能" --link-story story_123

# 查看特定故事下的所有任务
vc task list --story story_123

# 创建专注于特定任务的会话
vc flow session create --flow auth_flow --task task_456

# 查看任务相关的会话
vc task show task_456  # 会显示关联的会话

# 查看会话详情（包括它正在处理的任务）
vc flow session show session_789
```

## 设计原则

1. **单向关联**：避免双向关系复杂性，使数据流向清晰
2. **专注原则**：每个Session只专注于一个Task，保持工作流程的清晰度
3. **灵活性**：一个Task可以有多个Session，支持多种工作流程组合
4. **可追溯性**：通过关系链可以从Session追溯到Task和Story

---

通过这种关系模型，VibeCopilot能够清晰地管理开发工作流程，从需求（Story）到具体工作（Task），再到实际执行过程（Session），形成完整的工作链条。
