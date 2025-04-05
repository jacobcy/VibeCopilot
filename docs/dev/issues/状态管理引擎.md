好的，现在我们来设计一个更具体的方案，明确使用本地 SQLite 记录 Agent 执行状态，并通过适配器模式（Adapter）与 GitHub Project 和 n8n Workflow 集成。这个方案在 MVP 的基础上增加了与外部系统的集成，使其更接近一个完整的自动化流程。

**核心架构:**

1. **本地 SQLite 状态库 (`agent_status.db`):** 作为 Agent 执行状态的**详细记录中心 (Source of Truth for Execution Status)**。
2. **Agent (`basic_agent.py`):**
    * 负责执行任务。
    * **核心职责:** 在执行的关键节点（开始、生成计划、等待审批、步骤执行、完成、失败）**更新本地 SQLite 状态库**。
    * **不直接**调用 GitHub 或 n8n API。
3. **状态同步适配器 (`status_sync_adapter.py`):**
    * **目的:** 解耦 Agent 核心逻辑与外部系统的状态同步。
    * **触发方式:**
        * **方式一 (推荐 MVP):** 作为一个**独立的 Python 脚本**，可以被 n8n 工作流调用，或者定期运行。
        * **方式二 (更紧密，但耦合度高):** Agent 在更新 SQLite 后，通过一个简单的消息队列或事件机制触发适配器。
    * **功能:**
        * 读取本地 SQLite 中**状态发生变化**的任务。
        * 根据预定义的映射规则，调用相应的外部系统适配器（GitHub Adapter, n8n Adapter）来同步状态。
4. **GitHub 适配器 (`github_adapter.py`):**
    * **目的:** 封装与 GitHub API (特别是 Projects 和 Issues) 的交互。
    * **功能:** 提供函数如 `update_issue_status(issue_id, status_label)`, `add_comment(issue_id, comment)`, `get_issue_details(issue_id)` 等。
    * **使用库:** `PyGithub` 或 `requests`。
5. **n8n 适配器 (`n8n_adapter.py`):**
    * **目的:** 封装与 n8n Webhook 或 API 的交互。
    * **功能:** 提供函数如 `trigger_workflow(workflow_url, payload)`, `get_workflow_status(execution_id)` 等。
    * **使用库:** `requests`。

**组件交互流程 (示例: 执行一个 Issue 任务):**

1. **触发 (n8n):**
    * n8n 工作流检测到 GitHub Issue `PROJ-123` 被标记为 "Ready for Dev"。
    * n8n 工作流触发 Agent 执行，可能通过执行 Shell 命令：`python basic_agent.py --issue_id PROJ-123 --command "/implement_feature"`。
2. **Agent 启动 & 初始状态:**
    * `basic_agent.py` 启动。
    * Agent **写入/更新 `agent_status.db`**: 设置 `issue_id='PROJ-123'`, `status='INITIALIZING'`, `command='/implement_feature'`, etc.
3. **Agent 请求计划:**
    * Agent 调用 `cddrg_engine.generate_action_plan()`。
    * Agent **更新 `agent_status.db`**: `status='GENERATING_PLAN'`.
    * `cddrg_engine` 返回行动计划。
    * Agent **更新 `agent_status.db`**: `status='PENDING_APPROVAL'`, `action_plan_json='...'`.
4. **状态同步 -> GitHub & n8n (通过 `status_sync_adapter`):**
    * n8n 工作流在触发 Agent 后，可能会调用 `python status_sync_adapter.py --issue_id PROJ-123` (或者适配器定期轮询)。
    * `status_sync_adapter.py` 读取 `agent_status.db` 中 `PROJ-123` 的状态 (`PENDING_APPROVAL`)。
    * 适配器调用 `github_adapter.update_issue_status('PROJ-123', 'Status:PendingApproval')`。
    * 适配器调用 `github_adapter.add_comment('PROJ-123', '行动计划已生成，请审批: [链接或摘要]')`。
    * 适配器调用 `n8n_adapter.trigger_workflow('n8n_approval_workflow_url', {'issue_id': 'PROJ-123', 'plan': ...})`，启动审批流程。
5. **人类审批 (n8n):**
    * n8n 的审批工作流启动，可能通过 Slack/Email 发送计划给负责人。
    * 负责人审批通过。
    * n8n 审批工作流接收到结果。
6. **触发 Agent 继续执行 (n8n -> Agent):**
    * n8n 审批工作流执行 Shell 命令：`python basic_agent.py --issue_id PROJ-123 --action approved` (或通过其他机制通知 Agent)。
7. **Agent 继续执行 & 更新状态:**
    * `basic_agent.py` 收到 `approved` 信号。
    * Agent **更新 `agent_status.db`**: `status='RUNNING'`, `current_step_index=0`.
    * Agent 开始执行计划中的步骤。
    * 每完成一步，Agent **更新 `agent_status.db`**: `current_step_index+=1`, `last_log_message='...'`.
8. **状态同步 -> GitHub (通过 `status_sync_adapter`):**
    * 适配器再次被调用或轮询。
    * 读取到状态 `RUNNING`。
    * 调用 `github_adapter.update_issue_status('PROJ-123', 'Status:InProgress')` (移除 PendingApproval 标签)。
    * 调用 `github_adapter.add_comment('PROJ-123', '审批通过，开始执行...')`。
