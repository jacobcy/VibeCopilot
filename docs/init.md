# Vibe Coding 项目助手工具 V1.0 (开发流程指南)

## 引言

本指南旨在为使用 AI 辅助编码工具（如 Cursor）的开发者提供一个结构化、规范化的软件开发流程。遵循此指南有助于减少常见开发陷阱（如代码失控、文档缺失、AI 误操作），提升项目质量和开发效率。

**核心理念:** 将开发过程分解为明确的阶段和步骤，在每一步提供指导、检查点和模板，并明确如何有效利用 AI 及规避其风险。

## Phase 0: 准备与配置 (Setup & Configuration)

**目标:** 搭建稳定、规范、且对 AI 友好的开发基础环境。

1.  **开发工具选择与配置:**
    *   [ ] **选择 IDE:** Cursor / VS Code / Windsurf
    *   [ ] **安装必要插件:** Linter, Formatter, GitLens, Docker, 特定语言/框架插件等。
    *   [ ] **配置同步:** (如 VS Code Settings Sync) 确保配置一致性。
    *   [ ] **Cursor/Windsurf 特定配置:** 熟悉 AI 相关设置。

2.  **AI 规则配置 (CursorRules/WindsurfRules):**
    *   [ ] **创建 `cursor.rules` 或类似文件。**
    *   [ ] **定义编码风格:** (如参考 PEP8, Prettier)
    *   [ ] **定义注释要求:** (函数/方法注释、复杂逻辑注释)
    *   [ ] **定义 Commit Message 规范:** (如 Conventional Commits)
    *   [ ] **定义文档更新规则:** (例如: "每次成功实现 Feature 后，提示 AI 更新相关的 PRD 或 API 文档")
    *   [ ] **定义代码生成偏好:** (例如: "优先使用函数式编程风格", "避免使用全局变量")
    *   *模板/示例: [链接到 CursorRules 模板或最佳实践]*

3.  **AI 上下文/记忆配置 (AI Context Provisioning):**
    *   [ ] **配置 AI 可访问的项目目录:** (在 Cursor/Windsurf 中设置)
    *   [ ] **关联核心知识库文档:** (将 Phase 1 中创建的文档添加到 AI 的知识库/上下文)
    *   [ ] **理解并利用 AI 的记忆/上下文窗口:** (知道如何提供关键信息，避免上下文丢失)

4.  **项目级知识库建立 (Core "Coding Docs"):**
    *   [ ] **创建文档目录:** (例如: `/.docs` 或 `/knowledge_base`)
    *   [ ] **初始化核心文档 (稍后填充):**
        *   `1_Project_Requirements_Document_(PRD).md`
        *   `2_App_Flow.md` (或使用绘图工具链接)
        *   `3_Tech_Stack.md`
        *   `4_Frontend_Guidelines.md` (如果适用)
        *   `5_Backend_Structure.md` (如果适用)
        *   `6_AI_Rules.md` (即 `cursor.rules` 的副本或引用)
        *   `7_Implementation_Plan.md`
        *   `(Optional) 8_Best_Practices.md` (框架/语言的最佳实践)
    *   *参考: [链接到 CodeGuide 或类似工具生成的文档模板]*

5.  **开发环境搭建:**
    *   [ ] **选择包管理器:** (如 `pip/venv`, `conda`, `npm/yarn/pnpm`, `uv`)
    *   [ ] **创建虚拟环境:** (如 `python -m venv .venv`, `uv venv`)
    *   [ ] **安装项目依赖:** (`pip install -r requirements.txt`, `npm install`, `pnpm install`)
    *   [ ] **配置环境变量:** (使用 `.env` 文件和 `python-dotenv` 或类似工具)
    *   [ ] **Docker/容器化配置 (如果需要):** (`Dockerfile`, `docker-compose.yml`)
    *   *检查清单: 确保环境可复现，依赖版本固定。*

## Phase 1: 规划与设计 (Planning & Design)

**目标:** 清晰定义项目目标、范围、技术方案和实施路径。

1.  **项目需求文档 (PRD):**
    *   [ ] **填充 `1_Project_Requirements_Document_(PRD).md`:**
        *   项目背景与目标
        *   用户画像与用户故事
        *   功能性需求 (按优先级排列)
        *   非功能性需求 (性能, 安全, 可用性)
        *   范围边界 (明确做什么，不做什么)
        *   验收标准
    *   *使用 AI 辅助: 让 AI 根据初步想法生成 PRD 草稿，然后人工评审修改。*

