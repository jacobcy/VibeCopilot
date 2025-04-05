# 产品需求文档 (PRD): CDDRG 引擎库 (嵌入式)

---

**版本:** 1.0
**日期:** 2023年10月27日
**作者:** [你的名字/团队] & AI 助手

**1. 概述 (Overview)**

**1.1 背景:**
静态规则库在指导 AI 智能体（Agent）时面临维护复杂、适应性差和上下文感知弱的挑战。为了克服这些限制，我们提出了一种创新的“命令驱动的动态规则生成”（CDDRG）范式。

**1.2 目标产品:**
本产品是一个名为 `**cddrg_engine**` 的 **Python 库 (Package)**。它封装了 CDDRG 范式的核心逻辑，使 Python 应用程序（Agent）能够通过简单的函数调用，根据输入的命令和上下文，动态地从本地知识源生成执行规则。该库旨在提供一个轻量级、易于集成、本地运行的解决方案，赋能开发者构建更智能、更具适应性的 Agent。

**1.3 核心架构:**`cddrg_engine` 作为一个可嵌入的库运行在 Agent 应用程序的同一进程中。它直接访问本地文件系统上的知识源、配置文件、本地向量数据库（如 ChromaDB）和元数据存储（如 SQLite）。它通过网络调用外部 LLM API 进行推理。这种架构简化了部署，降低了集成复杂度，并优化了本地运行性能。

**1.4 解决的问题:**

- 为 Agent 应用提供一种按需、上下文感知的规则生成机制。
- 简化 Agent 的规则管理，避免维护庞大的静态规则文件。
- 提供一个易于集成到现有 Python 应用中的规则生成解决方案。
- 支持本地开发、测试和运行，无需额外部署服务。
**2. 目标与目的 (Goals and Objectives)**

- **主要目标:** 提供一个稳定、可靠、易于使用的 `cddrg_engine` Python 库，实现 CDDRG 范式的核心功能。
- **次要目标:**
- 支持通过配置文件灵活配置知识源、数据库路径、模型和 Prompt。
- 提供清晰的 API 接口 (`initialize`, `generate_rules`)。
- 实现高效的本地知识索引和检索。
- 确保与主流 LLM API 的兼容性。
- 提供全面的日志记录能力，方便调试和监控。
- **衡量指标 (示例):**
- `generate_rules` 函数平均本地处理时间（不含 LLM 网络延迟） < 500ms。
- 知识库索引（首次）时间与知识库大小成合理比例。
- API 接口文档覆盖率 > 95%。
- 单元测试覆盖率 > 80%。
- 成功集成到至少一个示例 Agent 应用中。
**3. 目标用户 (Target Audience)**

- **主要用户:** 使用 Python 开发 AI Agent 或自动化脚本的开发者。
- **次要用户:** 需要为特定应用定制规则生成逻辑的技术研究人员或架构师。
**4. 范围 (Scope)**

**4.1 In-Scope (库提供的功能):**

- **配置加载:** 从指定文件加载配置 (YAML 或 .env)。
- **知识索引管道 (Knowledge Indexing Pipeline):**
- 扫描本地文件系统指定的知识源目录。
- 对文本文件进行分块 (Chunking)。
- 调用 Embedding 模型进行向量化。
- 将向量和元数据存入本地向量数据库 (ChromaDB)。
- 将文件的元数据（路径、处理时间等）存入本地 SQLite 数据库。
- **核心 API 函数:**
- `initialize(config_path)`: 加载配置，初始化连接，运行（或检查）知识索引。
- `generate_rules(command, parameters, context)`: 接收命令、参数和上下文，执行规则生成流程。
- **内部逻辑组件:**
- 知识检索器 (Knowledge Retriever): 根据输入从向量库和元数据存储中检索相关知识片段。
- Prompt 引擎 (Prompt Engine): 使用模板，将命令、上下文和检索到的知识组装成发送给 LLM 的 Prompt。
- LLM 客户端 (LLM Client): 与配置的外部 LLM API 进行交互（发送 Prompt，接收响应，处理错误）。
- 响应格式化器 (Response Formatter): 解析 LLM 响应，将其格式化为预定义的结构（如 JSON、指令列表）返回给调用者。
- **本地存储交互:** 与本地 ChromaDB 文件和 SQLite 文件进行交互。
- **日志记录:** 提供可配置的日志记录功能。
**4.2 Out-of-Scope (库不负责的功能):**