9. **Agent 执行完成/失败 & 更新状态:**
    * Agent 执行完毕。
    * Agent **更新 `agent_status.db`**: `status='SUCCEEDED'` 或 `status='FAILED'`, `last_log_message='...'`.
10. **最终状态同步 -> GitHub & n8n (通过 `status_sync_adapter`):**
    * 适配器读取到最终状态。
    * 调用 `github_adapter.update_issue_status('PROJ-123', 'Status:Done'/'Status:Failed')`。
    * 调用 `github_adapter.add_comment('PROJ-123', '执行完成/失败: [结果摘要/日志链接]')`。
    * (可选) 调用 `n8n_adapter.trigger_workflow('n8n_completion_workflow_url', {'issue_id': 'PROJ-123', 'status': ...})`，触发后续流程（如通知、部署等）。

**SQLite `agent_status.db` Schema (细化):**

```sql
CREATE TABLE IF NOT EXISTS agent_task_status (
    task_run_id TEXT PRIMARY KEY,           -- 唯一执行 ID (UUID 或 时间戳+IssueID)
    issue_id TEXT NOT NULL,                 -- 关联的 GitHub/GitLab Issue ID
    command TEXT NOT NULL,
    parameters TEXT,                        -- JSON
    context TEXT,                           -- JSON
    status TEXT NOT NULL CHECK(status IN (
        'PENDING_START',                    -- 等待 Agent 启动
        'INITIALIZING',                     -- Agent 启动中
        'GENERATING_PLAN',                  -- 正在生成计划
        'PENDING_APPROVAL',                 -- 等待人类批准计划
        'RUNNING',                          -- 正在执行计划
        'PAUSED',                           -- (可选) 执行暂停
        'WAITING_EXTERNAL',                 -- (可选) 等待外部事件
        'SUCCEEDED',                        -- 执行成功
        'FAILED'                            -- 执行失败
    )),
    status_message TEXT,                    -- 状态附加信息 (如失败原因)
    current_step_index INTEGER,
    total_steps INTEGER,
    action_plan_json TEXT,                  -- 生成的行动计划
    execution_log_summary TEXT,             -- 关键执行日志摘要
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_issue_id ON agent_task_status(issue_id);
CREATE INDEX IF NOT EXISTS idx_status ON agent_task_status(status);
```

* **`task_run_id`**: 每次 Agent 执行（即使是针对同一个 Issue 重试）都应该有一个唯一的 ID。
* **`status`**: 定义了更细粒度的状态。
* **`status_message`**: 用于记录失败原因或等待的具体事件。

**适配器实现要点:**

* **`status_sync_adapter.py`:**
  * 需要逻辑来查询 `agent_status.db` 中最近更新或特定状态的记录。
  * 需要定义状态映射：SQLite 状态如何映射到 GitHub 标签/状态以及触发哪个 n8n 工作流。例如：
        ```python
        STATUS_MAP = {
            'PENDING_APPROVAL': {'github_label': 'Status:PendingApproval', 'n8n_workflow': 'approval_workflow'},
            'RUNNING': {'github_label': 'Status:InProgress'},
            'SUCCEEDED': {'github_label': 'Status:Done', 'n8n_workflow': 'completion_workflow'},
            'FAILED': {'github_label': 'Status:Failed', 'n8n_workflow': 'failure_workflow'},
        }
        ```
  * 需要处理错误，例如 GitHub 或 n8n API 调用失败时的重试或记录。
* **`github_adapter.py` & `n8n_adapter.py`:**
  * 封装 API 调用细节，处理认证 (如 GitHub Token, n8n API Key/Webhook Secret)。
  * 提供简洁的接口供 `status_sync_adapter` 调用。

**优点:**

* **关注点分离:** Agent 专注于执行任务和更新本地状态；适配器负责与外部系统同步。
* **本地状态权威:** Agent 的执行状态以本地 SQLite 为准，更可靠，即使外部系统短暂不可用，状态也不会丢失。
* **灵活性:**
  * 可以轻松添加对其他外部系统（如 Jira, Slack）的支持，只需增加新的适配器。
  * 状态同步逻辑集中在 `status_sync_adapter`，易于修改和管理。
  * `status_sync_adapter` 的触发方式可以调整（n8n 调用 vs. 定时任务 vs. 事件驱动）。
* **可测试性:** 可以独立测试 Agent 的核心逻辑（通过 Mock SQLite），以及独立测试每个适配器。

**缺点/Effort:**

* **增加了适配器层:** 需要额外开发 `status_sync_adapter`, `github_adapter`, `n8n_adapter`。这是主要的 effort 增加点。
* **状态同步延迟:** 同步不是实时的（除非使用事件驱动），可能存在短暂的状态不一致。
* **配置复杂性增加:** 需要配置适配器如何连接外部系统、状态如何映射等。

**结论:**

这个方案通过引入适配器层，在保持 Agent 核心逻辑简洁的同时，实现了与 GitHub Project 和 n8n Workflow 的解耦集成。本地 SQLite 作为 Agent 执行状态的中心，提供了可靠性和详细记录。虽然相比纯本地方案增加了开发 effort（主要是适配器），但它构建了一个更健壮、更灵活、更接近实际生产需求的系统架构，为后续扩展和替换外部工具打下了良好基础。这对于一个希望整合外部系统的 MVP 来说，是一个平衡了 effort 和功能的合理选择。
