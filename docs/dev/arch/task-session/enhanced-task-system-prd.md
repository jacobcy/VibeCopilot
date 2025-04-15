# 增强型任务管理系统 PRD

## 1. 概述

### 1.1 背景

目前VibeCopilot的任务管理系统提供了基本的任务创建、查看和更新功能，但在任务执行过程中缺乏结构化的日志记录、参考资料管理和与工作流会话(flow-session)的深度集成。当前方案存在以下问题：

1. 任务的执行日志分散，没有统一的存储和查看机制
2. 任务相关的参考资料没有结构化管理
3. 任务与工作流会话的关联性不够紧密
4. 缺乏对任务历史记录和内存的管理
5. 缺少便捷的任务信息摘要和检索能力

### 1.2 目标

增强VibeCopilot的任务管理系统，使其能够：

1. 提供结构化的任务日志记录和查看机制
2. 支持任务相关参考资料的智能管理
3. 深度集成任务与工作流会话
4. 固化任务相关内容到专门的目录结构，便于检索
5. 利用现有命令实现更智能的任务管理
6. 整合记忆(memory)功能，为任务提供智能资料检索和存储
7. 简化用户操作，提供直观的任务管理体验

## 2. 需求详情

### 2.1 任务日志记录与查看

#### 2.1.1 日志记录

- 任务创建时自动在`.ai/tasks/<task_id>`目录下创建日志文件，**固定路径**为`.ai/tasks/<task_id>/task.log`
- 自动记录任务的创建、更新、评论等事件
- 支持记录任务执行过程中的关键操作
- 日志采用Markdown格式，便于查看和解析

#### 2.1.2 日志查看

- 通过现有命令查看任务日志：`vc task show <task_id> --log`
- 日志内容直接呈现，无需额外命令
- 日志路径在任务详情中显示，便于访问

### 2.2 任务参考资料管理

#### 2.2.1 参考资料关联

- 使用memory功能自动搜索相关资料
- 如果未找到相关资料，自动创建新的memory_item存储该内容
- 通过`vc task update <task_id> --ref`命令添加参考资料

#### 2.2.2 参考资料查看

- 通过`vc task show <task_id> --ref`查看任务关联的所有参考资料
- 参考资料以摘要形式展示（摘要由memory在存储时自动生成），便于快速了解内容

### 2.3 任务与工作流会话集成

#### 2.3.1 共享日志

- 工作流会话能够访问并更新关联任务的日志
- 会话日志自动同步到任务日志
- 任务视图能够展示关联会话的活动

#### 2.3.2 上下文共享

- 任务详情作为会话的上下文传递
- 会话能够访问任务的参考资料
- 会话状态变更可以同步到任务状态

### 2.4 任务内容固化

#### 2.4.1 目录结构

```
.ai/
  tasks/
    <task_id>/
      task.log         # 主日志文件（固定路径）
      metadata.json    # 任务元数据（包含关联的memory_item引用）
```

#### 2.4.2 内容固化机制

- 任务创建时**自动**初始化目录结构
- 任务更新、评论等操作自动更新日志
- 所有更改实时记录，确保数据一致性

### 2.5 任务创建信息增强

- 创建任务时自动提示日志和参考资料的位置
- 智能推断任务类型，提供相关上下文
- 自动从相似任务获取参考信息

### 2.6 记忆功能集成

#### 2.6.1 智能资料管理

- 使用memoryManager中的memory功能在文档库中搜索已有资料
- 如无相关资料，自动创建新的memory_item
- 摘要在memory_item创建时自动生成，无需额外处理

#### 2.6.2 知识检索

- 将任务内容索引到memoryManager系统中
- 支持跨任务的知识检索
- 为新任务提供相关历史任务的参考

### 2.7 命令行界面设计

