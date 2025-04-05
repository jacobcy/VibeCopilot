# 系统架构报告: CDDRG 引擎库 (嵌入式)

---

**版本:** 1.0
**日期:** 2023年10月27日
**作者:** [你的名字/团队] & AI 助手

**1. 引言**

本报告详细描述了 `cddrg_engine` Python 库的系统架构。该库旨在实现“命令驱动的动态规则生成”（CDDRG）范式，作为一个可嵌入的组件，供 Python 应用程序（Agent）调用，以根据命令和上下文动态生成执行规则。架构设计的核心目标是提供一个轻量级、高性能、易于集成、支持本地运行，并融入了缓存机制、知识循环理念和清晰人机交互模式的解决方案。

**2. 架构目标**

- **模块化与可维护性:** 将核心功能封装在清晰定义的组件中，易于理解、测试和扩展。
- **性能:** 通过缓存机制减少对 LLM API 的重复调用和本地计算开销，优化 `generate_rules` 的响应时间。
- **易于集成:** 提供简洁的 Python API 接口，方便 Agent 应用直接调用。
- **灵活性与可配置性:** 支持通过配置文件定制知识源、模型、存储路径、缓存策略等。
- **本地优先:** 支持在本地文件系统上运行知识索引、元数据存储和向量存储。
- **知识循环:** 架构应能容纳并利用开发过程产生的文档和日志作为背景知识的一部分。
- **支持人机交互:** 架构设计需支撑一个包含人类确认环节的交互模式。
**3. 核心架构：嵌入式 Python 库**

`cddrg_engine` 被设计为一个 Python 库，直接嵌入到 Agent 应用程序中运行。所有组件（除外部 LLM API）都在同一进程空间内执行。

**3.1 整体组件图 (细化)**

```mermaid
graph TD
    subgraph Agent Application (Python)
        A[Agent Core Logic] -- 1. import & call initialize() --> B(CDDRG Engine Facade);
        A -- 5. call generate_rules(cmd, params, ctx) --> B;
        A -- 11. receive ruleset or error --> B;
        U[User Interaction Logic] -- 0. User issues command --> A;
        U -- 12. Present ruleset for confirmation --> V((User));
        V -- 13. Confirm/Reject --> U;
        A -- 14. Executes based on confirmed rules --> W((External Systems/Tasks));
        A -- 15. Logs execution results --> L[Execution Log Storage (Filesystem/DB)];
    end

    subgraph CDDRG Engine Library (Python Package - cddrg_engine)
        B -- Manages --> X(Configuration Loader);
        B -- Coordinates --> K(Knowledge Indexing Pipeline);
        B -- Coordinates --> CA(Cache Manager);
        B -- Coordinates --> CR(Core Rule Generation Workflow);

        CR -- 6. Request knowledge --> C(Knowledge Retriever);
        CR -- 8. Build prompt --> D(Prompt Engine);
        CR -- 9. Send prompt --> F(LLM Client);
        CR -- 10. Format response --> H(Response Formatter);

        C -- 7a. Query vectors --> E(Vector Store Client - ChromaDB);
        C -- 7b. Query metadata --> M(Metadata Store Client - SQLite);

        K -- Manages --> E;
        K -- Manages --> M;

        CA -- Uses --> CS(Cache Storage - e.g., SQLite/File Cache/In-Memory);

        X -- Provides config --> K;
        X -- Provides config --> C;
        X -- Provides config --> E;
        X -- Provides config --> M;
        X -- Provides config --> D;
        X -- Provides config --> F;
        X -- Provides config --> CA;
        X -- Provides config --> Y;

        Y(Logging Module) -- Used by all components --> Z((Log Output));
    end

    subgraph Knowledge & Data Stores (Local Filesystem)
        O[Knowledge Source (Files)] --> K;
        L -- Read by --> K; # Execution Logs as part of Knowledge Source
        P[Vector Store (ChromaDB File)] <--> E;
        R[Metadata Store (SQLite File)] <--> M;
        S[Cache Store (SQLite/File)] <--> CS;
        Q[Configuration File (YAML/.env)] --> X;
    end

    G((External LLM API)) <-- 9. Network Call / 10. Response --> F;

    %% Styling
    style Agent Application fill:#e0f0ff,stroke:#333,stroke-width:1px
    style CDDRG Engine Library fill:#ffffe0,stroke:#333,stroke-width:1px
    style Knowledge & Data Stores fill:#e0ffe0,stroke:#333,stroke-width:1px
    style G fill:#f9f,stroke:#333,stroke-width:2px
    style V fill:#fcc,stroke:#333,stroke-width:2px
    style W fill:#fcc,stroke:#333,stroke-width:2px

    %% Annotations for Flow Steps
    linkStyle 0 stroke-width:1px,color:blue;
    linkStyle 1 stroke-width:1px,color:blue;
    linkStyle 5 stroke-width:1px,color:red;
    linkStyle 6 stroke-width:1px,color:orange;
    linkStyle 7 stroke-width:1px,color:purple;
    linkStyle 8 stroke-width:1px,color:orange;
    linkStyle 9 stroke-width:1px,color:green;
    linkStyle 10 stroke-width:1px,color:orange;
    linkStyle 11 stroke-width:1px,color:red;
    linkStyle 12 stroke-width:1px,color:blue;
    linkStyle 13 stroke-width:1px,color:blue;
    linkStyle 14 stroke-width:1px,color:blue;
    linkStyle 15 stroke-width:1px,color:blue;

```