- **Agent 应用程序本身:** 调用 `cddrg_engine` 的宿主应用程序的逻辑。
- **用户界面 (UI/CLI):** 任何用户交互界面都由 Agent 应用程序提供。
- **知识源内容的创建和管理:** 库只负责读取和索引，不负责内容的编写。
- **规则冲突的自动解决:** 库可能在 Prompt 中要求 LLM 识别冲突，但本身不实现解决逻辑。
- **规则执行:** 库只生成规则，不负责执行。
- **网络服务部署与管理:** 本库设计为嵌入式，不作为独立服务运行。
- **复杂的访问控制或多租户:** 假设在单用户或受信任的环境中运行。
**5. 用例 (Use Cases)**

- **UC-01: 初始化 CDDRG 引擎**
- **Actor:** Agent 应用程序 (启动时) 或 维护脚本
- **Preconditions:** 配置文件存在，知识源文件存在。
- **Flow:**
1. Agent 代码调用 `cddrg_engine.initialize(config_path='path/to/config.yaml')`。
1. 库加载配置。
1. 库检查本地向量库和元数据存储的状态（或根据配置强制重新索引）。
1. **如果需要索引:**
a. 库启动知识索引管道。
b. 扫描知识源目录。
c. 处理文件（分块、向量化）。
d. 写入向量库 (ChromaDB) 和元数据存储 (SQLite)。
e. 记录索引过程日志。
1. 库完成初始化，准备接收 `generate_rules` 调用。
1. (可选) `initialize` 返回状态信息（如索引是否运行，知识库大小等）。
- **UC-02: Agent 请求动态规则**
- **Actor:** Agent 应用程序 (执行任务时)
- **Preconditions:** `cddrg_engine` 已成功初始化。
- **Flow:**
1. Agent 准备好 `command` (e.g., "/create_prd"), `parameters` (e.g., `{'project': 'X', 'features': ['A', 'B']}`), `context` (e.g., `{'user_role': 'architect', 'timestamp': ...}`).
1. Agent 代码调用 `ruleset = cddrg_engine.generate_rules(command, parameters, context)`。
1. 库接收输入。
1. **知识检索器:** 根据输入查询向量库和元数据存储，获取相关知识片段。
1. **Prompt 引擎:** 使用配置的模板，将命令、参数、上下文和检索到的知识组装成最终的 Prompt。
1. **LLM 客户端:** 将 Prompt 发送给外部 LLM API。
1. LLM API 返回响应。
1. **响应格式化器:** 解析 LLM 响应，提取或转换成预定义的规则格式（如 JSON）。
1. 库将格式化后的 `ruleset` 返回给 Agent。
1. Agent 使用 `ruleset` 继续执行任务。
1. 库记录本次调用的关键信息和结果日志。
- **UC-03: 更新知识源**
- **Actor:** 规则/知识维护者
- **Flow:**
1. 维护者在文件系统中添加、修改或删除知识源文件。
1. 维护者运行一个脚本（或 Agent 的某个管理功能）再次调用 `cddrg_engine.initialize()`，可能带有强制重新索引的参数。
1. 库重新执行知识索引管道，更新向量库和元数据存储以反映变化。
**6. 功能需求 (Functional Requirements)**

