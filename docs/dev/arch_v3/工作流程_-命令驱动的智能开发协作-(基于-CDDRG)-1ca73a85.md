# 工作流程: 命令驱动的智能开发协作 (基于 CDDRG)

---

**核心理念:** 使用一系列标准化的命令来驱动整个开发（或类似知识工作）流程。每一步都由 Agent 在 `cddrg_engine` 生成的动态规则指导下执行，关键节点有人工审核，最终成果和过程日志被系统性地记录和学习。

**参与者:**

- **人类用户 (User):** 需求的提出者、指令的发出者、关键决策的审核者。
- **智能体 (Agent):** Python 应用程序，内嵌 `cddrg_engine` 库。负责解析命令、与引擎交互、执行任务、生成报告、与用户交互。
- **CDDRG 引擎 (Engine):** `cddrg_engine` 库。负责根据命令和上下文动态生成规则。
- **知识库 (Knowledge Base):** 包含策略文档、最佳实践、代码库、**历史 PRD**、**历史计划**、**历史执行报告**、**历史测试报告**、**历史 Review 记录**、**开发日志 (Blogs)** 等。由引擎的索引管道管理。
- **知识图谱/记忆库 (Memory Store):** 用于存储结构化的工作流程实例和关键洞察。
**标准工作流程 (以一个功能开发为例):**

**阶段 1: 定义任务 (做什么?)**

1. **用户发出指令:**
- 用户输入命令: `/task create_login_feature based on requirement doc /docs/req/login_req.md`
- **(User -> Agent)**
1. **Agent 解析与准备:**
- Agent 解析命令 (`/task`) 和参数 (任务描述, 需求文档路径)。
- Agent 收集上下文 (用户角色, 当前项目状态, 时间戳等)。
- **(Agent Internals)**
1. **Agent 请求规则:**
- Agent 调用: `rules = engine.generate_rules(command='/task', parameters={'description': '...', 'source_doc': '...'}, context={...})`
- **(Agent -> Engine)**
1. **引擎生成 PRD 撰写规则:**
- 引擎 (利用缓存或重新生成):
- 检索知识库中关于撰写 PRD 的最佳实践、模板、历史 PRD 示例、以及 `login_req.md` 的相关信息。
- LLM 推理生成撰写此特定 PRD 的具体规则/指南 (e.g., "使用标准 PRD 模板", "必须包含安全考量章节", "明确用户故事和验收标准", "参考 `/docs/prd/similar_feature_prd.md`")。
- 引擎返回 JSON 格式的规则集。
- **(Engine Internals -> Engine)**
1. **Agent 呈现规则 (可选，或用于复杂任务):**
- Agent 可以向用户展示生成的 PRD 撰写指南，供参考。
- **(Engine -> Agent -> User)**
1. **Agent 执行 **`**/task**`** (生成 PRD 草稿):**
- Agent 严格遵循返回的规则集，结合需求文档 (`login_req.md`)，调用 LLM 或使用模板引擎生成 PRD 草稿 (`/drafts/prd_login_feature_v0.1.md`)。
- **(Agent Internals)**
1. **Agent 提交 PRD 草稿:**
- Agent 通知用户 PRD 草稿已生成，并提供文件路径。
- **(Agent -> User)**
1. **用户评审与修改 (迭代):**
- 用户评审 PRD 草稿，可能直接修改，或向 Agent 发出修改指令 (e.g., `/task revise_prd /drafts/prd_... add clarification on SSO`)。此步骤可能重复。
- **(User <-> Agent)**
**阶段 2: 规划工作 (怎么做?)**

1. **用户发出指令:**
- 用户 (在 PRD 稳定后) 输入命令: `/spec for prd /docs/prd/prd_login_feature_final.md assign_to @developer_A`
- **(User -> Agent)**
1. **Agent 解析与准备:**
- Agent 解析命令 (`/spec`) 和参数 (PRD 路径, 指派人)。
- Agent 收集上下文 (项目时间表, 团队成员技能, 依赖关系等)。
- **(Agent Internals)**
1. **Agent 请求规则:**
- Agent 调用: `rules = engine.generate_rules(command='/spec', parameters={'prd_path': '...', 'assignee': '...'}, context={...})`
- **(Agent -> Engine)**
1. **引擎生成计划制定规则:**
- 引擎检索知识库中关于任务分解、工时估算、依赖分析、风险识别的最佳实践，以及历史类似任务的计划。
- LLM 推理生成制定此特定任务计划的规则/指南 (e.g., "分解 PRD 为可执行子任务", "估算每个子任务工时 (使用斐波那契)", "识别对认证服务的依赖", "输出为 Markdown 格式的计划表")。
- 引擎返回规则集。
- **(Engine Internals -> Engine)**
1. **Agent 执行 **`**/spec**`** (生成工作计划草稿):**
- Agent 遵循规则，分析 PRD，生成包含子任务、估时、依赖、负责人的工作计划草稿 (`/plans/plan_login_feature_v0.1.md`)。
- **(Agent Internals)**
1. **Agent 提交计划草稿:**
- Agent 通知用户和指派人 (`@developer_A`) 计划草稿已生成。
- **(Agent -> User, @developer_A)**
1. **用户/团队评审与修改 (迭代):**
- 用户和团队成员评审计划，可能调整任务、估时、分配。可通过 Agent 修改或直接编辑。
- **(User, Team <-> Agent)**
**阶段 3: 执行任务**

