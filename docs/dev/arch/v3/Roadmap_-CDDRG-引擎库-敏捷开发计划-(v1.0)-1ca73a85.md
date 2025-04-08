# Roadmap: CDDRG 引擎库 - 敏捷开发计划 (v1.0)

**产品:** CDDRG 引擎库 (`cddrg_engine`)
**开发周期:** 3-6 个月 (假设资源到位)
**迭代周期:** 2 周

---

**Roadmap: CDDRG 引擎库 - 敏捷开发计划 (v1.0)**

**核心史诗 (Epics):**

- **E01: 基础架构与配置** (Foundation & Configuration)
- **E02: 知识索引与向量化** (Knowledge Indexing & Vectorization)
- **E03: 知识检索与查询优化** (Knowledge Retrieval & Query Optimization)
- **E04: 规则表示与动态生成** (Rule Representation & Dynamic Generation)
- **E05: 规则冲突检测** (Rule Conflict Detection)
- **E06: 缓存与性能优化** (Caching & Performance)
- **E07: 知识更新与循环** (Knowledge Update & Loop)
- **E08: API、文档与打包** (API, Documentation & Packaging)

---

**Milestone 1: 核心引擎骨架与知识入口 (约 4-6 周)**

- **目标:** 搭建基础项目结构，实现基本配置加载、知识源扫描和初步的向量化存储。
- **Issues / Stories / Tasks:**
- **E01:**
- **Task 1.1:** 初始化 Python 项目 (uv, Ruff, Mypy, Pytest)。
- **Task 1.2:** 设计并实现配置加载模块 (Pydantic + YAML/dotenv)。
- **Task 1.3:** 搭建基础日志记录模块。
- **Task 1.4:** 设计 `cddrg_engine` 的 Facade API 接口 (`initialize`, `generate_rules` 骨架)。
- **E02:**
- **Task 2.1:** 设计知识源扫描器 (扫描指定目录，识别文件类型)。
- **Task 2.2:** 实现基于 Langchain/LlamaIndex 的文档加载器 (支持 .md, .txt)。
- **Task 2.3:** 实现文本分块策略 (e.g., RecursiveCharacterTextSplitter)。
- **Task 2.4:** 集成 Embedding 模型客户端 (e.g., OpenAI, Sentence Transformers)。
- **Task 2.5:** 实现基础向量化流程 (将文本块转换为向量)。
- **Task 2.6:** 集成 ChromaDB 客户端，实现将向量和基础元数据 (chunk_id, source_file) 存入本地 ChromaDB。
- **Task 2.7:** 实现基础的知识索引管道 (`Knowledge Indexing Pipeline`) 骨架，串联扫描、加载、分块、向量化、存储流程。
- **E08:**
- **Task 8.1:** 编写 Milestone 1 相关的基本单元测试。
**Milestone 2: 知识检索与初步规则生成 (约 4-6 周)**

- **目标:** 实现根据输入进行知识检索，并能调用 LLM 生成初步的（非结构化）规则响应。
- **Issues / Stories / Tasks:**
- **E02:**
- **Task 2.8:** 设计并实现元数据存储 (SQLite) Schema (存储文件信息，可选的块元数据)。
- **Task 2.9:** 在知识索引管道中添加元数据存储写入逻辑。
- **E03:**
- **Task 3.1:** 实现 `Knowledge Retriever` 基础版本：根据输入文本（命令/参数/上下文）向量化后，在 ChromaDB 中执行 top-k 相似性搜索。
- **Task 3.2:** （优化）实现基于元数据的预过滤/后过滤检索逻辑 (e.g., 只检索特定类型或标签的知识)。
- **E04:**
- **Task 4.1:** 实现 `Prompt Engine` 基础版本：加载 Prompt 模板，将输入和检索到的知识注入模板。
- **Task 4.2:** 集成 LLM 客户端 (e.g., OpenAI API)，实现发送 Prompt 和接收响应。
- **Task 4.3:** 实现 `Response Formatter` 基础版本 (直接返回 LLM 的原始文本响应)。
- **Task 4.4:** 在 `generate_rules` API 中串联检索、Prompt 构建、LLM 调用流程。
- **E08:**
- **Task 8.2:** 编写 Milestone 2 相关的单元测试和集成测试（模拟 LLM）。
**Milestone 3: 结构化规则与动态文档理念 (约 4-6 周)**

- **目标:** 定义结构化的规则表示（按 Item 存储），支持动态文档块（Block）的概念，并让 LLM 返回结构化规则。
- **Issues / Stories / Tasks:**
- **E02:**
- **Task 2.10:** **(动态文档)** 设计文档块 (Block) 的元数据表示（e.g., block_id, type, tags, content_hash），可在 Markdown Front Matter 或特定标记中定义。
- **Task 2.11:** **(动态文档)** 更新知识索引管道，以识别和索引文档块，并将块元数据存入 SQLite 和/或 ChromaDB 元数据。
- **Task 2.12:** **(动态文档)** 更新 `Knowledge Retriever` 以支持按块 ID 或块属性进行检索。
- **E04:**
- **Task 4.5:** **(规则构建)** 设计规则 Item 的结构化表示 (e.g., JSON Schema: `id`, `type`, `condition`, `action`, `severity`, `source_block_id`)。
- **Task 4.6:** **(规则构建)** 更新 Prompt 模板，明确要求 LLM 根据检索到的知识（包括块信息）生成符合该 Schema 的**结构化规则列表 (JSON)**。
- **Task 4.7:** **(规则构建)** 增强 `Response Formatter`，使其能解析 LLM 返回的 JSON 字符串，验证其 Schema，并将其转换为 Python 对象。
- **Task 4.8:** **(规则构建)** 思考如何在知识源中直接定义一些基础/静态的规则 Item，并被索引。
- **E08:**
- **Task 8.3:** 编写 Milestone 3 相关的单元测试（Schema 验证、块处理）。
**Milestone 4: 规则冲突检测 (约 4-6 周)**

