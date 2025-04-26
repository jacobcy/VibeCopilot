
**当前状态剖析 (我们刚刚修复后的状态):**

1. **定义存储:** 工作流的完整定义（元数据、阶段列表、转换列表）被序列化成一个 JSON 对象，存储在 `workflow_definitions` 表的 `stages_data` 列中。列名 `stages_data` 具有误导性。
2. **独立表未使用:** 数据库中存在独立的 `stages` 和 `transitions` 表，但它们是空的，工作流定义不使用它们。SQLAlchemy 的 `relationship` 指向这些空表。
3. **实例状态:** `flow_sessions` 表通过 `current_stage_id` 跟踪当前阶段。`StageInstance` 模型和表存在，但并未在核心的 `context` 和 `next` 导航逻辑中被积极使用来记录或查询执行历史。`FlowSession.context` 存储任意 JSON 数据。
4. **`context` 命令:** 现在能够通过解析 `workflow.stages_data` 字典，找到当前阶段的 *定义*（名称、描述等），并结合 `FlowSession` 的元数据和 `context` 字段内容进行显示。它**无法**显示实际的执行历史（如当前阶段何时开始，之前的阶段结果）。
5. **`next` 命令:** 现在能够通过解析 `workflow.stages_data` 字典中的 `'transitions'` 列表，找到从当前阶段出发的转换规则，并返回下一个可能阶段的 *定义*。它**无法**处理依赖于历史执行状态的条件转换。
6. **问题隐患:**
    * **数据模型混乱:** 定义与实例状态界限不清，`stages_data` 列名不副实，空表和无效关系增加了理解成本。
    * **缺乏历史:** 无法追踪会话的实际执行路径、各阶段耗时、状态变化。
    * **功能受限:** 无法实现条件路由、并行处理、重试等高级工作流功能。
    * **维护困难:** 修改工作流定义（例如增删阶段）需要复杂地更新 `stages_data` JSON，且难以保证数据一致性。对 JSON 内部结构的查询和索引效率低下。
    * **版本问题:** 如果修改了工作流定义，所有引用该定义的活动会话可能会行为异常，因为它们没有绑定到特定的定义版本。

**目标架构 (最佳实践):**

为了构建一个健壮、可维护、可扩展的工作流引擎，数据库设计应遵循以下原则：

1. **定义与实例分离 (Normalization):**
    * **定义 (模板):** 使用规范化的表结构存储工作流的蓝图。
        * `workflow_definitions`: 存储核心元数据 (id, name, description, *latest\_version*)。
        * `workflow_versions`: 存储每个版本的详细信息 (id, workflow\_definition\_id, version\_string, created\_at, *is\_active*)。 **关键：引入版本概念。**
        * `stages`: 存储阶段定义 (id, workflow\_version\_id, name, description, type, `is_start_stage`, `is_end_stage`, 其他配置如 checklist 模板)。 **关联到特定版本。**
        * `transitions`: 存储转换定义 (id, workflow\_version\_id, name, from\_stage\_id, to\_stage\_id, condition, action)。 **关联到特定版本和 stages。**
    * **实例 (执行):** 记录具体的执行过程。
        * `flow_sessions`: 存储会话信息 (id, name, *workflow\_version\_id* (链接到运行的具体版本!), task\_id, status, start\_time, end\_time, context (通用上下文))。
        * `stage_instances`: 记录每个阶段的执行情况 (id, flow\_session\_id, stage\_id (链接到阶段定义), status ('pending', 'active', 'completed', 'failed', 'skipped'), start\_time, end\_time, result\_context (该实例的特定结果))。 **核心：追踪历史。**
        * **(可选)** `transition_instances`: 记录实际执行的转换 (id, flow\_session\_id, transition\_id, timestamp)。