**3.2 核心组件详解**

- **CDDRG Engine Facade (B):**
- 提供给 Agent 的主要接口 (`initialize`, `generate_rules`)。
- 封装内部复杂性，协调其他组件工作。
- 管理引擎的生命周期和状态。
- **Configuration Loader (X):**
- 负责从指定文件（YAML, .env）加载和验证配置。
- 向其他需要配置的组件提供配置信息。
- 处理敏感信息（如 API Keys）的安全加载（例如从环境变量）。
- **Knowledge Indexing Pipeline (K):**
- **职责:** 离线或按需处理知识源文件，构建和更新向量库和元数据存储。
- **子组件:** 文件扫描器、文本分块器、向量化器（调用 Embedding 模型）、向量库写入器、元数据存储写入器。
- **知识循环入口:** 配置应允许将开发文档、**执行日志 (L)** 等也作为知识源目录，使其内容被索引。
- **Cache Manager (CA):**
- **职责:** 缓存 `generate_rules` 的结果，减少对 LLM API 的调用和本地计算。
- **缓存键 (Cache Key):** 基于 `command`, `parameters`, `context` 的确定性哈希值，可能还需要考虑检索到的知识片段的哈希（避免知识更新导致缓存失效）。
- **缓存策略:** 可配置（如 LRU, TTL）。
- **缓存存储 (CS):** 可配置，例如：
- 内存缓存 (简单，进程结束失效)。
- 文件缓存 (基于哈希值存储 JSON 文件)。
- SQLite 数据库 (结构化存储缓存条目)。
- **工作流程:** 在执行核心规则生成工作流之前检查缓存，如果命中则直接返回缓存结果。否则，在工作流成功返回结果后，将结果存入缓存。
- **Core Rule Generation Workflow (CR):**
- **职责:** 编排单次 `generate_rules` 调用的核心逻辑。
- **流程:** 调用 Knowledge Retriever -> 调用 Prompt Engine -> 调用 LLM Client -> 调用 Response Formatter。
- **Knowledge Retriever (C):**
- **职责:** 根据输入（命令、参数、上下文的向量化表示或关键词）从向量库和元数据存储中检索最相关的知识片段。
- **交互:** 调用 Vector Store Client (E) 进行相似性搜索，调用 Metadata Store Client (M) 获取额外信息或进行过滤。
- **知识循环体现:** 检索时会包含来自文档和日志的索引内容。
- **Vector Store Client (E - ChromaDB):**
- 封装与本地 ChromaDB 文件交互的逻辑（连接、查询、写入）。
- **Metadata Store Client (M - SQLite):**
- 封装与本地 SQLite 数据库文件交互的逻辑（连接、查询、写入）。存储文件元数据、可选的块元数据、索引状态等。
- **Prompt Engine (D):**
- **职责:** 根据配置的模板，动态构建发送给 LLM 的最终 Prompt。
- **输入:** 命令、参数、上下文、检索到的知识片段。
- **输出:** 格式化的 Prompt 字符串。
- **LLM Client (F):**
- **职责:** 与外部 LLM API 进行网络通信。
- **功能:** 发送请求、处理响应、错误处理（重试、超时）、认证。
- **Response Formatter (H):**
- **职责:** 解析 LLM 返回的（通常是非结构化的）文本响应。
- **功能:** 提取关键信息，将其转换为 Agent 易于使用的结构化格式（如 JSON）。处理解析错误。
- **Logging Module (Y):**
- 提供标准的日志记录功能，供所有组件使用。输出到文件或控制台，级别可配。
- **Cache Storage (CS):**
- 实际存储缓存数据的后端（内存、文件、SQLite）。
- **Knowledge Source (O):**
- 存储原始知识的文件目录（Markdown 文档、文本文件等）。
- **Execution Log Storage (L):**
- Agent 执行任务后产生的日志文件或数据库记录。**可配置为 Knowledge Source 的一部分被索引**。
**4. 数据模型**