- **FR-LIB-INIT-01: **`**initialize**`** 函数:**
- 必须接受配置文件路径作为参数。
- 必须加载并验证配置。
- 必须根据配置初始化向量库和元数据存储客户端。
- 必须触发或管理知识索引管道的执行（根据策略：首次运行、强制更新、检查更新）。
- 必须处理初始化过程中的错误（如配置错误、路径无效）并返回或抛出异常。
- **FR-LIB-GEN-01: **`**generate_rules**`** 函数:**
- 必须接受 `command` (str), `parameters` (dict), `context` (dict) 作为输入。
- 必须按顺序调用内部组件：知识检索器 -> Prompt 引擎 -> LLM 客户端 -> 响应格式化器。
- 必须能处理内部组件可能发生的错误（如检索失败、LLM API 错误）。
- 必须返回格式化后的规则集（格式需可配置，默认为 JSON）。
- 必须是线程安全的（如果 Agent 应用是多线程的）。
- **FR-IDX-01: 知识索引 - 文件扫描:** 必须能递归扫描配置文件中指定的本地知识源目录。
- **FR-IDX-02: 知识索引 - 文件处理:** 必须支持处理常见的文本文件格式 (e.g., .md, .txt)。必须根据配置的策略进行文本分块。
- **FR-IDX-03: 知识索引 - 向量化:** 必须使用配置的 Embedding 模型（通过 Langchain 或类似库）生成向量。
- **FR-IDX-04: 知识索引 - 存储:** 必须将向量和元数据（来源文件、chunk ID 等）写入配置的本地 ChromaDB 实例。必须将文件级元数据写入配置的本地 SQLite 数据库。
- **FR-IDX-05: 知识索引 - 增量更新 (可选):** 理想情况下，索引管道应能识别已更改的文件并只更新相关的索引，而非每次都全量重建（需要基于文件修改时间或内容哈希）。
- **FR-CONF-01: 配置加载:** 必须支持从 YAML 或 .env 文件加载配置。
- **FR-CONF-02: 配置项:** 必须支持配置项如：知识源路径、向量库路径、SQLite 路径、Embedding 模型名称/端点、LLM 模型名称/端点/API Key、Prompt 模板路径或内容、检索 Top-K 值、日志级别等。
- **FR-RET-01: 知识检索:** 必须实现基于输入向量在 ChromaDB 中执行相似性搜索的逻辑。
- **FR-RET-02: 知识检索 - 过滤 (可选):** 必须支持在检索时结合元数据（从 SQLite 或向量库本身获取）进行过滤。
- **FR-PROM-01: Prompt 引擎:** 必须支持从文件或配置中加载 Prompt 模板。必须能将变量（命令、参数、上下文、检索到的知识）注入模板。
- **FR-LLM-01: LLM 客户端:** 必须支持与 OpenAI API 兼容的接口或其他配置的 LLM API。必须处理 API 请求、响应和常见错误（如超时、认证失败、速率限制）。必须能配置重试逻辑。
- **FR-RESP-01: 响应格式化:** 必须能解析 LLM 返回的文本（通常是 JSON 字符串或 Markdown），并将其转换为 Python 对象（如 dict, list）。必须能处理解析错误。
- **FR-LOG-01: 日志记录:** 必须使用标准的 Python `logging` 模块。必须记录关键操作、配置信息、错误和警告。日志级别必须可配置。
- **FR-ERR-01: 错误处理:** 库函数应通过返回特定错误代码/对象或抛出自定义异常来向调用者报告错误。
**7. 非功能需求 (Non-Functional Requirements)**

- **NFR-PERF-01: 性能:** `generate_rules` 的本地处理时间应尽可能短，不应成为 Agent 响应的瓶颈。索引性能应在可接受范围内。
- **NFR-ACC-01: 准确性:** 规则生成的准确性高度依赖于知识源质量、Prompt 设计和 LLM 能力。库本身应确保流程正确执行。
- **NFR-REL-01: 可靠性:** 库应能稳定运行，妥善处理文件 I/O 和网络 API 错误。
- **NFR-USAB-01: API 易用性:** `initialize` 和 `generate_rules` 接口应简单直观，文档清晰。
- **NFR-MAINT-01: 可维护性:** 代码应遵循 Python 最佳实践，模块化，包含单元测试。
- **NFR-SEC-01: 安全性:** API Keys 等敏感信息必须通过安全的配置方式（如环境变量、配置文件权限）管理，不应硬编码。库不应引入额外的安全风险。
- **NFR-PORT-01: 可移植性:** 库应能在主流操作系统（Linux, macOS, Windows）上运行。
**8. 数据需求 (Data Requirements)**

