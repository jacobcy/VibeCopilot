 **MVP (Minimum Viable Product) 版本的 CDDRG 系统**

我们将采用**适配器模式 (Adapter Pattern)** 的思想，核心模块定义清晰接口，对外接工具/库的调用进行封装，以便未来替换或扩展。

**核心原则:**

1. **本地优先:** 尽可能使用本地文件系统、本地数据库和嵌入式库，减少部署复杂度。
2. **Python 生态:** 优先选用 Python 库和工具，便于集成。
3. **最小化依赖:** 选择功能够用、配置相对简单的工具。
4. **渐进式完善:** 先实现核心流程，再逐步增强功能。

**拆分 Feature 与推荐的最小 Effort 模块组合:**

| Feature / 阶段             | 核心模块 (内部/自研)                     | 推荐技术选型 (Effort 最小组合)                                                                                                | 作用与集成方式                                                                                                                                                                                                                            |
| :--------------------------- | :--------------------------------------- | :------------------------------------------------------------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. 项目管理 & 文档 (目标与计划)** | *文档内容本身*                           | **Obsidian (创作) + Git (版本控制) + Docusaurus (发布)**                                                                  | Obsidian 用于本地 Markdown 编写 PRD、需求、计划。Git 管理版本。**Docusaurus 从 Obsidian (或其他 Markdown 源) 构建在线文档站点 (Docs-as-Code)。** 这是“文档”阶段的基石。                                                                         |
| **2. 规则编写与管理 ("规则"阶段)** | *规则内容本身*                           | **Obsidian (创作) + Git (版本控制)**                                                                                         | 使用 Obsidian 的 Markdown + Front Matter 编写结构化规则。Git 管理版本。规则文件是知识库的重要组成部分。                                                                                                                                       |
| **3. 知识库 - 核心引擎**      | **`cddrg_engine` (Python 库 - 自研核心)** | **`cddrg_engine` 包含:** <br> - **Langchain** (核心框架) <br> - **ChromaDB** (本地向量库) <br> - **SQLite** (本地元数据) <br> - **Sentence Transformers** (本地 Embedding) <br> - **OpenAI API Client** (或其他 LLM) | `cddrg_engine` 作为嵌入式库: <br> - `initialize()`: 扫描 Git 仓库中的 Obsidian 文件 (文档+规则)，运行索引管道 (Langchain 处理 -> Sentence Transformers 向量化 -> ChromaDB/SQLite 存储)。<br> - `generate_action_plan()`: 核心规则生成逻辑 (Langchain 检索 -> Langchain Prompt -> LLM -> Langchain 解析)。<br> **选择本地 Embedding (Sentence Transformers) 极大降低了对外部 API 的依赖和成本，Effort 较小。** |
| **4. AI Agent 执行框架 ("代码"阶段)** | **`basic_agent.py` (Python 脚本 - 自研)** | **`basic_agent.py` 导入并使用:** <br> - **`cddrg_engine`** <br> - **`subprocess`** (调用 Shell 命令) <br> - **`os`, `shutil`** (文件操作) <br> - **`gitpython`** (可选，更方便的 Git 操作)            | 简单的 Python 脚本作为 Agent: <br> 1. 接收命令 (e.g., 命令行参数)。 <br> 2. 调用 `cddrg_engine.generate_action_plan()` 获取计划。 <br> 3. **(关键) 调用下面的“人机交互”模块获取确认。** <br> 4. 解析确认后的计划。 <br> 5. 使用 `subprocess` 或 `gitpython` 等执行计划中的步骤 (如 `git clone`, `python run_tests.py`, 文件修改等)。 <br> 6. 记录执行日志到本地文件。 |
| **5. 人机交互 (计划确认)**   | **`human_approval.py` (Python 模块 - 自研)** | **`human_approval.py` 提供函数:** <br> - **`request_confirmation(plan_json)`**                                                       | 极其简化的交互: <br> `basic_agent.py` 调用 `request_confirmation()`。 <br> 此函数: <br> a. **在终端打印格式化后的行动计划。** <br> b. **提示用户输入 'yes' 或 'no' 进行确认。** <br> c. 返回用户的确认结果 (True/False)。<br> **这是 Effort 最小的实现方式，满足了核心的“人类确认”环节。** 后续可替换为更复杂的 UI 或 Bot。          |
| **6. Workflow (可选 - 流程粘合)** | *暂不实现或手动执行*                       | **(未来可选) n8n (自托管) / Manual Steps**                                                                               | MVP 阶段可以**省略自动化 Workflow 工具**。流程的触发（如根据 Git 事件启动 Agent）和协调可以先手动完成，或通过简单的 Git Hooks + Shell 脚本实现。如果需要，n8n 自托管相对灵活且成本较低。                                        |
| **7. 开发环境集成**        | *Agent 执行的一部分*                       | **依赖 Agent 使用的标准命令行工具 (Git, Docker CLI, Python, etc.)**                                                         | Agent 通过 `subprocess` 调用本地已安装的开发工具。无需额外集成层。                                                                                                                                                           |
| **8. 监控与日志**          | **`cddrg_engine` & `basic_agent.py` 的日志** | **Python `logging` 模块输出到本地文件**                                                                                      | `cddrg_engine` 和 `basic_agent.py` 都使用 Python 内置的 `logging`，将日志写入本地文件。通过查看日志文件进行基本的监控和调试。**Effort 最小。**                                                                               |
| **9. 安全与治理**          | *基本约束*                               | **1. 人类确认环节 (核心安全门)。 2. Agent 运行权限限制 (OS 层面)。 3. 敏感信息通过环境变量传递给 Agent。**                                | MVP 阶段依赖核心的人类审核来防止危险操作。限制 Agent 脚本的运行权限。API Keys 等通过环境变量管理。**这是最基本的安全措施。**                                                                                                   |