- **配置数据:** YAML 或 .env 文件，定义路径、模型、API Keys、缓存策略等。
- **知识源数据:** 文本文件 (.md, .txt)。
- **元数据 (SQLite):** 存储已索引文件信息、可选的块信息、索引时间戳等。
- **向量数据 (ChromaDB):** 存储文本块的向量表示及关联元数据（来源 ID）。
- **缓存数据 (SQLite/File/Memory):** 存储缓存键与 `generate_rules` 的 JSON 结果。
- **规则集数据 (JSON):** `generate_rules` 返回的标准格式。
- **执行日志数据:** Agent 生成的日志信息，格式由 Agent 定义，但应包含足够信息供 RGI 理解（如执行的命令、结果、遇到的问题）。
**5. 人机交互模式集成**

架构图中的 Agent Application 部分体现了明确的人机交互流程：

1. **用户发出指令 (0):** 用户通过某种界面（CLI, GUI）向 Agent 发出源命令。
1. **Agent 调用引擎 (1, 5):** Agent 解析命令，调用 `cddrg_engine.initialize()` (如果需要) 和 `cddrg_engine.generate_rules()`。
1. **引擎生成规则 (6-10):** 引擎内部执行检索、推理、生成流程（利用缓存）。
1. **引擎返回规则 (11):** `cddrg_engine` 返回生成的规则集 (JSON)。
1. **Agent 呈现给用户 (12):** Agent 将易于理解的规则文本（可能需要进一步处理 JSON）呈现给用户确认。
1. **用户确认/拒绝 (13):** 用户审核规则，通过界面反馈确认或拒绝。
1. **Agent 执行 (14):** 如果用户确认，Agent 按照返回的规则集执行任务，与外部系统交互。
1. **Agent 记录日志 (15):** Agent 将执行过程、结果、遇到的问题记录到执行日志存储 (L)。**这些日志随后可以被知识索引管道 (K) 处理，形成知识循环**。
**6. 知识循环实现**

知识循环通过以下机制实现：

- **日志作为知识源:** Agent 产生的执行日志 (L) 被配置为知识源 (O) 的一部分。
- **定期/按需索引:** 知识索引管道 (K) 会处理这些日志文件，提取关键信息（如成功/失败模式、特定参数下的常见问题、使用的解决方案）并将其向量化、存入向量库 (P) 和元数据存储 (R)。
- **检索时利用:** 当 Knowledge Retriever (C) 为新的 `generate_rules` 调用检索信息时，它也能检索到来自过去执行日志的相关片段。
- **LLM 推理增强:** 这些来自日志的“经验”信息被包含在发送给 LLM 的 Prompt 中，使得 LLM 在生成新规则时能够参考过去的成功经验和失败教训，从而生成更优化、更鲁棒的规则。
**7. 缓存策略细节**

- **缓存粒度:** 缓存整个 `generate_rules` 的输出（格式化的规则集）。
- **缓存键生成:**
- 基础：`hash(command + sorted(parameters.items()) + sorted(context.items()))`
- 考虑知识依赖 (可选，更复杂)：在检索到知识后，将检索到的知识片段的 ID 或哈希也纳入缓存键计算，`hash(base_key + sorted(retrieved_knowledge_ids))`。这确保了知识源更新后，依赖该知识的查询缓存会失效。
- **失效策略:**
- 基于 TTL（时间）。
- 基于 LRU（最近最少使用）。
- 显式清除（例如，在知识库重新索引后）。
- **存储选型:**
- **内存:** 最快，但进程重启丢失。适合短生命周期 Agent。
- **SQLite:** 持久化，结构化查询方便，适合单机持久缓存。
- **文件:** 简单，易于检查，但在大量缓存条目下性能可能下降。
**8. 部署模型**

该架构的核心是**嵌入式库**，因此部署非常简单：

- Agent 应用程序通过 Python 的包管理器 (pip) 安装 `cddrg_engine` 库及其依赖。
- 配置文件、知识源文件、数据库文件（ChromaDB, SQLite）、缓存文件（如果使用文件缓存）与 Agent 应用程序一起部署在本地文件系统上。
- Agent 应用程序在运行时加载和调用该库。
**9. 总结**

本架构报告描述了一个模块化、可配置、支持本地运行的 `cddrg_engine` Python 库。通过引入缓存层优化性能，通过知识循环机制（索引执行日志）增强了系统的学习和适应能力，并明确了支持人类确认环节的人机交互模式。该架构为构建智能、适应性强的 Agent 应用提供了一个坚实且灵活的基础。

