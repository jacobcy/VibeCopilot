# 开发计划: Task 命令系统集成与概念对齐

**1. 目标**

* 实现 VibeCopilot 的 `task` 命令系统，使其成为核心的任务管理单元。
* 确保 `task` 命令遵循 `@command-list.md` 的标准化设计和 Agent 友好原则。
* 设计 `task` 与 Roadmap 的关联机制，允许任务独立存在（快速任务）或关联到 Roadmap Story/Epic。
* 将 `task` 系统无缝集成到 Workflow 执行流程中，利用 Workflow 指导任务执行。
* 对齐并明确 `task`, `roadmap`, `workflow`, `status` 之间的概念和关系，确保 `status` 命令能准确反映各方面状态。
* 实现 `task` 与 GitHub Issues 的基本关联（链接为主，非实时同步）。

**2. 范围**

* **包含:**
  * `task` 命令的核心 CRUD 操作 (`list`, `show`, `create`, `update`, `delete`)。
  * `task` 的评论功能 (`task comment`)。
  * `task` 与 Roadmap、Workflow Session/Stage Instance、GitHub Issue/PR/Commit 的关联/取消关联机制 (`task link`, `task create/update` 中的关联选项)。
  * 修改 `flow context` 命令，使其输出当前阶段相关的 `task` 列表。
  * 修改 `roadmap show` 和 `roadmap status` 以反映关联 `task` 的信息。
  * 实现 `status task` 子命令，并更新 `status show` 以包含任务概览。
  * 定义清晰的 Task、Roadmap、Workflow、Status 概念关系。
  * 数据库模型和 Schema 调整以支持 `task` 及其关联。
* **排除:**
  * `task` 与 GitHub Issues 的实时双向同步。
  * 复杂的状态转换工作流（Task 状态转换逻辑保持简单）。
  * 任务依赖关系管理（A 任务阻塞 B 任务）。
  * 前端 UI 集成（仅关注后端 CLI 命令）。

**3. 核心设计**

* **Task 作为核心单元:**
  * `task` 是最小粒度的可跟踪工作项，对标 GitHub Issue。
  * 包含 `id`, `title`, `description`, `status`, `assignee`, `labels`, `comments`, 时间戳等。
* **处理快速任务 (独立任务):**
  * `task` 实体中的 `roadmap_link` 字段 **是可选的**。
  * `task create` 命令 **不强制** 要求关联 Roadmap 项。
  * 用户可以创建不属于任何 Roadmap Story/Epic 的独立任务，用于处理临时的、计划外的或与主要 Roadmap 无关的工作。
  * `task list` 可以通过参数过滤显示所有任务、仅关联 Roadmap 的任务或仅独立任务。
* **概念对齐与关系:**
  * **Roadmap:** **战略规划层** - 定义项目的目标和方向 (Epics, Stories)。回答 "我们要做什么？" 和 "为什么？"。
  * **Workflow:** **过程执行层** - 定义完成工作的标准化流程和阶段 (dev:story, dev:coding 等)。回答 "我们如何做？"。`flow session` 是流程的一次具体执行实例。
  * **Task:** **战术执行层** - 定义具体要完成的工作项。回答 "具体执行哪个工作？"。任务在 Workflow 定义的流程中被执行，以达成 Roadmap 的目标。
  * **Status (命令):** **统一视图层** - 提供对上述各层状态的聚合展示。
    * `status roadmap`: 展示 Roadmap 规划的完成进度（基于 Story/Epic 状态，可能间接参考其下 Task）。
    * `status flow`: 展示当前有哪些 Workflow Session 在运行，以及它们进行到哪个阶段。
    * `status task`: 展示当前所有 Task 的分布情况（如按状态、负责人统计）。
    * `status show`: 提供项目整体快照，可能包含当前项目阶段 (`ProjectState`)、活动的 Workflow、任务统计等。
* **Workflow 集成:**
  * Workflow 作为 **指导者/解释器**。
  * `flow run <workflow>:<stage>` 启动或继续一个阶段，准备环境。
  * **关键集成点:** `flow context <workflow_id> <stage_name> [--session=<sid>]` 的输出 `data.context` 中应包含一个 `relevant_tasks` 列表。
    * 此列表包含与当前会话/阶段关联的、状态适合当前处理的 `task` ID 或摘要信息 (例如，对于 `dev:coding` 阶段，列出关联 Story 下状态为 'open' 或 'in_progress' 的 Task)。
  * Agent/用户根据 `flow context` 提供的任务列表，使用 `task show <id>` 获取详情并执行工作。
  * `task update <id> --status=done` 更新任务状态，此状态变化会反映在后续的 `flow context` 或 `flow next` 的推荐中。
* **GitHub 集成:**
  * 采用 **链接优先** 策略。
  * `task` 存储关联的 `github_issue_number`。
  * 通过 `task link` 或 `task create --link-github` 建立关联。
  * `task show` 显示关联的 GitHub Issue 链接。
  * **不进行** 状态或内容的自动同步。

**4. 技术方案**

