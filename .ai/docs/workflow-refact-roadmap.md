
**项目：VibeCopilot 工作流系统重构**

**目标：** 按照 `workflow-refactor.md` 中定义的目标架构，对工作流系统进行数据库结构规范化和代码重构，以提高系统的健壮性、可维护性和可扩展性。

**核心原则：**

* **定义与实例分离：** 清晰区分工作流模板和具体执行实例。
* **版本控制：** 引入工作流定义版本管理。
* **历史追踪：** 使用 `StageInstance` 记录详细的执行历史。

---

**阶段一：设计与规划 (Design & Planning)**

* **目标：** 确定最终的数据库模型细节，规划迁移策略。
* **关键任务：**
  * [ ] 最终确定 `workflow_definitions`, `workflow_versions`, `stages`, `transitions`, `flow_sessions`, `stage_instances` 等表的详细字段、类型、约束和关系。
  * [ ] 制定详细的数据迁移计划，明确如何从现有的 `stages_data` JSON 迁移到新表结构。
  * [ ] 确定如何处理现有运行中的 `flow_sessions`（标记为legacy、尝试回填 `stage_instances` 或其他方案）。
  * [ ] 评估并选择数据迁移工具（推荐 Alembic），并设置好初始配置。
  * [ ] 规划重构过程中的分支策略和代码合并计划。
* **产出物：** 最终版数据库 ER 图，详细的数据迁移方案文档，Alembic 基础配置。

---

**阶段二：数据库迁移实施 (Database Migration)**

* **目标：** 创建新的数据库结构，并将现有定义数据迁移至新结构。
* **关键任务：**
  * [ ] 编写 Alembic 迁移脚本：
    * 创建 `workflow_versions`, `stages`, `transitions`, `stage_instances` 表。
    * 添加 `workflow_version_id` 列到 `flow_sessions`。
    * 实现解析 `workflow_definitions.stages_data` JSON 的逻辑。
    * 实现将解析数据填充到 `workflow_versions`, `stages`, `transitions` 的逻辑，建立关联。
    * 实现更新 `flow_sessions` 的 `workflow_version_id` 的逻辑（例如，指向 v1.0）。
    * （可选）根据迁移策略，尝试为旧 `flow_sessions` 回填 `stage_instances`。
  * [ ] 在开发/测试环境中执行并反复测试迁移脚本，确保数据完整性和正确性。
  * [ ] 准备生产环境的迁移步骤（可能需要停机窗口）。
  * [ ] **（迁移完成后）** 编写移除 `workflow_definitions.stages_data` 列的迁移脚本（待后续阶段确认后执行）。
* **产出物：** 可靠的 Alembic 迁移脚本，测试通过的迁移结果报告。

---

**阶段三：核心逻辑层重构 (Core Logic Refactoring)**

* **目标：** 更新数据访问层和核心服务层，使其适应新的数据库模型。
* **关键任务：**
  * [ ] 重写或更新 SQLAlchemy Repositories (`WorkflowDefinitionRepository`, `StageRepository`, `TransitionRepository`, `FlowSessionRepository`) 以操作新表。
  * [ ] 创建并实现 `StageInstanceRepository`。
  * [ ] 创建并实现 `WorkflowVersionRepository`。
  * [ ] 重构 `FlowSessionManager` 的核心方法：
    * `create_session`: 关联到特定的 `workflow_version_id`，创建初始 `StageInstance`。
    * `get_next_stages`: 基于 `StageInstance` 的完成状态、`transitions` 定义和条件评估逻辑。
    * `get_session_context`: 基于 `flow_sessions` 和当前的 `StageInstance` 数据。
    * `get_session_progress`: 基于 `stage_instances` 的历史记录。
    * 实现流程推进逻辑（如 `complete_stage`）：更新 `StageInstance` 状态，创建新的 `StageInstance`。
  * [ ] 确保所有数据库交互都通过新的 Repositories 进行。
* **产出物：** 更新后的 Repositories 和 `FlowSessionManager` 代码，单元测试。

---

**阶段四：命令接口层重构 (Command Interface Refactoring)**

* **目标：** 更新 CLI 命令处理程序以反映新的数据模型和逻辑。
* **关键任务：**
  * [ ] 重构 `src/cli/commands/flow/handlers/flow_info.py`：
    * `handle_context_subcommand`: 主要查询 `flow_sessions` 和 `stage_instances` 来展示当前状态和历史（如果需要）。关联 `stages` 获取定义信息。
    * `handle_next_subcommand`: 调用重构后的 `FlowSessionManager.get_next_stages` 获取下一阶段定义。
    * 更新相应的格式化函数 (`format_context_text`, `format_next_stages_text`) 以适应新的数据结构。
  * [ ] 检查并更新其他可能受影响的 `vc flow` 子命令（如 `run`, `list`, `session` 相关命令）。
* **产出物：** 更新后的 CLI 命令处理代码，端到端测试用例。

---

**阶段五：工作流定义管理 (Definition Management)**

* **目标：** 提供创建和更新规范化工作流定义的方式。
* **关键任务：**
  * [ ] 设计并实现创建/更新工作流定义的机制（可能通过 CLI 命令、管理界面或直接操作数据库的脚本）。
  * [ ] 实现工作流定义的版本管理逻辑（例如，更新定义时创建新版本）。
  * [ ] 确保定义创建/更新操作的原子性和一致性。
* **产出物：** 工作流定义管理工具或流程文档。

---

**阶段六：全面测试与验证 (Testing & Validation)**

* **目标：** 确保重构后的系统功能正确、性能达标且稳定。
* **关键任务：**
  * [ ] 编写和执行全面的单元测试、集成测试和端到端测试。
  * [ ] 测试各种边界条件和异常情况（如无效的转换、条件评估失败等）。
  * [ ] 验证历史数据的准确性（如果进行了回填）。
  * [ ] 进行性能测试，特别是涉及大量 `stage_instances` 的查询。
  * [ ] 用户验收测试 (UAT)。
* **产出物：** 测试报告，Bug修复记录。

---

**阶段七：文档与清理 (Documentation & Cleanup)**

* **目标：** 更新文档，清理旧代码，完成收尾工作。
* **关键任务：**
  * [ ] 更新所有相关的开发者文档和用户文档，反映新的架构和命令行为。
  * [ ] **确认并执行**移除 `workflow_definitions.stages_data` 列的数据库迁移脚本。
  * [ ] 移除代码中所有与旧 `stages_data` 相关的逻辑和注释。
  * [ ] 进行最终的代码审查和质量检查。
  * [ ] 合并代码到主分支并部署。
* **产出物：** 更新的文档，清理后的代码库。

---

**风险与挑战：**

* **数据迁移复杂性：** 从非结构化 JSON 迁移到规范化表可能遇到数据不一致或解析困难。
* **对现有会话的影响：** 需要仔细处理正在运行的旧会话。
* **工作量：** 这是一个涉及数据库和多层代码的较大重构。
* **测试覆盖：** 需要确保测试足够全面以捕捉回归错误。