2.  **应用流程设计 (App Flow):**
    *   [ ] **绘制核心流程图:** (用户注册/登录, 主要功能操作流程等)
    *   [ ] **工具:** Mermaid (Markdown), Excalidraw, Miro, Lucidchart 等。
    *   [ ] **更新 `2_App_Flow.md`:** (嵌入图像或添加链接)
    *   *使用 AI 辅助: 描述流程，让 AI 生成 Mermaid 代码或流程描述。*

3.  **技术选型 (Tech Stack):**
    *   [ ] **决策与记录:**
        *   编程语言 (Python, JS/TS, Go...)
        *   Web 框架 (Django, Flask, FastAPI, React, Vue, Svelte...)
        *   数据库 (PostgreSQL, MySQL, MongoDB, SQLite...)\n        *   ORM (SQLAlchemy, Prisma, Django ORM...)
        *   状态管理 (Redux, Zustand, Pinia...)
        *   部署方式 (Serverless, Docker, VM...)
        *   核心第三方库/API
    *   [ ] **更新 `3_Tech_Stack.md`。**

4.  **项目架构设计:**
    *   [ ] **选择架构模式:** (分层, MVC, MVVM, 微服务, 事件驱动...)
    *   [ ] **绘制高层架构图:** (展示主要组件及其交互)
    *   [ ] **更新相关文档:** (可在 PRD 或单独的架构文档中体现)
    *   *使用 AI 辅助: 描述需求和技术栈，让 AI 推荐架构模式并生成初步架构图描述。*

5.  **模块/组件设计:**
    *   [ ] **识别核心模块/服务。**
    *   [ ] **定义模块职责和接口 (API)。**
    *   *可在此阶段细化，也可在实施计划中分解。*

6.  **前端规范 (Frontend Guidelines):**
    *   [ ] **填充 `4_Frontend_Guidelines.md`:**
        *   UI 库/组件库选用 (MUI, Ant Design, Shadcn/ui...)
        *   代码风格与 Linter/Formatter 配置
        *   目录结构规范
        *   状态管理策略
        *   命名约定 (组件, 变量, CSS 类)
        *   API 请求封装方式
    *   *使用 AI 辅助: 让 AI 基于选定的库和框架生成规范草稿。*

7.  **后端结构 (Backend Structure):**
    *   [ ] **填充 `5_Backend_Structure.md`:**
        *   API 设计规范 (RESTful, GraphQL)
        *   数据库 Schema 设计 (表结构, 关系)
        *   认证与授权方案 (JWT, OAuth, Session...)
        *   目录结构规范 (按功能或类型组织)
        *   错误处理机制
        *   日志记录规范
    *   *使用 AI 辅助: 让 AI 基于选定的框架和数据库生成规范草稿或数据库 Schema。*

8.  **实施计划 (Implementation Plan):**
    *   [ ] **填充 `7_Implementation_Plan.md`:**
        *   将 PRD 功能点分解为更小的、可管理的开发任务 (Features/User Stories)。
        *   估算任务优先级和大致顺序。
        *   定义每个任务的输入、输出和验收标准。
        *   *(这是动态文档，会随着开发进展而更新)*
    *   *使用 AI 辅助: 提供 PRD 和架构设计，让 AI 生成初步的任务分解建议。*

## Phase 2: 开发与执行 (Development & Execution)

**目标:** 高效、规范地编写代码，实现功能，并保持文档同步。

1.  **编码实践:**
    *   [ ] **遵循 `AI_Rules.md` 和 `Best_Practices.md`。**
    *   [ ] **编写清晰、可读、可维护的代码。**
    *   [ ] **利用 AI 进行代码生成、补全、重构和解释，但需谨慎审查。**
        *   **审查点:** 是否符合规范？逻辑是否正确？有无潜在 bug？性能如何？
    *   [ ] **小步提交，频繁集成。**

