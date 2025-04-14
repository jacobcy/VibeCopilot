# FlowSession 数据模型实现总结

## 数据模型结构

1. **FlowSession（工作流会话）**:
   - 核心字段：id、workflow_id、name、status、current_stage_id、completed_stages、context、task_id、flow_type、is_current
   - 表示一个正在执行的工作流实例，可以跟踪其状态、上下文和进度

2. **StageInstance（阶段实例）**:
   - 核心字段：id、session_id、stage_id、name、status、started_at、completed_at、completed_items、context、deliverables
   - 表示工作流中特定阶段的执行实例，记录执行状态和结果

## 技术架构

1. **数据访问层**:
   - 采用仓库模式（Repository Pattern）
   - 基础仓库类：`Repository<T>`（通用CRUD操作）
   - 实体仓库：`FlowSessionRepository`、`StageInstanceRepository`
   - 使用SQLAlchemy ORM实现数据访问

2. **业务逻辑层**:
   - 核心管理类：`FlowSessionManager`
   - 采用Mixin设计模式划分功能：
     - `SessionCRUDMixin`：实现CRUD操作
     - `SessionStateMixin`：管理会话状态
     - `SessionContextMixin`：管理会话上下文
     - `CurrentSessionMixin`：管理当前会话
   - 补充管理类：`StageInstanceManager`（管理阶段实例）

3. **API设计**:
   - 使用单例模式包装`FlowSessionManager`实例
   - 通过全局函数（如`create_session`）提供更简洁的API接口
   - 支持ID或名称两种方式查找会话

## 业务功能

1. **会话管理**:
   - 创建、查询、更新、删除会话
   - 状态管理：启动、暂停、恢复、完成、关闭
   - 当前会话管理：获取、设置、切换

2. **上下文管理**:
   - 获取、更新、清除会话上下文
   - 上下文数据存储为JSON格式

3. **阶段管理**:
   - 获取会话阶段列表
   - 获取会话第一个阶段
   - 获取进度信息
   - 设置当前阶段
   - 获取可能的下一阶段

4. **与其他模块集成**:
   - 与任务系统集成（通过task_id）
   - 与工作流定义系统集成（通过workflow_id）

该实现提供了一个灵活、可扩展的工作流会话管理系统，能够跟踪复杂工作流的执行状态。