* **数据模型:**
  * 在数据库中创建 `tasks` 表，包含上述核心字段和关联外键 (`roadmap_item_id`, `workflow_session_id`, `workflow_stage_instance_id`)。
  * 创建 `task_comments` 表。
  * 可能需要在 `roadmap_items`, `workflow_sessions`, `workflow_stage_instances` 表中添加反向关联或调整现有结构。
* **命令实现:**
  * 在 `src/cli/commands/` 下创建 `task/` 目录。
  * 实现 `TaskCommand` 基类及各子命令 (`ListTaskCommand`, `ShowTaskCommand`, etc.)，遵循 `BaseCommand` 结构。
  * 修改 `src/cli/commands/flow/context.py` (或相关文件) 以查询并包含 `relevant_tasks`。
  * 修改 `src/cli/commands/roadmap/show.py` 和 `status.py`。
  * 修改 `src/cli/commands/status/` 下的子命令实现。
* **数据库交互:**
  * 创建或更新 SQLAlchemy 模型。
  * 创建或更新相应的 Repository 类 (`TaskRepository`) 或调整 `DatabaseService`。
  * 使用 Alembic 或类似工具管理数据库迁移。
* **状态管理 (`@status` 模块):**
  * `status` 命令的实现主要依赖于调用其他服务的接口或 Repository (`TaskRepository`, `RoadmapRepository`, `WorkflowSessionRepository`, `ProjectState`) 来获取数据并聚合展示。它本身不存储状态，而是作为状态的 **查询和呈现者**。

**5. 实施步骤**

1. **数据模型与数据库设计 (2 天):**
    * 定义 `Task` 和 `TaskComment` 的 SQLAlchemy 模型。
    * 确定并添加必要的关联字段到现有模型。
    * 设计并应用数据库 Schema 变更 (Alembic 迁移脚本)。
2. **核心 Task 命令实现 (CRUD) (3 天):**
    * 实现 `TaskRepository` (或在 `DatabaseService` 中添加方法)。
    * 实现 `task list`, `task show`, `task create`, `task update`, `task delete` 的基本功能 (不含关联)。
    * 实现 `task comment`。
    * 编写单元测试。
3. **关联机制实现 (2 天):**
    * 实现 `task link` 命令。
    * 在 `task create` 和 `task update` 中添加处理关联参数的逻辑 (`--link-*`, `--unlink-*`)。
    * 更新 `task show` 以显示关联信息。
    * 编写关联相关的测试。
4. **Workflow 集成 (3 天):**
    * 修改 `flow context` 命令的逻辑，使其能够查询并返回与当前会话/阶段相关的 `task` 列表。
    * 调整 `WorkflowSession` 或 `StageInstance` 模型/状态以支持任务关联（如果需要）。
    * 测试 `flow context` 输出是否包含正确的 `task` 信息。
    * 审视 `flow run` 和 `flow next` 是否需要根据 `task` 状态做调整（初期可能不需要）。
5. **Roadmap 集成 (1 天):**
    * 修改 `roadmap show` 命令以显示关联的 `task` 列表及其状态。
    * 修改 `roadmap status` 的计算逻辑以考虑关联 `task` 的状态（可选，可能保持基于 Story 本身状态）。
    * 测试 Roadmap 命令输出。
6. **Status 命令集成 (2 天):**
    * 实现 `status task` 子命令，调用 `TaskRepository` 获取统计数据。
    * 修改 `status show` 子命令，聚合 `ProjectState`, Workflow, Roadmap 和 Task 的关键信息。
    * 修改 `status roadmap` 和 `status flow` 以确保概念清晰，只展示其领域内的状态。
    * 测试 Status 命令输出。
7. **文档与最终测试 (2 天):**
    * 更新 `@command-list.md` 和其他相关命令文档。
    * 编写 `task` 命令的用户文档和示例。
    * 进行端到端集成测试。
    * 代码审查和合并。

**6. 风险与对策**

* **风险:** 关联逻辑复杂，可能引入 Bug。
  * **对策:** 编写详尽的单元测试和集成测试覆盖各种关联场景。先实现核心关联，逐步增加复杂性。
* **风险:** Workflow 集成点 (`flow context`) 修改难度大。
  * **对策:** 仔细分析现有 `flow context` 实现，分小步修改，增加日志记录，充分测试。
* **风险:** 概念混淆导致 `status` 命令输出不清晰。
  * **对策:** 在开发 `status` 命令前，团队内部再次确认各概念边界和 `status` 各子命令的职责，确保输出符合预期。
* **风险:** 数据库迁移出错。
  * **对策:** 在开发环境中充分测试迁移脚本，备份生产数据（如果适用）。

**7. 验收标准**

* 所有 `task` 命令按设计工作，符合标准化输出。
* 可以创建独立任务和关联到 Roadmap 的任务。
* 可以成功将 `task` 关联/取消关联到 Roadmap 和 Workflow Session/Stage Instance。
* `task show` 正确显示所有信息，包括关联。
* `flow context` 命令能根据当前会话和阶段，列出相关的 `task` ID。
* `roadmap show` 能显示其关联的 `task`。
* `status task` 命令能正确显示任务统计信息。
* `status show`, `status roadmap`, `status flow` 的输出符合概念对齐后的定义。
* 相关文档已更新。