2.  **Git 源代码管理:**
    *   [ ] **遵循分支策略:** (如 GitFlow 或 GitHub Flow)
        *   `main`/`master`: 稳定发布分支。
        *   `develop`: 集成开发分支。
        *   `feature/xxx`: 功能开发分支。
        *   `fix/xxx`: Bug 修复分支。
    *   [ ] **编写规范的 Commit Message:** (使用 `AI_Rules.md` 中定义的格式)
    *   [ ] **使用 Pull Request (PR) / Merge Request (MR) 进行代码合并。**
    *   [ ] **配置 `.gitignore` 文件。**

3.  **Prompt 提示词优化:**
    *   [ ] **明确任务目标:** (生成代码? 解释? 重构? 找 Bug?)
    *   [ ] **提供充足上下文:** (相关代码片段, 文件结构, `AI_Rules.md` 中的关键规则, 相关文档片段)
    *   [ ] **指定输出格式:** (代码块, 特定语言, JSON, Markdown...)
    *   [ ] **迭代优化:** 如果 AI 输出不理想，调整 Prompt 或提供更精确的指令。
    *   *维护一个 Prompt 片段库以供复用。*

4.  **文档同步更新:**
    *   [ ] **Feature 完成后，检查是否需要更新:**
        *   PRD (需求变更?)
        *   API 文档 (接口变更?)
        *   架构图 (设计调整?)
        *   `Implementation_Plan.md` (任务状态更新)
    *   *使用 AI 辅助: 提交代码变更后，提示 AI 根据 diff 更新相关文档。*

## Phase 3: 测试与质量保证 (Testing & QA)

**目标:** 确保代码质量、功能正确性和系统稳定性。

1.  **单元测试:**
    *   [ ] **选择测试框架:** (Pytest, Jest, Go testing...)
    *   [ ] **为核心逻辑和函数编写单元测试。**
    *   [ ] **追求合理的测试覆盖率 (根据项目需求)。**
    *   [ ] **在 CI/CD 流程中集成单元测试。**
    *   *使用 AI 辅助: 让 AI 为现有函数生成单元测试草稿，然后人工审查和完善。*

2.  **集成测试:**
    *   [ ] **测试模块之间或服务之间的交互。**
    *   [ ] **模拟外部依赖 (数据库, API)。**

3.  **功能测试:**
    *   [ ] **根据 PRD 中的用户故事和验收标准进行测试。**
    *   [ ] **手动测试或编写端到端 (E2E) 测试 (如使用 Playwright, Cypress)。**

4.  **代码审核 (Code Review):**
    *   [ ] **在 PR/MR 合并前进行。**
    *   [ ] **关注点:**
        *   逻辑正确性
        *   是否符合规范 (`AI_Rules.md`)
        *   可读性与可维护性
        *   性能问题
        *   安全性漏洞
        *   测试覆盖率
        *   文档更新
    *   [ ] **使用 Code Review Checklist。**
    *   *使用 AI 辅助: 让 AI 对代码变更进行初步审查，识别潜在问题，辅助人类 Reviewer。*

## Phase 4: 项目管理与维护 (Management & Maintenance)

**目标:** 有效跟踪项目进展，管理技术债务，并从项目中学习。

1.  **项目流程管理 (Feature Tracking):**
    *   [ ] **使用工具:** GitHub Projects, Jira, Trello, Linear 等。
    *   [ ] **保持任务状态更新:** (Todo, In Progress, In Review, Done)
    *   [ ] **关联 PR/MR 到具体任务/Issue。**

2.  **处理技术债:**
    *   [ ] **识别:** (代码中的 "TODO", "FIXME", suboptimal 实现, 缺乏测试, 过期依赖等)
    *   [ ] **记录:** (在代码注释中标记, 或在 Issue Tracker 中创建 Tech Debt 任务)
    *   [ ] **规划偿还:** (安排专门时间或在相关 Feature 开发时一并处理)

3.  **项目总结与复盘 (Retrospective):**
    *   [ ] **项目里程碑或完成后进行。**
    *   [ ] **讨论:**
        *   做得好的地方 (Keep Doing)
        *   可以改进的地方 (Stop Doing / Start Doing)
        *   遇到的问题与解决方案
        *   经验教训
    *   [ ] **记录复盘结果，用于改进未来项目流程。**

## 结语

本指南提供了一个基础框架。请根据您的具体项目需求和团队实践进行调整和完善。持续迭代和改进这个流程本身也是项目成功的一部分。祝您 Vibe Coding 顺利！