```
# 创建任务（自动在.ai/tasks生成对应目录结构）
vc task create --title=<title> --ref=<file_path>

# 显示任务概要信息
vc task show <task_id>

# 显示任务日志信息
vc task show <task_id> --log

# 显示任务参考资料（memory提供摘要）
vc task show <task_id> --ref

# 更新任务信息
vc task update <task_id>

# 添加任务参考资料（memory首先查找是否存在，不存在则存储）
vc task update <task_id> --ref=<file_path>
```

## 3. 数据模型

### 3.1 扩展Task模型

```python
class Task(Base):
    # 现有字段...

    # 新增字段
    log_path = Column(String, default=lambda task_id: f".ai/tasks/{task_id}/task.log")  # 日志文件固定路径
    memory_items = Column(JSON, default=list)  # 存储关联的memory_item ID列表
    has_summary = Column(Boolean, default=False)  # 是否有摘要
    last_update_time = Column(String, nullable=True)  # 最后更新时间
```

### 3.2 使用现有MemoryItem模型

```python
# 不创建新的TaskReference模型，而是使用现有的MemoryItem模型关联任务
# MemoryItem模型由memoryManager负责管理
# 任务和MemoryItem通过关联表或索引进行关联
```

## 4. API和服务设计

### 4.1 简化TaskService

```python
class TaskService:
    """任务服务（集成日志功能，协调与memoryManager的交互）"""

    def create_task(self, title: str, description: Optional[str] = None, ref_path: Optional[str] = None) -> Task:
        """创建任务（自动创建目录结构，可选关联参考文件）"""

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Task:
        """更新任务信息"""

    def add_reference(self, task_id: str, file_path: str) -> bool:
        """添加参考资料（调用memoryManager）"""

    def get_task(self, task_id: str, include_log: bool = False, include_refs: bool = False) -> Dict[str, Any]:
        """获取任务信息（可选择包含日志和参考资料）"""

    def add_log_entry(self, task_id: str, content: str) -> bool:
        """添加日志条目"""
```

### 4.2 利用MemoryManager服务

```python
# TaskService将调用MemoryManager的以下功能：
# 1. 查找相关参考资料
# 2. 创建新的memory_item
# 3. 获取参考资料的摘要
# 这些功能由现有memoryManager提供，不需要在task中实现
```

### 4.3 集成FlowSessionService

```python
class FlowSessionTaskIntegration:
    """流程会话和任务集成服务"""

    def link_session_to_task(self, session_id: str, task_id: str) -> bool:
        """关联会话到任务"""

    def sync_session_logs_to_task(self, session_id: str) -> bool:
        """同步会话日志到任务"""
```

## 5. 实现计划

### 5.1 阶段一：基础自动化

1. 实现任务创建时自动生成目录结构（固定路径）
2. 扩展Task模型，添加必要字段
3. 实现基本的日志自动记录机制

### 5.2 阶段二：命令增强

1. 增强`task show`命令支持不同视图（概要、日志、参考资料）
2. 增强`task update`命令支持添加参考资料
3. 实现与memoryManager的集成

### 5.3 阶段三：智能集成

1. 实现与Flow Session系统的集成
2. 优化参考资料检索和推荐机制
3. 完善任务与memory_item的关联机制

### 5.4 阶段四：测试与优化

1. 编写单元测试和集成测试
2. 进行用户体验测试和优化
3. 完善文档和使用示例

## 6. 预期效果

实现该系统后，VibeCopilot的任务管理能力将得到显著增强：

1. **简洁直观**：使用现有命令完成复杂功能，降低学习成本
2. **自动化**：任务创建自动生成固定路径的目录结构，无需手动操作
3. **智能化**：通过memoryManager自动检索相关资料，为任务提供上下文支持
4. **集成化**：与工作流会话紧密集成，提供连贯体验
5. **高效率**：简化操作流程，统一数据源，提高开发效率

这些改进使VibeCopilot能够更加智能地辅助开发过程，特别是在处理复杂任务时，不需要记忆复杂命令，系统会智能地提供必要的上下文和支持。