- **配置文件 (YAML 示例):**
```yaml
knowledge_source:
  path: ./knowledge_base
  include_patterns: ["*.md", "*.txt"]
vector_store:
  provider: chromadb
  path: ./db/chroma_db
  collection_name: cddrg_rules
metadata_store:
  provider: sqlite
  path: ./db/metadata.db
embeddings:
  provider: openai # or huggingface, etc.
  model: text-embedding-ada-002
  # api_key: $OPENAI_API_KEY (loaded from env)
llm:
  provider: openai
  model: gpt-4-turbo-preview
  # api_key: $OPENAI_API_KEY
  temperature: 0.5
prompt:
  template_file: ./prompts/rule_gen_template.txt
retrieval:
  top_k: 5
logging:
  level: INFO
  file: ./logs/cddrg_engine.log

```

- **SQLite Schema (示例):**
- `indexed_files` (file_path TEXT PRIMARY KEY, last_modified REAL, content_hash TEXT, indexed_at TIMESTAMP)
- `knowledge_chunks` (chunk_id TEXT PRIMARY KEY, file_path TEXT, chunk_text TEXT, vector_id TEXT) -- 可选，如果向量库不存文本
- **Vector Store (ChromaDB) Schema:**
- Collection: `cddrg_rules` (可配置)
- Stored Objects: Vectors, IDs
- Metadata per vector: `rule_id` (or `chunk_id`), `source_file`, `node` (if available from source), `item` (if available) etc.
- **输出规则格式 (示例 JSON):**
```json
{
  "status": "success", // or "error"
  "rules": [
    {"step": 1, "instruction": "Use the PRD template located at /templates/prd_v2.md", "severity": "mandatory"},
    {"step": 2, "check": "Ensure 'Non-Functional Requirements' section exists", "severity": "mandatory"},
    {"step": 3, "action": "Store final document in /docs/prd/{year}/", "parameters": {"year": 2023}, "severity": "mandatory"},
    {"step": 4, "action": "Request review from 'Product Manager'", "severity": "recommended"}
  ],
  "errors": null // or error message if status is "error"
  "raw_llm_response": "..." // optional, for debugging
}

```

**9. 假设与依赖 (Assumptions and Dependencies)**

- **假设:**
- Agent 应用程序使用 Python 3.8+。
- 运行环境具有访问本地文件系统的权限。
- 运行环境具有访问外部 LLM API 的网络连接。
- 知识源主要是文本格式。
- **依赖:**
- Python 3.8+
- 核心库: `langchain` (或类似框架用于集成), `openai` (或其他 LLM SDK), `chromadb-client`, `sqlite3`, `pyyaml` (或 `python-dotenv`), `tiktoken` (或相应 tokenizer)。
- 有效的 LLM API Key 和 Embedding 模型访问权限。
**10. 未来的考虑/开放问题 (Future Considerations / Open Questions)**

- 如何优化索引策略以支持大规模知识库和快速增量更新？
- 是否需要支持除 ChromaDB 和 SQLite 之外的其他本地存储选项？
- 如何更好地处理 LLM 的幻觉或不准确的响应？(增加验证层？)
- 是否应该在库内部提供更明确的冲突标记（基于 LLM 的判断）？
- 如何打包和分发这个库 (`setup.py`, PyPI)？
- 是否需要异步版本的 `generate_rules` 函数 (`async def`)？
- 如何支持本地运行的 Embedding 和 LLM 模型？
---