2. **明确职责:**
    * **`context` 命令:** 主要职责是展示**当前执行状态**。
        * 查询 `flow_sessions` 获取当前会话信息。
        * 查询 `stage_instances` 找到当前会话的 `status='active'` 的实例（或最新完成的实例）。
        * 显示该 `StageInstance` 的信息（状态、开始时间、结果等）。
        * 关联查询 `stages` 表获取该阶段的静态定义（名称、描述）。
        * 可以补充显示 `FlowSession.context` 中的通用信息和关联任务。
        * 可选：提供 `--history` 参数查询并展示该会话所有 `StageInstance` 记录。
    * **`next` 命令:** 主要职责是根据**当前已完成状态**和**定义**预测下一步。
        * 找到当前会话最新 `status='completed'` 的 `StageInstance`，获取其 `stage_id`。
        * 查询 `transitions` 表，查找 `workflow_version_id` 匹配且 `from_stage_id` 匹配的转换规则。
        * （关键）评估每个找到的 `transition.condition` 是否满足。条件评估可能需要访问 `FlowSession.context` 和相关的 `StageInstance.result_context`。
        * 对于条件满足的转换，获取其 `to_stage_id`。
        * 查询 `stages` 表获取这些目标阶段的定义。
        * 返回这些有效的目标阶段定义列表。

3. **核心流程驱动:**
    * **`flow run`:**
        * 创建 `FlowSession` 记录，关联到最新的（或指定的）`workflow_version_id`。
        * 查询 `stages` 表找到该版本的起始阶段 (`is_start_stage=True`)。
        * 创建第一个 `StageInstance`，状态为 'active'，记录 `start_time`。
        * 更新 `FlowSession.current_stage_id`（或者这个字段可以去掉，完全依赖 active 的 StageInstance）。
    * **推进流程 (例如 `flow complete_stage` 或内部逻辑):**
        * 将当前 'active' 的 `StageInstance` 标记为 'completed'，记录 `end_time` 和 `result_context`。
        * 执行 `next` 命令的核心逻辑（查找匹配转换、评估条件）。
        * 如果找到唯一的、条件满足的下一阶段：创建新的 `StageInstance`，状态设为 'active'。
        * 如果找到多个或零个：可能需要用户交互或进入特定状态。

**重构建议:**

1. **数据库迁移:** 这是最关键的一步。
    * 设计新的规范化表结构（如上所述）。
    * 编写迁移脚本（推荐 Alembic）：
        * 创建新表 (`workflow_versions`, `stages`, `transitions`, `stage_instances` 等）。
        * 解析 `workflow_definitions.stages_data` JSON 数据。
        * 为每个解析出的定义创建一个 `workflow_versions` 记录 (v1.0)。
        * 将解析出的阶段和转换数据分别插入新的 `stages` 和 `transitions` 表，并关联到对应的 `workflow_version_id`。
        * 更新 `flow_sessions` 表，添加 `workflow_version_id` 列，并尝试根据 `workflow_id` 填充（指向 v1.0）。
        * （难点）尝试根据 `FlowSession.context` 或日志为现有会话回填 `stage_instances`。如果太复杂，可以将现有会话标记为 legacy 或保持原样。
        * **移除 `stages_data` 列。**
2. **代码重构:**
    * 重写 Repositories (`WorkflowDefinitionRepository`, `StageRepository`, `TransitionRepository`, `FlowSessionRepository`) 以适应新表结构。创建 `StageInstanceRepository`。
    * 重写 `FlowSessionManager` 的核心方法 (`create_session`, `get_next_stages`, `get_session_context`, `get_session_progress`, 以及状态推进逻辑) 以使用新的表和 `StageInstance`。
    * 重写 `flow_info.py` 中的 `handle_context_subcommand`, `handle_next_subcommand` 以及它们的格式化函数，以反映新的数据来源和结构。
    * 确保工作流定义的创建/更新流程现在操作的是规范化的表，并处理版本。

**总结 (架构师视角):**

当前的 JSON 嵌入方案是一个权宜之计，已经暴露了其局限性。为了系统的长期健康、可维护性和功能扩展性，**强烈建议进行数据库结构的规范化重构**。

* **分离定义与实例:** 这是核心，使得模型清晰，易于管理。
* **引入版本控制:** 解决定义变更影响运行中实例的问题。
* **使用 `StageInstance`:** 提供必要的执行历史和状态追踪，是实现健壮 `context` 和条件 `next` 的基础。

虽然重构工作量较大，但这是构建可靠工作流引擎的必经之路。它可以消除当前数据模型的混乱，为未来添加更复杂的工作流逻辑和分析功能铺平道路。现在投入时间进行重构，将避免未来在充满技术债的系统上进行更痛苦的修改。