- **目标:** 实现基于 LLM 的规则冲突检测机制。
- **Issues / Stories / Tasks:**
- **E05:**
- **Task 5.1:** 设计冲突检测流程：是在 `generate_rules` 内部对新生成的规则集进行自我检查，还是提供单独的冲突检查接口？**（初步定为在 **`**generate_rules**`** 后进行检查）**
- **Task 5.2:** 实现冲突对筛选逻辑：如何选择可能冲突的规则对进行比较？（e.g., 语义相似的规则 Item，影响同一实体的规则）。这可能需要利用向量相似性或结构化属性。
- **Task 5.3:** 设计冲突检测的 Prompt 模板，引导 LLM 分析给定的规则对（结构化表示 + 来源上下文）是否存在矛盾。
- **Task 5.4:** 实现调用 LLM 进行冲突分析的逻辑。
- **Task 5.5:** 设计并实现冲突结果的存储（e.g., 在 SQLite 中记录冲突对 ID、LLM 解释）。
- **Task 5.6:** （可选）将冲突信息整合回 `generate_rules` 的返回结果中。
- **E08:**
- **Task 8.4:** 编写冲突检测相关的测试用例（构造已知冲突和非冲突的规则对）。
**Milestone 5: 缓存、知识更新与初步循环 (约 4-6 周)**

- **目标:** 实现缓存机制，支持知识库的更新，并建立初步的知识循环（索引日志）。
- **Issues / Stories / Tasks:**
- **E06:**
- **Task 6.1:** 设计缓存键生成策略（考虑命令、参数、上下文、可能还有知识片段）。
- **Task 6.2:** 实现 `Cache Manager`，集成可配置的缓存后端（优先 SQLite）。
- **Task 6.3:** 在 `generate_rules` 流程中集成缓存检查和写入逻辑。
- **E07:**
- **Task 7.1:** **(知识更新)** 实现知识索引管道的增量更新能力（基于文件修改时间或哈希值，避免全量索引）。
- **Task 7.2:** **(知识更新)** 定义旧知识处理策略（当文件被删除或内容大幅改变时，如何处理相关的索引和向量？标记为废弃？删除？）。
- **Task 7.3:** **(知识循环)** 确定 Agent 执行日志的格式和存储位置。
- **Task 7.4:** **(知识循环)** 配置知识索引管道，使其能够处理和索引 Agent 执行日志文件。
- **Task 7.5:** （验证）测试知识检索是否能包含来自日志的信息，并观察其对规则生成的影响。
- **E08:**
- **Task 8.5:** 编写缓存和知识更新相关的测试。
**Milestone 6: API 完善、文档、打包与发布 v1.0 (约 2-4 周)**

- **目标:** 完善 API 接口，编写用户文档和 API 文档，打包库，准备发布第一个稳定版本。
- **Issues / Stories / Tasks:**
- **E03:**
- **Task 3.3:** （优化）评估并可能实现更高级的检索策略 (e.g., HyDE, Reranking)。
- **E04 & E05:**
- **Task 4.9 / 5.7:** 根据测试反馈，优化 Prompt 模板以提高规则生成和冲突检测的准确性。
- **E08:**
- **Task 8.6:** 完善 `initialize` 和 `generate_rules` 的错误处理和返回状态码。
- **Task 8.7:** 编写用户指南（如何配置、使用库）。
- **Task 8.8:** 生成 API 参考文档 (e.g., 使用 Sphinx 或 MkDocs + mkdocstrings)。
- **Task 8.9:** 准备 `setup.py` 或 `pyproject.toml` 文件，用于库的打包。
- **Task 8.10:** 执行端到端测试，确保所有功能按预期工作。
- **Task 8.11:** 打包并发布 `cddrg_engine` v1.0 版本。

---

**总任务数:** 约 41 个 (在 50 个以内)。

**说明:**

- 这是一个高级别的 Roadmap，每个 Task 可能需要分解为更小的子任务。
- 时间估算非常粗略，实际需要根据团队规模和效率调整。
- 强调迭代：每个 Milestone 的产出应该是可测试、可演示的部分功能。允许在后续 Milestone 中根据反馈进行调整和优化。
- “知识图谱”概念主要体现在结构化元数据存储 (SQLite) 和对关系/实体的理解（体现在 Prompt 和 LLM 的推理中），暂未引入独立的图数据库。如果需要，可在后续版本规划。
- “动态文档”的核心是按 Block 索引和检索，允许更细粒度的知识利用。
- “规则构建”侧重于结构化表示和 LLM 生成。
- “知识更新”和“知识循环”是 M5 的重点，确保系统能学习和适应。
这个 Roadmap 提供了一个清晰的、分阶段的交付计划，有助于团队聚焦核心价值，并逐步构建出强大的 `cddrg_engine` 库。