1. **开发者 (或 Agent) 执行 **`**/work**`**:**
- 开发者 `@developer_A` 开始工作，并定期 (或完成时) 通过 Agent 记录进展或提交结果。
- 或者，如果任务可由 Agent 自动执行 (e.g., 运行脚本, 生成代码片段):
- 用户/开发者发出指令: `/work on task 'Implement login API endpoint' from plan /plans/plan_...`
- Agent 请求 `/work` 的执行规则 (可能包括编码规范、单元测试要求、日志记录标准)。
- Agent 遵循规则执行任务 (e.g., 编写代码, 运行测试)。
- Agent 提交工作产出 (代码 commit, 文件) 和一份**工作报告/日志** (`/logs/work_login_api_... .log`)，说明完成情况、遇到的问题、耗时等。
- **(Developer/User -> Agent -> Engine -> Agent -> Output & Work Report)**
**阶段 4: 测试验证**

1. **用户/测试者发出指令:**
- `/test feature 'login API endpoint' against prd /docs/prd/... using criteria from spec /plans/plan_...`
- **(User/Tester -> Agent)**
1. **Agent 请求规则:**
- Agent 请求 `/test` 的执行规则 (可能包括测试环境设置、测试数据准备、测试用例设计原则、报告格式要求)。
- **(Agent -> Engine)**
1. **Agent 执行 **`**/test**`** (运行测试):**
- Agent 遵循规则，准备测试环境，执行测试用例（手动提示或自动执行），记录结果。
- **(Agent Internals)**
1. **Agent 生成测试报告:**
- Agent 生成详细的测试报告 (`/reports/test_login_api_... .md`)，包含测试结果、失败详情、覆盖率等。
- **(Agent -> User/Tester)**
**阶段 5: 审核与确认**

1. **用户发出指令:**
- `/review task 'Implement login API endpoint' with work_report /logs/work_... and test_report /reports/test_...`
- **(User -> Agent)**
1. **Agent 请求规则:**
- Agent 请求 `/review` 的执行规则 (可能包括审核清单、常见幻觉模式检查点、与 PRD 和 Spec 的一致性核对要求)。
- **(Agent -> Engine)**
1. **Agent 执行 **`**/review**`** (辅助审核):**
- Agent 遵循规则，对比工作报告、测试报告、PRD、Spec，高亮潜在问题、不一致之处、未满足的需求，并可能进行初步的幻觉检测分析（基于 LLM 的自我反思）。
- Agent 生成一份**审核辅助报告**。
- **(Agent Internals -> Agent)**
1. **Agent 呈现审核信息:**
- Agent 将工作产出、报告和审核辅助报告一起呈现给用户。
- **(Agent -> User)**
1. **用户进行最终审核:**
- 用户结合 Agent 的分析，进行最终的判断和审核，**这是避免 AI 幻觉、确保质量的关键人工环节**。用户可以批准或要求返工（回到 `/work` 或 `/spec`）。
- **(User)**
**阶段 6: 提交与固化**

1. **用户发出指令:**
- 用户 (在审核通过后) 输入命令: `/commit feature 'login_feature' with artifacts [prd_path, plan_path, code_commit_hash, test_report_path]`
- **(User -> Agent)**
1. **Agent 请求规则:**
- Agent 请求 `/commit` 的规则 (可能包括版本控制操作指南、文档归档标准、通知相关人员的模板)。
- **(Agent -> Engine)**
1. **Agent 执行 **`**/commit**`**:**
- Agent 遵循规则，执行相应的操作（如合并代码到主分支、标记版本、将最终文档移动到发布目录、发送通知）。
- Agent 记录 commit 操作日志。
- **(Agent Internals -> External Systems & Logs)**
**阶段 7: 知识沉淀与学习**

1. **用户 (或系统自动触发) 发出指令:**
- `/memory store workflow_instance 'login_feature_dev' with artifacts [...] status completed`
- **(User/System -> Agent)**
1. **Agent 请求规则:**
- Agent 请求 `/memory` 的规则 (定义如何结构化地存储工作流实例到知识图谱/记忆库，提取哪些关键信息和关系)。
- **(Agent -> Engine)**
1. **Agent 执行 **`**/memory**`**:**
- Agent 遵循规则，提取本次工作流的关键信息（任务、计划、产出、结果、耗时、人员、遇到的问题、解决方案），并将其结构化地存入知识图谱或专门的记忆数据库。
- **(Agent Internals -> Memory Store)**
1. **用户 (或系统自动触发) 发出指令:**
- `/blog generate for task 'login_feature_dev' using logs [...] audience developers`
- **(User/System -> Agent)**
1. **Agent 请求规则:**
- Agent 请求 `/blog` 的规则 (日志总结、关键洞察提炼、面向特定受众的写作风格指南)。
- **(Agent -> Engine)**
1. **Agent 执行 **`**/blog**`**:**
- Agent 遵循规则，分析相关的工作日志、报告和 commit 信息，生成一篇开发日志/博客文章草稿 (`/blogs/devlog_login_feature_... .md`)。
- **(Agent Internals -> Agent)**
1. **用户评审发布:**
- 用户评审日志草稿，修改后发布。**这篇日志也成为知识库的一部分**。
- **(Agent -> User -> Knowledge Base)**
**工作流程特点总结:**

- **命令驱动:** 清晰、标准化的命令启动每个阶段。
- **规则动态生成:** 每一步都由 `cddrg_engine` 根据上下文生成具体指导。
- **人机协作:** Agent 处理繁琐工作和初步分析，人类负责关键决策和最终审核。
- **知识闭环:** 整个流程的产出（PRD, Plan, Logs, Reports, Blogs）和过程本身（Memory）都被系统性地记录和反馈回知识库/记忆库，用于未来的规则生成和学习。
- **迭代性:** 流程中的多个阶段（PRD, Plan, Review）都支持迭代和修改。
这个工作流程将 CDDRG 的能力融入到一个结构化的开发范式中，旨在提高效率、保证质量，并实现持续的知识积累和改进。