**模块组合总结 (MVP):**

1. **文档/规则创作 & 版本控制:** **Obsidian + Git**
2. **在线文档发布:** **Docusaurus** (读取 Obsidian/Git 中的 Markdown)
3. **知识库后端 & 规则生成核心:** **`cddrg_engine` Python 库** (封装 Langchain, ChromaDB, SQLite, Sentence Transformers, LLM Client)
4. **Agent 执行:** **`basic_agent.py` Python 脚本** (使用 `cddrg_engine` 和 `subprocess`)
5. **人机交互 (确认):** **`human_approval.py` 简单的终端交互模块**
6. **日志:** **Python `logging` 输出到本地文件**
7. **安全:** **依赖人类确认 + OS 权限 + 环境变量**
8. **Workflow:** **手动触发或简单脚本** (暂缓复杂工具)

**流程串联 (MVP):**

1. **文档/规则阶段:** 使用 Obsidian 编写 `.md` 文件 (PRD, 规则等)，提交到 Git。
2. **发布文档:** 配置 Docusaurus 读取 Git 仓库中的相关 Markdown 文件，构建并发布在线文档站点。
3. **初始化 (可能需要手动运行一次脚本):** 运行一个脚本调用 `cddrg_engine.initialize()`，它会扫描 Git 仓库中的文件，建立本地的 ChromaDB 和 SQLite 索引。
4. **触发 Agent:** 手动运行 `python basic_agent.py --command "/create_feature X" --issue "PROJ-123"`。
5. **生成计划:** `basic_agent.py` 调用 `cddrg_engine.generate_action_plan()`。
6. **人类确认:** `basic_agent.py` 调用 `human_approval.request_confirmation()`，在终端显示计划并等待用户输入 `yes`。
7. **执行:** 用户确认后，`basic_agent.py` 解析计划，通过 `subprocess` 调用 `git`, `python` 等命令执行步骤。
8. **记录日志:** `basic_agent.py` 和 `cddrg_engine` 将日志写入本地文件。
9. **知识循环 (手动):** Agent 执行产生的报告、重要日志，需要手动整理成 Markdown 文件，提交回 Git 仓库的知识源目录，下次 `initialize` 时会被索引。

**这个 MVP 组合的优势:**

* **Effort 相对最小:** 主要的自研工作集中在 `cddrg_engine` 库和 `basic_agent.py` 脚本的核心逻辑。人机交互、日志、安全等都采用了最简实现。
* **高度本地化:** 大部分组件在本地运行，便于开发、测试和单机使用。
* **Python 技术栈统一:** 集成相对容易。
* **核心流程完整:** 实现了“文档 -> 规则 -> 确认 -> 代码 -> 日志”的核心闭环，并整合了 Docusaurus。
* **可扩展性:** 未来可以将 `human_approval` 替换为 Web UI 或 Bot，将 `basic_agent.py` 发展为更复杂的 Agent 框架，将日志接入专业系统，引入 Workflow 工具等，而核心 `cddrg_engine` 保持相对稳定。

这个组合为你提供了一个坚实的基础，可以快速验证 CDDRG 范式的核心价值，并在此基础上逐步迭代和完善。
