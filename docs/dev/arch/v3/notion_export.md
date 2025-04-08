# Research for VibeCopilot

[📑 动态开发文档系统](1ca73a85-7f76-805a-a1bd-d4322960c2c0)

**版本:** 1.0
**日期:** 2023年10月27日
**作者:** (你的名字/团队)

**1. 引言**

- **1.1 背景:**
当前开发团队维护着大量的开发文档，包括架构设计、API 规范、开发指南、操作手册等。随着项目的快速迭代和代码库的演进，文档的更新、重命名和重组变得频繁。现有的文档管理方式（例如，直接基于文件系统或简单的 Wiki）导致以下痛点：
- **链接失效:** 文档间的相互引用（链接）在源文件或目标文件被移动、重命名或删除时，极易失效，导致信息断裂。
- **维护成本高:** 手动查找和修复失效链接耗时耗力，尤其在文档规模庞大时。
- **信息一致性难保证:** 难以追踪某个文档被哪些其他文档所引用，导致更新时可能遗漏相关依赖。
- **版本追踪困难:** 难以清晰地标识和管理文档的废弃与替代关系。
- **1.2 产品目标:**
构建一个“动态开发文档系统”，旨在解决上述问题，实现：
- **链接健壮性:** 确保文档间的引用链接在文档结构调整时保持有效。
- **维护自动化:** 自动化链接的生成、验证和更新提示。
- **内容结构化:** 通过标准化元数据提升文档的可管理性。
- **版本可追溯:** 清晰地管理文档的生命周期（活跃、废弃、替代）。
- **提升效率:** 降低文档维护成本，提高开发者查找和信任信息的效率。
- **1.3 目标用户:**
- **主要用户:**
- 软件开发者（阅读、编写、更新文档）
- 软件架构师（设计、撰写、评审架构文档）
- 技术文档工程师（规划、撰写、维护文档体系）
- DevOps 工程师（集成文档构建到 CI/CD 流程）
- **次要用户:**
- 测试工程师（参考功能规格、API 定义）
- 产品经理（了解技术实现细节）
- 新员工（快速学习项目知识）
- **1.4 核心理念:**
采用“文档即代码 (Docs-as-Code)”的理念，将文档视为项目代码的一部分进行管理，并引入持久化标识符和自动化构建流程来保证文档的动态性和健壮性。
**2. 功能需求 (Features)**

- **2.1 持久化唯一标识符 (Persistent ID)**
- **描述:** 系统中的每一个可独立引用的文档单元（通常对应一个 Markdown 文件）必须被分配一个全局唯一且持久不变的标识符 (ID)。此 ID 不应随文件名或路径的改变而改变。
- **要求:**
- FE-1.1: 支持在文档源文件（如 Markdown Front Matter）中定义 `id` 字段。
- FE-1.2: 构建系统需能在构建时检查并强制 `id` 的唯一性，若发现重复则报错。
- FE-1.3: `id` 格式应简洁、易于引用（例如，`arch-overview`, `api-auth-v2`）。
- **2.2 基于 ID 的内部链接**
- **描述:** 作者在文档中使用特定的、基于 ID 的语法来引用系统内的其他文档，而非易变的相对/绝对路径。
- **要求:**
- FE-2.1: 定义清晰的内部链接语法，例如 `[[target-doc-id]]` 或 `[链接文本](doc:target-doc-id)`。
- FE-2.2: 该语法应能方便地在 Markdown 中书写。
- **2.3 自动化链接解析与生成**
- **描述:** 在文档发布（构建）过程中，系统自动将基于 ID 的内部链接转换为最终用户可访问的、正确的 URL 链接。
- **要求:**
- FE-3.1: 构建脚本需扫描所有文档，提取 `id` 和对应的最终输出路径 (slug/URL)。
- FE-3.2: 构建脚本需维护一个 `id` 到 URL 的映射索引（可基于 SQLite）。
- FE-3.3: 构建脚本需在处理 Markdown 内容时，查找内部链接语法，并使用索引将其替换为标准的 HTML `<a>` 标签，链接文本默认为目标文档的标题（或允许自定义）。
- FE-3.4: 链接解析过程需高效，不应显著拖慢整体构建时间。
- **2.4 链接有效性验证**
- **描述:** 在构建过程中自动检查所有内部链接，确保其指向的 `id` 真实存在。
- **要求:**
- FE-4.1: 如果内部链接指向一个在索引中不存在的 `id`，构建过程必须失败，并明确报告哪个文件的哪个链接无效。
- **2.5 文档状态管理与废弃处理**
- **描述:** 支持标记文档的状态（如：活跃、草稿、已废弃），并能指定已废弃文档的新替代文档。
- **要求:**
- FE-5.1: 支持在文档元数据中定义 `status` 字段 (e.g., `active`, `deprecated`, `draft`)。
- FE-5.2: 支持在文档元数据中定义 `replaced_by` 字段，其值为替代文档的 `id` (当 `status` 为 `deprecated` 时)。
- FE-5.3: 当一个内部链接指向 `status` 为 `deprecated` 的文档时，构建系统应能：
- (选项 A - 推荐) 自动将链接重定向到 `replaced_by` 指定的新文档 URL。
- (选项 B) 在生成的链接旁边显示 "(已废弃)" 标记，并提供一个指向 `replaced_by` 文档的附加链接。
- (选项 C) 构建失败，强制要求作者更新链接。 (具体策略需讨论决定)
- FE-5.4: (可选) 废弃的文档页面本身也应有明显标记，并引导用户前往新文档。
- **2.6 结构化元数据**
- **描述:** 强制或推荐在文档中使用标准化的元数据（Front Matter），以支持系统功能和未来的扩展。
- **要求:**
- FE-6.1: 必须包含的元数据：`id`, `title`。
- FE-6.2: 推荐包含的元数据：`status`, `replaced_by`, `tags`, `version_added`, `last_updated` 等。
- FE-6.3: 构建系统可选择性地验证元数据的完整性或格式。
- **2.7 文档发布与展现 (基于 Docusaurus)**
- **描述:** 提供一个统一的、现代化的 Web 门户来发布和展现所有开发文档。
- **要求:**
- FE-7.1: 利用 Docusaurus 生成静态文档网站。
- FE-7.2: 提供清晰的导航结构（侧边栏、顶部导航）。
- FE-7.3: 提供全文搜索功能。
- FE-7.4: 支持代码高亮、Mermaid 图表等常用技术文档特性。
- FE-7.5: 支持版本化文档 (Docusaurus 内建功能)。
- **2.8 (高级) 自动化文本链接分析 (可选 V2.0)**
- **描述:** 自动分析文档正文中的纯文本，识别可能指向其他文档标题或 ID 的内容，并建议或自动转换为 ID 链接。
- **要求:**
- FE-8.1: 开发 Python 脚本，使用 Markdown 解析库分析文档 AST。
- FE-8.2: 脚本能将文本与已知文档的 `id` 或 `title` (存储在 SQLite 索引中) 进行匹配。
- FE-8.3: 提供报告，列出潜在的、未转换的文本链接。
- FE-8.4: (可选) 提供交互式工具或命令，帮助作者批量转换这些文本为 ID 链接。
- **2.9 (高级) 链接关系数据库与报告 (可选 V2.0)**
- **描述:** 将文档间的链接关系存储到数据库中，用于分析和报告。
- **要求:**
- FE-9.1: 构建脚本在解析链接时，将 `(source_doc_id, target_doc_id)` 关系存入 SQLite 数据库的 `links` 表。
- FE-9.2: 提供脚本或工具，基于此数据库生成报告，例如：
- 哪些文档链接到了特定文档 X？
- 哪些文档是“孤岛”（没有入链或出链）？
- 可视化文档引用关系图。
**3. 非功能性需求 (Non-Functional Requirements)**

- **3.1 易用性 (Usability):**
- 对作者：编写体验接近标准 Markdown，ID 链接语法简单直观。元数据易于理解和填写。
- 对读者：文档网站导航清晰，搜索准确，阅读体验良好。
- **3.2 可靠性 (Reliability):**
- 链接解析和生成必须 100% 准确。
- 链接验证过程必须可靠，能捕获所有无效链接。
- **3.3 性能 (Performance):**
- 文档构建时间应在可接受范围内（具体指标需根据文档规模确定）。
- 生成的文档网站加载速度快。
- **3.4 可维护性 (Maintainability):**
- 自定义的 Python 脚本代码应结构清晰、有注释、易于维护和扩展。
- Docusaurus 配置应遵循最佳实践。
- **3.5 可扩展性 (Scalability):**
- 系统应能支持未来文档数量的增长，而性能不会急剧下降。
- 架构应允许未来添加更多自动化分析或集成功能。
- **3.6 集成性 (Integration):**
- 能够方便地集成到现有的 CI/CD 流程中（例如，在代码合并前自动构建和验证文档）。
**4. 技术架构概要**

- **内容格式:** Markdown + YAML Front Matter
- **版本控制:** Git (文档与代码同仓库)
- **静态站点生成器 (SSG):** Docusaurus v2/v3
- **自动化脚本:** Python 3.x
- **构建时索引/数据库:** SQLite 3
- **核心流程:**

1. 开发者在本地使用 Markdown 编写/修改文档，定义 Front Matter (`id` 等)。
1. 使用 `[[doc-id]]` 语法进行内部链接。
1. 提交到 Git。
1. CI/CD 触发（或本地手动触发）构建流程：
a. Python 脚本扫描所有文档，解析 Front Matter，构建/更新 SQLite 索引 (`id` -> metadata, path)。
b. Python 脚本 (或 Docusaurus 插件) 遍历 Markdown 文件：
i. 验证元数据。
ii. 查找 `[[doc-id]]` 链接。
iii.查询 SQLite 索引，验证 `id` 并获取目标信息。
iv. 处理废弃逻辑。
v. 将 `[[doc-id]]` 替换为 HTML 链接。
vi. (可选) 进行文本链接分析和关系存储。
c. 如果验证通过，调用 Docusaurus 构建命令生成静态网站。
d. 部署静态网站。
1. 用户通过 Web 浏览器访问 Docusaurus 站点。
**5. 成功指标 (Success Metrics)**

- **量化指标:**
- 构建过程中检测到的无效内部链接数量（目标：随时间推移趋近于 0）。
- 因文档链接问题导致的工单或开发者求助次数（目标：显著减少）。
- 文档构建成功率（目标：接近 100%，失败主要由真实的内容错误或无效链接导致）。
- **定性指标:**
- 开发者/用户关于查找信息效率和文档可靠性的满意度调查得分（目标：提升）。
- 技术文档工程师维护文档（特别是重构和更新）的效率反馈（目标：提升）。
**6. 未来考虑 / 超出范围 (Out of Scope for V1.0)**

- **未来考虑:**
- 实现高级功能 FE-8 (文本链接分析) 和 FE-9 (链接关系数据库与报告)。
- 可视化文档依赖图。
- 与项目管理工具（如 JIRA）的集成。
- 更细粒度的内容引用（例如，引用文档中的某个段落或代码块）。
- 基于内容的语义搜索。
- **超出范围 (V1.0):**
- 实时协作编辑功能。
- 复杂的文档审批工作流。
- 非开发类文档的管理（如市场、销售文档）。
- 完整的所见即所得 (WYSIWYG) 编辑器。

---

[📑 AI 驱动的规则冲突检测系统](1ca73a85-7f76-8004-b986-fadc0e6b741f)

**AI 驱动的规则冲突检测系统**

**版本:** 1.0
**日期:** 2023年10月27日
**作者:** [你的名字/团队]

**1. 概述 (Overview)**

**1.1 背景:**
随着系统（尤其是由 Agent 或 LLM 驱动的系统）依赖的规则集日益复杂和分散，手动维护规则一致性、检测潜在冲突变得极其困难且容易出错。规则可能分布在不同的文档、由不同人员编写、使用不同的术语描述相似的概念。当规则被修改或添加时，可能无意中引入与现有规则矛盾的指令，导致系统行为异常或不可预测。

**1.2 目标产品:**
本产品旨在构建一个自动化系统，利用结构化规则定义、向量化语义搜索和大型语言模型 (LLM) 的分析能力，在规则创建或修改时自动检测潜在的冲突。系统将帮助规则维护者及时发现并解决不一致之处，确保规则库的整体协调性。

**1.3 核心理念:**
将规则视为包含特定“实体”（概念、对象、动作、属性）的陈述。当一条规则被修改时，系统通过向量相似性检索与之相关的其他规则（即讨论相似实体的规则），并将这些规则对提交给 LLM 进行深度语义分析，以判断是否存在冲突。

**1.4 解决的问题:**

- 手动检查规则冲突耗时耗力且易遗漏。
- 不同文档、不同作者、不同术语表达的规则难以关联和比较。
- 规则变更时，难以评估其对整个规则体系的影响。
- 为基于规则的 Agent 提供更可靠、一致的行为基础。
**2. 目标与目的 (Goals and Objectives)**

- **主要目标:** 自动化检测规则库中的语义冲突，降低人工审核负担。
- **次要目标:**
- 提高规则库的一致性和可靠性。
- 缩短规则维护周期。
- 在规则变更时提供即时反馈，减少错误引入。
- 为下游系统（如 Agent 执行引擎）提供经过一致性检查的规则基础。
- **衡量指标 (示例):**
- 规则冲突检测的召回率（发现真实冲突的能力） > 80% (需持续优化)。
- 规则冲突检测的精确率（报告的冲突中真实冲突的比例） > 60% (需持续优化，允许一定的误报，人工确认)。
- 规则修改后冲突检测的平均响应时间 < 10 秒。
- 减少因规则冲突导致的线上事故/Agent 行为异常 X%。
**3. 目标用户 (Target Audience)**

- 规则制定者与维护者 (如系统管理员、流程设计师、知识库管理员)
- 软件架构师、开发人员 (在定义系统行为规则时)
- 依赖规则库执行任务的 Agent 或自动化系统的开发者/运维者
**4. 范围 (Scope)**

**4.1 In-Scope (包含功能):**

- **规则定义接口:** 支持结构化（如 Node-Item 结构，通过 Markdown Front Matter 或特定格式）和自然语言描述的规则输入。
- **规则持久化:** 将结构化元数据和规则文本存储在数据库中 (如 SQLite)。
- **规则向量化:** 在规则创建/修改时，自动将规则的关键部分（如描述、实体属性值）向量化。
- **向量存储与索引:** 将向量及关联元数据存储在向量数据库中。
- **冲突检测引擎:**
- 触发机制：在规则保存时自动触发。
- 相关规则检索：基于向量相似性查找可能冲突的规则。
- LLM 分析：调用 LLM API，提交潜在冲突规则对进行分析。
- 冲突结果解析与存储：解析 LLM 返回结果，存储检测到的冲突信息（冲突规则对 ID、冲突描述）。
- **冲突报告:** 提供界面或报告，展示检测到的潜在冲突列表。
**4.2 Out-of-Scope (不包含功能):**

- **规则的自动修复/解决:** 系统仅负责检测和报告冲突，解决冲突需要人工介入。
- **完整的规则执行引擎:** 本系统专注于规则的一致性检查，不负责执行规则。
- **复杂的规则版本控制系统:** 依赖外部版本控制系统（如 Git）进行历史追踪。
- **高级用户权限管理:** 初期假设所有用户有权查看和管理规则及冲突。
- **非文本规则的冲突检测:** 初期主要处理基于文本描述的规则。
**5. 用例 (Use Cases)**

- **UC-01: 创建新规则并检测冲突**
- **Actor:** 规则维护者
- **Flow:**

1. 维护者使用指定格式（如 Markdown + Front Matter）创建一条新规则，包含结构化字段 (Node, Item, 实体描述如 `entity: storage`, `attribute: location`, `value: 'doc/'`) 和自然语言描述。
1. 维护者保存规则。
1. 系统触发：
a. 解析规则，存储结构化数据到 SQLite。
b. 向量化规则的关键描述或实体信息。
c. 将向量存入向量数据库。
d. 在向量数据库中搜索与新规则语义相似的现有规则。
e. 将新规则与检索到的每条相关规则组成对，提交给 LLM 进行冲突分析。
f. 解析 LLM 响应，如果发现冲突，记录到冲突数据库 (SQLite)。
g. 向维护者显示保存成功信息，并提示发现 X 条潜在冲突（或无冲突）。

- **UC-02: 修改现有规则并检测冲突**
- **Actor:** 规则维护者
- **Flow:**

1. 维护者打开并编辑一条现有规则。
1. 维护者保存修改。
1. 系统触发：
a. 更新 SQLite 中的结构化数据。
b. 重新向量化规则的修改部分。
c. 更新向量数据库中的对应向量。
d. 执行与 UC-01 步骤 3.d - 3.g 相同的冲突检测流程（将修改后的规则视为“新”规则进行比较）。

- **UC-03: 查看规则冲突报告**
- **Actor:** 规则维护者
- **Flow:**

1. 维护者访问冲突报告界面/功能。
1. 系统从冲突数据库 (SQLite) 查询所有未解决/活动的冲突记录。
1. 系统以列表形式展示冲突，每条记录包含：

- 冲突涉及的规则 ID (可链接到规则详情)。
- LLM 提供的冲突描述。
- 检测时间。
- 冲突状态 (如: New, Acknowledged, Resolved - 状态管理可选)。
**6. 功能需求 (Functional Requirements)**

- **FR-01: 规则结构定义:**
- 系统必须支持通过 Markdown Front Matter 定义规则的结构化元数据。
- 必须包含字段：`id` (唯一标识符), `node` (所属节点/分类), `item` (具体条目名), `description` (自然语言描述)。
- (推荐) 支持定义规则中的核心实体、属性和值，例如：`entity_focus: storage`, `attribute: location`, `value: 'doc/'` 或 `condition: 'user_role == architect'` 等，以便更精确地向量化和分析。
- **FR-02: 规则存储:**
- 系统必须将规则的结构化元数据（来自 Front Matter）存储在关系型数据库 (SQLite) 中，便于快速查询和过滤。
- 系统必须存储规则的原始文本内容（或其路径）。
- **FR-03: 规则向量化:**
- 系统必须在规则创建或修改时，自动提取规则的关键文本部分（如 `description` 和定义的 `entity/attribute/value` 组合）进行向量化。
- 必须使用指定的 Embedding 模型（需配置）。
- **FR-04: 向量存储:**
- 系统必须将生成的向量及其关联的 `rule_id` 和其他必要元数据存储在向量数据库中。
- 向量数据库必须支持高效的相似性搜索。
- **FR-05: 冲突检测触发:**
- 系统必须在规则成功保存到主存储（SQLite 和文件）后自动触发冲突检测流程。
- **FR-06: 相关规则检索:**
- 冲突检测流程必须首先根据被修改/创建规则的向量，在向量数据库中检索 top-k 个语义最相似的其他规则。`k` 值应可配置。
- (可选) 可以结合 SQLite 查询，检索结构上相关（如同一 `node` 下，或影响同一 `entity_focus`）的规则，作为补充或过滤。
- **FR-07: LLM 冲突分析:**
- 系统必须将被修改/创建的规则文本与每个检索到的相关规则文本，打包成 Prompt 发送给配置的 LLM API。
- Prompt 设计必须清晰引导 LLM 判断是否存在冲突，并解释冲突原因。示例 Prompt 结构:

```plain text
Analyze potential conflict between Rule 1 and Rule 2.
Rule 1 (ID: {id1}, Node: {node1}, Item: {item1}): "{text1}"
Rule 2 (ID: {id2}, Node: {node2}, Item: {item2}): "{text2}"
Does Rule 2 contradict, override, or create inconsistency with Rule 1 regarding actions, conditions, requirements, or outcomes for the same subject or context (e.g., both define storage location but specify different paths like 'doc/' vs 'dev/')?
Respond with:
Conflict: YES | NO
Explanation: {Brief explanation of why or why not, detailing the conflicting aspects if YES}

```

- 系统必须能解析 LLM 返回的结构化（或半结构化）响应，提取冲突判断 (YES/NO) 和解释。
- **FR-08: 冲突记录:**
- 如果 LLM 判断存在冲突 (YES)，系统必须将冲突信息（涉及的规则 ID 对、LLM 提供的解释、检测时间戳）存储在 SQLite 的 `rule_conflicts` 表中。
- 应避免重复记录完全相同的冲突对（基于规则 ID 对）。
- **FR-09: 冲突展现:**
- 系统必须提供一个界面或命令行工具，允许用户查看当前活动的（未解决的）冲突列表。
- 列表应清晰展示冲突涉及的规则 ID 和 LLM 的解释。
- **FR-10: 配置:**
- 系统应允许配置使用的 Embedding 模型、向量数据库连接信息、LLM API Endpoint 及 Key、相似性搜索的 `k` 值、LLM Prompt 模板（可选）。
**7. 非功能需求 (Non-Functional Requirements)**

- **NFR-01: 性能:**
- 单个规则修改后的冲突检测过程（从保存到返回冲突提示）应在用户可接受的时间内完成（目标 < 10 秒，取决于 LLM 响应速度和 k 值）。
- 向量数据库的查询性能应能支持预期的规则库规模。
- **NFR-02: 准确性:**
- 冲突检测应优先保证高召回率（尽可能找出潜在冲突），允许一定的误报率，由人工确认。目标是显著减少漏报。
- **NFR-03: 可靠性:**
- 系统应能稳定处理 LLM API 的暂时性故障或超时（如重试机制、错误记录）。
- 数据库操作应保证事务性。
- **NFR-04: 可扩展性:**
- 系统应能处理预期增长的规则数量（例如，支持数千到数万条规则）。
- 架构设计应允许未来替换或增加不同的 Embedding 模型、向量数据库或 LLM。
- **NFR-05: 可维护性:**
- 代码应模块化，易于理解和修改。
- 应有充分的日志记录冲突检测过程和与外部 API 的交互。
- **NFR-06: 安全性:**
- LLM API Key 等敏感配置信息必须安全存储。
- 若涉及用户数据，需考虑数据隐私。
**8. 数据需求 (Data Requirements)**

- **SQLite Schema (示例):**
- `rules` (id TEXT PRIMARY KEY, node TEXT, item TEXT, description TEXT, file_path TEXT, last_modified TIMESTAMP, vector_hash TEXT)
- `rule_entities` (rule_id TEXT, entity_type TEXT, entity_value TEXT) -- 可选，用于结构化实体
- `rule_conflicts` (conflict_id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id_1 TEXT, rule_id_2 TEXT, llm_explanation TEXT, detected_at TIMESTAMP, status TEXT DEFAULT 'new')
- **Vector Database Schema (示例):**
- 存储对象：向量 (embedding), 关联的 `rule_id`, 规则文本 chunk (可选), 其他元数据 (如 `node`, `item`, 用于过滤)。
**9. 假设与依赖 (Assumptions and Dependencies)**

- **假设:**
- 规则以可被脚本解析的格式（如 Markdown + Front Matter）存储。
- 规则的自然语言描述包含足够的信息来判断潜在冲突。
- 用户有能力理解并解决 LLM 报告的冲突。
- **依赖:**
- 可用的 Embedding 模型服务/库。
- 可用的向量数据库服务/库。
- 可用的 LLM API 服务 (如 OpenAI, Anthropic, 或本地部署模型)。
- Python 环境及相关库 (Langchain, DB drivers, etc.)。
**10. 未来的考虑/开放问题 (Future Considerations / Open Questions)**

- 如何优化 LLM Prompt 以提高准确性并减少成本？
- 如何处理更复杂的、涉及多条规则（>2条）的连锁冲突？
- 是否需要支持冲突的严重性评级？
- 是否需要一个更丰富的 UI 来可视化规则关系和冲突？
- 如何处理规则的版本历史与冲突的关系？
- 如何定义和利用更复杂的“实体”关系进行检索？
- 是否需要引入规则优先级或覆盖机制来自动处理某些类型的冲突？

---

[📑 白皮书：命令驱动的动态规则生成——赋能下一代智能体自主性与适应性](1ca73a85-7f76-8018-a333-dae4250885a1)

**版本:** 0.9 (草案)
**日期:** 2023年10月27日
**作者:** [你的名字/团队名称] & AI 助手

**摘要**

随着人工智能（AI）智能体（Agent）在自动化任务中扮演日益重要的角色，如何有效指导和约束其行为成为关键挑战。传统的静态规则库方法在面对复杂、多变的环境时，暴露了维护成本高、适应性差、上下文感知能力弱等诸多弊端。本文提出了一种全新的范式——**命令驱动的动态规则生成 (Command-Driven Dynamic Rule Generation, CDDRG)**。该范式不再依赖于预先定义和维护庞大的细粒度规则集，而是通过定义高层级的“源命令” (Source Commands)，让智能体在执行任务时，按需向一个智能化的“规则生成接口” (Rule Generation Interface, RGI) 查询，由 RGI 结合当前上下文动态地生成一套适用的、具体的执行规则。这种方法旨在显著降低规则维护复杂度，提高智能体的上下文适应能力和执行效率，为实现更高级别的自主自动化铺平道路。本文将详细阐述 CDDRG 的核心理念、架构组件、关键优势、面临的挑战以及潜在应用前景。

**1. 引言：智能体自动化时代的规则困境**

AI 智能体正被广泛应用于从软件开发、IT 运维到业务流程自动化的各个领域。为了确保这些智能体按照预期、安全、合规地执行任务，通常需要为其设定一套行为规则。然而，当前主流的基于静态规则库的方法正面临严峻挑战：

- **维护噩梦:** 规则数量随系统复杂度爆炸式增长，手动创建、更新、验证和维护这些规则变得极其耗时且容易出错。
- **僵化与脆弱:** 静态规则难以适应快速变化的环境、新的业务需求或未预见的情况，导致智能体行为僵化甚至错误。
- **上下文缺失:** 预定义的规则往往缺乏对具体执行上下文（如用户角色、输入数据特性、当前系统状态）的精细感知，难以做出最优决策。
- **冲突频发:** 在庞大且分散的规则库中，检测和解决规则之间的潜在冲突是一项艰巨的任务。
这些限制严重阻碍了智能体发挥其全部潜力，无法真正实现高效、灵活、智能的自主操作。我们需要一种新的范式来克服这些障碍。

**2. 解决方案：命令驱动的动态规则生成 (CDDRG) 范式**

我们提出“命令驱动的动态规则生成”（CDDRG）作为下一代智能体指导框架。其核心思想是：**从“预先规定一切”转向“按需智能推断”**。

该范式包含以下关键要素和工作流程：

- **源命令 (Source Commands):** 定义一组高层级的、面向意图的命令，作为智能体可执行动作的起点。这些命令封装了核心任务目标，例如 `/create prd` 或 `/deploy service`。
- **智能体 (Agent):** 接收源命令和相关参数后，并不直接执行。它的首要任务是理解命令意图，并打包当前上下文信息。
- **规则生成接口 (Rule Generation Interface - RGI):** 这是系统的智能核心。Agent 将命令和上下文信息发送给 RGI。RGI 负责：
- **理解意图与上下文:** 解析命令的深层含义和执行环境。
- **知识检索与推理:** 访问其背后的知识源（如策略文档、最佳实践库、知识图谱、微调模型），根据当前情况推理出完成任务所需的具体步骤、约束、标准和参数。
- **动态规则生成:** 实时生成一套为**本次特定执行量身定制**的规则集（可能是自然语言指令、结构化数据或配置片段）。此过程可能包含对潜在冲突的内部检查。
- **规则返回:** 将生成的临时规则集发送回 Agent。
- **知识源 (Knowledge Sources):** RGI 进行推理的基础。这不再是传统意义上的规则库，而是更灵活、更抽象的知识集合，如组织策略、行业标准、设计原则、成功案例库等。
- **智能体执行:** Agent 接收到动态生成的规则集，并将其作为本次任务执行的具体指南。
**[概念图占位符：一个流程图展示命令 -> Agent -> RGI (连接知识源) -> 动态规则 -> Agent 执行]**

**3. CDDRG 的核心组件详解**

- **源命令:** 设计简洁、意图明确，参数化以适应不同场景。它们是人与智能体交互的主要接口。
- **智能体:** 需要具备基本的命令解析、上下文收集、与 RGI 通信以及理解并执行 RGI 返回规则的能力。
- **规则生成接口 (RGI):**
- **技术核心:** 很可能基于强大的大型语言模型 (LLM)，结合检索增强生成 (RAG)、知识图谱查询、甚至符号逻辑推理能力。
- **关键能力:** 上下文理解、多源知识融合、逻辑推理、冲突感知（自我校验）、结构化/非结构化规则生成。
- **可配置性:** 其推理逻辑、知识源访问方式、输出格式应可配置和调整。
- **知识源:**
- **形式多样:** 可以是文档库、数据库、API、经过微调的模型等。
- **质量关键:** 知识源的准确性、完整性、及时性直接决定了生成规则的质量。需要配套的知识管理流程。
**4. CDDRG 范式的关键优势与价值**

采用 CDDRG 范式将带来显著的变革性优势：

- **大幅降低维护成本:** 从维护海量细则转向维护核心命令和更高层级的知识源，极大简化管理负担。
- **卓越的上下文适应性:** 生成的规则天然契合当前执行环境，使智能体行为更智能、更精准。
- **增强的灵活性与弹性:** 系统能更快地适应策略变更和环境变化，只需更新知识源或 RGI 逻辑。
- **提高执行效率与质量:** 动态生成的规则可能比通用静态规则更优化，指导智能体采取更有效的行动路径，并嵌入最新的质量标准。
- **促进知识显性化与重用:** 鼓励将隐性的组织知识（策略、最佳实践）结构化、数字化，使其成为可被 RGI 利用的资产。
- **迈向更高阶的自主性:** 使智能体不仅仅是规则的执行者，更是在指导下的“思考者”，为实现更复杂的自主任务奠定基础。
**5. 面临的挑战与缓解策略**

CDDRG 范式也带来了新的挑战：

- **可控性与可预测性:** 动态生成增加了不确定性。
- **缓解:** 引入“护栏”规则（核心静态规则 RGI 必须遵守）、严格的测试验证、对 RGI 输出进行模式约束。
- **一致性保障:** 相似输入应产生相似规则。
- **缓解:** 优化 RGI 推理逻辑的稳定性、引入缓存机制、对关键任务进行模板化生成。
- **可解释性与可审计性:** 难以追溯“错误规则”的来源。
- **缓解:** 记录 RGI 的推理过程（检索到的知识、关键决策点）、对生成的规则进行快照存档、开发可视化调试工具。
- **隐式冲突检测:** 冲突可能发生在推理层面。
- **缓解:** 让 RGI 在生成时进行自我冲突检查、对生成的规则集应用后置的（快速）冲突检测逻辑。
- **知识源管理:** 需要新的方法论。
- **缓解:** 建立清晰的知识管理流程、使用版本控制、定期评估知识源质量。
- **技术复杂度与性能:** RGI 设计复杂，实时生成可能引入延迟。
- **缓解:** 采用高效的 AI 模型和推理引擎、优化知识检索、异步生成或预热机制。
**6. 应用场景与前景展望**

CDDRG 范式适用于各种需要智能体根据复杂、变化的环境执行任务的场景：

- **软件开发生命周期 (SDLC):** 动态生成代码审查标准、部署流程、测试用例生成规则。
- **IT 运维 (ITOps):** 根据告警上下文生成故障排查步骤、资源调整策略、安全响应规则。
- **业务流程自动化 (BPA):** 动态生成订单处理规则、客户服务脚本、合规性检查清单。
- **个性化服务:** 为每个用户动态生成内容推荐规则、交互流程。
- **机器人流程自动化 (RPA):** 指导机器人根据屏幕内容和任务目标动态调整操作步骤。
展望未来，随着 RGI 智能程度的提升和知识源的不断丰富，CDDRG 有望实现：

- **更强的自适应与自学习能力:** RGI 能从执行结果中学习，持续优化规则生成逻辑。
- **跨领域知识融合:** RGI 能整合来自不同领域的知识，生成更全面的解决方案。
- **人机协作新模式:** 人类负责设定目标（源命令）和提供高级知识，AI 负责动态规划和执行细节。
**7. 结论**

静态规则库的时代正在接近尾声。命令驱动的动态规则生成 (CDDRG) 提供了一条通往更智能、更灵活、更易于管理的智能体自动化未来的道路。它将规则管理的焦点从繁琐的细节维护转移到更高层次的意图定义、知识构建和智能推理上。虽然面临挑战，但 CDDRG 范式所蕴含的巨大潜力使其成为未来智能系统设计中值得投入和探索的关键方向。我们相信，拥抱 CDDRG 将是释放 AI 智能体全部能力、推动自动化迈向新高度的关键一步。

---

[📑 产品需求文档 (PRD): CDDRG 引擎库 (嵌入式)](1ca73a85-7f76-80ce-9cbb-c65699816207)

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

[📑 系统架构报告: CDDRG 引擎库 (嵌入式)](1ca73a85-7f76-808f-b526-e6c5975b806c)

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

[📑 工作流程: 命令驱动的智能开发协作 (基于 CDDRG)](1ca73a85-7f76-80c8-b276-d8f4f3658b1b)

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

[📑 Roadmap: CDDRG 引擎库 - 敏捷开发计划 (v1.0)](1ca73a85-7f76-80e1-bbfb-cbe2b4387af3)

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

[📑 技术选型报告: CDDRG 引擎及支撑生态系统](1ca73a85-7f76-80d8-9971-dcdd105e60b2)

**版本:** 1.0
**日期:** 2023年10月27日
**作者:** [你的名字/团队] & AI 助手

**1. 引言**

本报告旨在为“命令驱动的动态规则生成”（CDDRG）引擎库 (`cddrg_engine`) 及其相关的 Agent 应用、知识管理和文档系统提供一套推荐的技术选型。选型原则优先考虑 Python 生态的成熟度、社区活跃度、性能、易用性、可扩展性，并尽可能结合已有的技术偏好和优秀的开源解决方案。目标是构建一个高效、可靠、易于维护的技术栈，支持 CDDRG 范式的实现。

**2. 核心引擎库 (**`**cddrg_engine**`**) 技术选型**

- **编程语言:** **Python 3.10+**
- **理由:** 广泛的 AI/ML 生态系统（Langchain, Transformers, etc.），成熟的 Web 框架和工具链，社区支持强大，符合团队偏好。选用较新版本以利用类型提示、性能改进等新特性。
- **包管理与虚拟环境:** **uv**
- **理由:** 新一代的 Python 包管理工具，以其极高的速度和 `pip` + `venv` 的兼容性著称，能显著提升开发和依赖管理的效率，符合团队偏好。
- **核心框架/编排:** **Langchain** 或 **LlamaIndex**
- **理由:** 两者都是强大的 LLM 应用开发框架，提供了构建 RAG（检索增强生成）、Agent、Prompt 管理、模型集成、文档加载、文本分割等核心功能的抽象和工具链。
- **选型考量:**
- **Langchain:** 功能更全面，社区更大，集成度高，更灵活但也可能更复杂。适合需要高度定制和编排复杂流程的场景。
- **LlamaIndex:** 更专注于 RAG 和知识库构建与查询，API 可能更简洁直观，尤其在数据索引和检索方面有优势。
- **建议:** 根据对 RAG 性能和易用性的侧重程度选择。**初步倾向 Langchain**，因其更广泛的工具集可能对 Prompt Engine、LLM Client 等组件的实现更有利，但 LlamaIndex 也可以作为备选或混合使用（例如，用 LlamaIndex 做知识检索，用 Langchain 做流程编排）。
- **向量数据库 (本地):** **ChromaDB**
- **理由:** 开源，专为 AI 应用设计，API 友好（尤其与 Langchain/LlamaIndex 集成良好），支持本地文件存储模式，易于嵌入和部署，满足本地优先的需求。性能对于中小型知识库足够。
- **备选:** FAISS (Facebook AI Similarity Search) + 本地存储。性能可能更高，但集成和管理相对复杂。
- **元数据存储 (本地):** **SQLite**
- **理由:** 轻量级、无需单独服务器、文件 기반、Python 内建支持 (`sqlite3` 模块)，易于嵌入。非常适合存储文件索引信息、缓存元数据等结构化但不需要高并发的场景。
- **配置管理:** **Pydantic** + **PyYAML** / **python-dotenv**
- **理由:** Pydantic 提供强大的数据验证和设置管理能力，结合 YAML 或 .env 文件，可以实现类型安全、结构清晰的配置加载。
- **缓存实现:**
- **内存缓存:** Python 内建 `functools.lru_cache` 或 `cachetools` 库。简单高效，适合进程内缓存。
- **磁盘缓存 (文件/SQLite):** 标准库 `shelve` (简单 key-value)，或使用 SQLite 实现更结构化的缓存表，或使用 `diskcache` 库。提供持久化。
- **建议:** 提供可配置选项，**默认为 SQLite 缓存**，兼顾持久性和查询能力。
- **LLM & Embedding 模型客户端:**
- **LLM:** `openai` Python 库 (用于 OpenAI/Azure OpenAI), `anthropic` 库 (用于 Claude), `google-generativeai` (用于 Gemini), 或通过 `litellm` 统一多种 API 接口。
- **Embeddings:** `openai` 库, `sentence-transformers` (Hugging Face 模型), `google-generativeai`。
- **建议:** 使用 **Langchain/LlamaIndex 提供的模型抽象接口**，可以方便地切换底层模型和客户端库。优先支持 OpenAI 和开源模型 (通过 Hugging Face)。
- **日志记录:** Python 内建 `logging` 模块。
- **理由:** 标准库，灵活可配置，生态兼容性好。
- **任务编排/工作流 (库内部，如果复杂):** `Prefect` 或 `Dagster` (如果需要更复杂的依赖管理和可视化，但可能增加库的重量级)。对于简单线性流程，标准 Python 函数调用即可。
- **建议:** **初期保持简单**，直接使用 Python 函数编排。
**3. Agent 应用技术选型**

- **编程语言:** **Python 3.10+** (与引擎库保持一致)
- **包管理与虚拟环境:** **uv**
- **核心框架:** 取决于 Agent 的形态。
- **命令行工具:** `Typer` 或 `Click`。提供优雅的 CLI 参数解析和命令组织。
- **桌面应用:** `PyQt` 或 `PySide` (Qt), `Tkinter` (简单), `CustomTkinter` (现代 UI)。
- **Web 服务/API:** `FastAPI` 或 `Flask`。`FastAPI` 性能高，基于 Pydantic，与类型提示结合好。
- **后台服务:** 标准库 `multiprocessing`, `threading` 或 `Celery` (分布式任务队列)。
- **引擎集成:** 直接 `import cddrg_engine` 并调用其 API。
- **日志存储:** 本地文件、SQLite 或发送到中央日志系统 (如 ELK Stack, Graylog)。
**4. 文档系统选型 (用于人类阅读的规则/知识/开发文档)**

- **框架:** **Docusaurus**
- **理由:** 基于 React，现代化的静态站点生成器，特别适合项目文档和知识库。支持 MDX (Markdown + JSX)，版本控制，搜索 (Algolia)，主题化，插件丰富，社区活跃。符合团队偏好。
- **内容格式:** **Markdown / MDX**
- **理由:** 易于编写和版本控制，Docusaurus 原生支持。MDX 允许嵌入 React 组件，增强交互性。
- **部署:** 静态文件部署到 GitHub Pages, Netlify, Vercel, 或自托管服务器 (Nginx/Apache)。
**5. 知识图谱/记忆库方案选型 (用于 **`**/memory**`** 命令沉淀结构化知识)**

- **核心概念:** 需要一个能存储结构化关系数据的系统，用于记录工作流实例、关键实体及其关系。
- **方案 1: 图数据库 (如果关系复杂且需要深度图查询)**
- **选型:** **Neo4j** (最流行，Cypher 查询语言强大) 或 **ArangoDB** (多模型数据库，支持图、文档、键值)。
- **优点:** 专业图存储，高效处理复杂关系查询（如查找相似工作流模式、依赖链分析）。
- **缺点:** 需要额外部署和维护数据库服务，学习曲线较陡。
- **方案 2: 关系型数据库 + JSON (如果关系相对简单或初期)**
- **选型:** **PostgreSQL** (功能强大，支持 JSONB 查询) 或 **SQLite** (如果规模不大且本地运行)。
- **实现:** 设计 Schema 来存储核心实体（任务、计划、报告、人员）和它们之间的关系表。复杂属性或非结构化信息可以存入 JSON 字段。
- **优点:** 技术栈更统一（如果已使用 RDBMS），易于上手。
- **缺点:** 复杂的图遍历查询性能可能不如原生图数据库。
- **方案 3: 向量数据库 + 元数据 (利用现有技术栈)**
- **选型:** **ChromaDB** (或其他向量库)
- **实现:** 将每个工作流实例或关键事件（如 commit, review）表示为一个“记忆”文档，包含结构化元数据和自然语言描述。向量化描述，存入向量库。通过元数据过滤和语义相似性搜索来检索相关记忆。
- **优点:** 技术栈复用，能进行语义层面的记忆检索（“查找类似问题的解决方案”）。
- **缺点:** 难以进行精确的多步关系查询，结构化程度不如前两者。
- **建议:** **初期或中小型项目，优先考虑方案 2 (SQLite/PostgreSQL + JSON)**，技术栈更统一，易于实现。**如果图关系分析是核心需求且复杂度高，再考虑引入 Neo4j (方案 1)**。方案 3 可以作为补充，用于语义检索，但不适合作为主要的结构化记忆存储。**对于 **`**/memory**`** 命令，输出结构化的 JSON 数据，由 Agent 应用负责将其写入选定的记忆库（SQLite/PostgreSQL/Neo4j）**。
**6. 其他推荐开源库**

- **文本处理:** `NLTK`, `spaCy` (如果需要更高级的 NLP 功能，如实体识别、词性标注，用于知识提取或 Prompt 构建)。
- **文件操作:** 标准库 `os`, `pathlib`, `shutil`。
- **数据序列化:** 标准库 `json`, `pickle` (注意安全风险)。
- **单元测试:** `pytest` (功能强大，插件丰富)。
- **代码格式化与检查:** `Black`, `Ruff` (速度极快，集成了 Flake8, isort 等多种工具)。
- **类型检查:** `Mypy`。
**7. 技术栈总结图 (简化)**

```mermaid
graph TD
    subgraph User Facing
        UI[Agent UI (CLI/GUI/Web)]
        DOC[Documentation (Docusaurus)]
    end

    subgraph Agent Application (Python + uv)
        AGENT_CORE[Agent Core Logic (Typer/FastAPI/PyQt)]
        CDDRG_LIB(cddrg_engine Library);
        AGENT_CORE -- Uses --> CDDRG_LIB;
        AGENT_CORE -- Interacts --> MEMORY_WRITER[Memory Writer];
    end

    subgraph CDDRG Engine Library (Python + uv)
        ENGINE_FACADE[Facade API];
        FRAMEWORK[Langchain/LlamaIndex];
        VECTOR_DB_CLIENT[Vector DB Client (ChromaDB)];
        METADATA_CLIENT[Metadata Client (SQLite)];
        CACHE_MGR[Cache Manager];
        LLM_CLIENT[LLM & Embedding Clients];
        CONFIG[Config (Pydantic)];
        LOGGING[Logging];
        ENGINE_FACADE -- Uses --> FRAMEWORK;
        FRAMEWORK -- Uses --> VECTOR_DB_CLIENT;
        FRAMEWORK -- Uses --> METADATA_CLIENT;
        FRAMEWORK -- Uses --> LLM_CLIENT;
        ENGINE_FACADE -- Uses --> CACHE_MGR;
        ENGINE_FACADE -- Uses --> CONFIG;
        %% ... other internal connections
    end

    subgraph Data & Knowledge Stores
        KNOWLEDGE_SRC[Knowledge Files (FS)];
        VECTOR_DB[Vector DB (ChromaDB File)];
        METADATA_DB[Metadata DB (SQLite File)];
        CACHE_STORE[Cache Store (SQLite/File)];
        MEMORY_DB[Memory Store (SQLite/Postgres/Neo4j)];
        CONFIG_FILE[Config File (YAML/.env)];
    end

    subgraph External Services
        LLM_API[LLM & Embedding API];
    end

    UI --> AGENT_CORE;
    AGENT_CORE --> KNOWLEDGE_SRC; %% Agent writes logs which become knowledge
    CDDRG_LIB --> KNOWLEDGE_SRC; %% Engine reads knowledge
    CDDRG_LIB --> VECTOR_DB;
    CDDRG_LIB --> METADATA_DB;
    CDDRG_LIB --> CACHE_STORE;
    CDDRG_LIB -- Network --> LLM_API;
    MEMORY_WRITER --> MEMORY_DB;

    %% Styling
    style User Facing fill:#ccf
    style Agent Application fill:#cff
    style CDDRG Engine Library fill:#ffc
    style Data & Knowledge Stores fill:#cfc
    style External Services fill:#fcc


```

**8. 结论**

本报告提出了一套基于 Python 生态、结合团队偏好和优秀开源库的技术选型方案。核心是采用 Python + uv + Langchain/LlamaIndex + ChromaDB + SQLite 构建 `cddrg_engine` 嵌入式库。文档使用 Docusaurus，知识记忆库推荐初期使用 SQLite/PostgreSQL。该技术栈在性能、易用性、可维护性和生态系统支持方面取得了良好的平衡，为成功实现 CDDRG 范式提供了坚实的技术基础。后续应根据原型开发和具体性能测试结果进行微调。

[📑 VibeCopilot 项目概述](1ca73a85-7f76-80c2-b17b-eeb464c44330)

好的，我们来评估一下 `VibeCopilot` 项目 ([https://github.com/jacobcy/VibeCopilot](https://github.com/jacobcy/VibeCopilot)) 与我们设定的 CDDRG 引擎目标之间的差距。

- **目标:** 旨在成为一个基于 RAG (Retrieval-Augmented Generation) 和 LLM 的 AI 编码助手。
- **核心功能:**
- 读取和理解项目代码库。
- 用户提出编码相关的问题或请求。
- 系统检索代码库中的相关信息 (RAG)。
- 将问题和检索到的上下文发送给 LLM (如 GPT)。
- 展示 LLM 生成的答案、代码建议或解释。
- **技术栈 (可能):** Python, LLM API (OpenAI), 向量数据库 (用于 RAG), 文件系统交互。
- **关注点:** 代码理解、代码生成、回答编程问题。
**与 CDDRG 引擎目标的差距分析:**

**1. 核心目标的差异 (最显著的差距):**

- **VibeCopilot:** **直接辅助编码/回答问题。** 其输出是代码片段、解释或解决方案，供开发者直接使用或参考。
- **CDDRG Engine:** **生成指导 Agent 执行任务的动态规则。** 其输出是一套指令、约束或步骤（可能是结构化的 JSON 或自然语言列表），Agent *依据这些规则* 去完成一个更高层次的任务（如 `/create prd`, `/deploy service`）。CDDRG 是一个“元工具”，指导行动；VibeCopilot 是一个“执行/辅助工具”。
**2. 动态规则生成与结构化:**

- **VibeCopilot:** LLM 的目标是理解代码并生成相关代码/文本。Prompt 可能类似于 "根据这段代码，解释 X" 或 "为 Y 功能生成 Python 代码"。
- **CDDRG Engine:** 需要精心设计的 Prompt 来引导 LLM **推理**并**生成特定格式的规则集**。例如："根据命令`/task`，参数 Z，以及检索到的知识(策略A, 最佳实践B, 历史日志C)，生成完成此任务的步骤列表(JSON格式)，包含条件和必要检查点。"
- **差距:** VibeCopilot 缺少专门用于 *生成执行规则* 的 Prompt 工程和逻辑。它也不需要 CDDRG 要求的**结构化规则输出** (如 JSON Schema) 和相应的响应格式化器 (`Response Formatter`)。
**3. 知识源的多样性与知识循环:**

- **VibeCopilot:** 主要知识源是**项目代码**，可能包括少量文档。
- **CDDRG Engine:** 知识源设计上更为广泛，包括**策略文档、最佳实践指南、PRD、计划、历史执行日志、测试报告、Review 记录、开发博客**等。至关重要的**知识循环**（将 Agent 执行日志反馈回知识库进行索引）在 VibeCopilot 中似乎没有体现。
- **差距:** VibeCopilot 的知识范围较窄，缺乏利用和学习历史执行经验的机制。
**4. 规则表示与动态文档 (Block 存储):**

- **VibeCopilot:** 将知识视为代码文件或文档整体。
- **CDDRG Engine:** 引入了更细粒度的概念：
- **规则 (Item 存储):** 最终生成的规则应有结构化表示。
- **动态文档 (Block 存储):** 知识源文档可以被分解为带有元数据的 Block 进行索引和检索，以支持更精确的知识定位和引用。
- **差距:** VibeCopilot 的知识索引和表示可能不够细粒度，不支持按结构化 Item 或 Block 进行管理和检索。
**5. 规则冲突检测:**

- **VibeCopilot:** 不涉及规则冲突检测。代码建议的正确性由开发者判断。
- **CDDRG Engine:** **冲突检测是核心功能之一。** 需要实现筛选潜在冲突规则对（基于语义或结构）、调用 LLM 进行分析、存储和报告冲突的完整逻辑。
- **差距:** VibeCopilot 完全缺少此模块。
**6. 缓存机制:**

- **VibeCopilot:** 可能有简单的 LLM 调用缓存，但规则生成的缓存需求（基于命令、参数、上下文、知识片段）更为复杂和关键。
- **CDDRG Engine:** 需要专门的 `Cache Manager` 和策略来优化 `generate_rules` 的性能和一致性。
- **差距:** VibeCopilot 的缓存需求和实现可能与 CDDRG 不同或缺失。
**7. 知识更新策略:**

- **VibeCopilot:** 可能只在启动时或手动触发时重新索引代码库。
- **CDDRG Engine:** 需要更健壮的知识更新机制，包括**增量索引**和处理**旧知识/文档废弃**的策略。
- **差距:** 对知识库动态更新和版本管理的需求更为复杂。
**8. 架构与 API (嵌入式库):**

- **VibeCopilot:** 可能是一个独立的 CLI 工具、服务或 IDE 插件。
- **CDDRG Engine:** 明确设计为**可嵌入的 Python 库 (**`**cddrg_engine**`**)**，提供清晰的 `initialize` 和 `generate_rules` API 供 Agent 应用调用。
- **差距:** VibeCopilot 的项目结构和暴露的接口可能与 CDDRG 的库化目标不同。
**9. 人机交互模式:**

- **VibeCopilot:** 典型的“提问-回答”模式。
- **CDDRG Engine:** 支持更复杂的“指令-生成规则-**人类确认**执行-记录”模式。引擎需要生成适合人类审核的规则表示。
- **差距:** CDDRG 对人机交互环节有更明确的设计和支撑需求。
**总结:**

`VibeCopilot` 项目提供了一个很好的 **RAG 技术基础**，这与 CDDRG 引擎所需的技术栈有显著重叠（Python, RAG, LLM, Vector Store）。这是一个不错的起点。

然而，两者在**核心目标、功能范围和设计理念**上存在巨大差距：

- **目标差异:** 代码辅助 vs. 动态规则生成指导。
- **核心功能缺失:** 结构化规则生成、冲突检测、知识循环、面向规则的缓存、细粒度知识表示（Block/Item）、知识更新策略等在 VibeCopilot 中基本没有体现。
- **架构差异:** 嵌入式库 vs. 可能的应用形态。
- **知识范围差异:** 代码为主 vs. 多样化知识源（含日志）。
**结论:**

可以将 `VibeCopilot` 视为 CDDRG 引擎所需技术的一个**早期原型或技术验证**，特别是在 RAG 实现方面。但要达到 CDDRG 的目标，需要在 VibeCopilot 的基础上进行**大量的重构、功能添加和概念调整**。

**下一步建议:**

1. **复用基础:** 可以借鉴 VibeCopilot 在文件读取、基础 RAG 流程（向量化、检索）、LLM 客户端交互方面的实现。
1. **核心重塑:** 重点开发 CDDRG 独有的模块：

- 重新设计 Prompt Engine，目标是生成规则而非代码/答案。
- 实现 Response Formatter 以处理结构化规则输出。
- 构建 Conflict Detection 模块。
- 扩展知识索引管道以支持多样化来源和 Block 结构。
- 实现 Cache Manager。
- 设计并实现知识更新和循环逻辑。

1. **架构调整:** 将核心逻辑封装成符合设计目标的 `cddrg_engine` Python 库。
1. **知识管理:** 建立管理策略、日志等多样化知识源的流程。
VibeCopilot 提供了一个起点，但通往功能完备的 CDDRG 引擎还需要大量的开发工作。

[📑 源命令和基础规则](1ca73a85-7f76-80bf-9eb8-ef49a229f8f5)

我们来为 CDDRG 设计一套更通用、更结构化、更符合动态规则生成范式的源命令和基础规则（或称为“元规则”/原则）。这套设计将兼顾项目开发场景，但也具备一定的泛化能力，并能作为 Agent 与 `cddrg_engine` 交互的基础。

**设计原则:**

1. **命令驱动:** 以动词开头的命令明确表达用户意图。
1. **参数化:** 命令接受参数以适应具体场景。
1. **上下文感知:** 引擎在生成规则时应考虑传递的上下文。
1. **关注“做什么”而非“怎么做细节”:** 命令描述目标，具体步骤由引擎动态生成。
1. **可扩展性:** 基础命令集应易于扩展，添加新的命令。
1. **与知识循环结合:** 命令的执行结果（日志、产出）应能反哺知识库。
1. **支持人机交互:** 设计应考虑人类审核环节。

---

**CDDRG 源命令与基础原则 (v1.0)**

**A. 核心源命令 (Source Commands)**

这些命令是用户与 Agent 交互的主要入口，触发规则生成和任务执行。

- `**/plan <goal_description> [using <source_docs>] [with_context <key=value_pairs>]**`
- **意图:** 为一个目标或需求制定计划。
- **示例:** `/plan Implement user authentication using /docs/req/auth_req.md with_context project=phoenix priority=high`
- **引擎职责:** 生成任务分解、步骤定义、资源估算、风险识别等规划规则。知识源可能包括项目管理模板、历史计划、需求文档。
- **输出:** 工作计划草稿（结构化或文本）。
- `**/create <artifact_type> "<artifact_name>" [based_on <source_artifacts>] [with_template <template_id>] [with_context <key=value_pairs>]**`
- **意图:** 创建一个新的工件（文档、代码模块、配置等）。
- **示例:** `/create prd "User Profile Feature" based_on /docs/req/profile_req.md with_template prd_standard_v2`
- **引擎职责:** 生成创建该类型工件的具体规则，包括内容结构、必填项、格式规范、质量标准、参考示例等。
- **输出:** 工件草稿。
- `**/execute <task_description_or_id> [from_plan <plan_id>] [with_inputs <input_data>] [with_context <key=value_pairs>]**`
- **意图:** 执行一项具体的任务（可能由 Agent 自动完成，或指导人类执行）。
- **示例:** `/execute Implement login API endpoint from_plan plan_auth_v1 with_context tech_stack=python/fastapi`
- **引擎职责:** 生成执行该任务的具体步骤、技术规范、编码标准、测试要求、日志记录规则等。
- **输出:** 任务执行结果（代码、配置、报告）和执行日志。
- `**/review <artifact_or_task_id> [against <criteria_sources>] [focus_on <review_aspects>] [with_context <key=value_pairs>]**`
- **意图:** 对某个工件或任务结果进行审核。
- **示例:** `/review /code/auth_service.py against /docs/prd/auth_prd.md /docs/styleguide.md focus_on security,performance`
- **引擎职责:** 生成审核清单、一致性检查规则、常见问题模式、特定关注点的检查指南，辅助人类 Reviewer 或进行初步自动化检查。
- **输出:** 审核辅助报告，高亮潜在问题。
- `**/test <target_artifact_or_feature> [using <test_plan_or_criteria>] [in_environment <env_name>] [with_context <key=value_pairs>]**`
- **意图:** 对目标进行测试。
- **示例:** `/test login_feature using /plans/auth_test_plan.md in_environment staging`
- **引擎职责:** 生成测试执行规则，包括环境准备、测试数据生成、测试用例执行步骤、结果记录标准、报告格式等。
- **输出:** 测试执行日志和测试报告。
- `**/integrate <source_branch_or_artifact> into <target_branch_or_system> [with_checks <check_list_id>] [with_context <key=value_pairs>]**`
- **意图:** 将一部分工作集成到更大的整体中（如代码合并、文档发布）。
- **示例:** `/integrate feature/login into main with_checks pre_merge_checklist_v1`
- **引擎职责:** 生成集成流程规则，包括代码合并前检查、构建验证、部署步骤（如果适用）、通知规则、版本更新规则等。
- **输出:** 集成操作日志和状态报告。
- `**/learn from <source_logs_or_artifacts> [extract_insights_for <topic>] [update_knowledge_base <boolean>] [with_context <key=value_pairs>]**`
- **意图:** 显式触发知识学习过程（通常可自动化，但提供手动入口）。
- **示例:** `/learn from /logs/deploy_prod_*.log extract_insights_for deployment_failures update_knowledge_base true`
- **引擎职责:** 生成日志分析、模式识别、关键洞察提取的规则。如果 `update_knowledge_base=true`，触发知识索引管道处理这些新洞察。
- **输出:** 分析报告或知识库更新状态。
- `**/generate <output_type> "<output_name>" based_on <source_data> [for_audience <audience_type>] [with_style <style_guide_id>] [with_context <key=value_pairs>]**`
- **意图:** 基于现有数据生成衍生内容（报告、文档、摘要、日志等）。
- **示例:** `/generate developer_log "Week 1 Login Feature DevLog" based_on /logs/work_login_*.log for_audience developers with_style internal_blog_style`
- **引擎职责:** 生成内容提炼、结构组织、语言风格调整、格式化等规则。
- **输出:** 生成的内容草稿。
**B. 基础原则/元规则 (Underlying Principles / Meta-Rules)**

这些原则不是直接命令，而是 RGI 在生成具体规则时**必须考虑和遵守**的更高层次的指导方针。它们通常存储在知识库的核心策略文档中，并被 RGI 的 Prompt 或推理逻辑引用。

- **P01: 清晰性原则 (Clarity):**
- 生成的规则和产出物应清晰、简洁、无歧义。
- 避免使用模糊术语，明确定义关键概念。
- **P02: 一致性原则 (Consistency):**
- 生成的规则应与项目/组织的既定标准、架构、风格指南保持一致。
- 相似的输入应产生逻辑一致的规则。
- **P03: 可验证性原则 (Verifiability):**
- 规则应尽可能可衡量、可测试。
- 任务的完成标准（DoD）应明确。
- **P04: 模块化原则 (Modularity):**
- 生成的计划应将任务分解为合理大小、低耦合的模块。
- 代码和文档结构应遵循模块化设计。
- **P05: 安全性原则 (Security):**
- 所有生成的规则和产出必须优先考虑安全性。
- 涉及数据处理、认证、授权的任务，必须包含安全检查规则。 (OWASP Top 10, etc.)
- **P06: 可靠性原则 (Reliability):**
- 生成的规则应引导产生健壮、容错的系统和流程。
- 考虑边缘情况、错误处理和恢复机制。
- **P07: 效率原则 (Efficiency):**
- 生成的规则应引导采用高效的算法、流程和资源利用方式。
- 避免不必要的复杂性。
- **P08: 可维护性原则 (Maintainability):**
- 生成的代码应易于理解、修改和扩展。
- 文档应保持最新且易于查找。
- **P09: 知识沉淀原则 (Knowledge Persistence):**
- 所有重要的决策、过程、结果都应被记录（日志）。
- 成功的模式和失败的教训应被提炼并反馈回知识库。
- **P10: 人类中心原则 (Human-Centric):**
- 系统是辅助人类的工具。
- 关键决策点必须有人类审核环节。
- 生成的规则和报告应易于人类理解。
**如何使用:**

1. **定义命令 Schema:** 为每个 `/command` 定义其期望的参数、上下文变量和大致的输出类型。
1. **构建知识源:** 准备包含上述原则、项目标准、模板、最佳实践和历史数据的知识库。
1. **设计 RGI Prompt:** 为每个命令设计 Prompt 模板，引导 LLM：

- 理解命令意图和上下文。
- 检索相关知识（包括基础原则）。
- 遵循原则，推理生成具体的、结构化的规则集。
- (可选) 进行自我冲突检查。

1. **Agent 实现:** Agent 解析用户输入的命令，调用 `cddrg_engine.generate_rules()`，获取规则，与用户交互（确认），执行任务，并记录结果反哺知识库。
**与 VibeCopilot 规则的对比和改进:**

- **命令化:** 你的 `copilot.mdc` 类似于定义了一些可执行的动作，这与源命令的思想一致。但 CDDRG 的命令更通用，参数化程度更高。
- **结构化原则:** 你的 `vibe_convention.mdc` 包含了一些编码约定，这类似于 CDDRG 的基础原则，但 CDDRG 的原则更抽象、更通用，并且是 RGI 推理的输入，而非直接规则。
- **动态性:** CDDRG 的核心在于规则是**动态生成**的，而不是像 `.mdc` 文件中那样预先写死所有细节。`vibe_convention.mdc` 更多是静态的 Linter 配置或检查表。
- **知识源:** CDDRG 依赖更广泛的知识源进行推理，而不仅仅是几个规则文件。
这套源命令和基础原则为 CDDRG 提供了一个更强大、更灵活的框架，能更好地适应复杂任务和不断变化的开发环境。

[📑 模板体系 (Templates)](1ca73a85-7f76-80b4-90d0-d6347ef808f5)

好的，我们来设计一套用于管理 CDDRG 引擎知识源（开发文档/静态规则）的 Prompt 和模板。这套体系旨在实现结构化、支持 Block 分布，并能方便地被 `cddrg_engine` 的索引管道处理。

**核心理念:**

1. **结构化优先:** 使用 Markdown Front Matter (YAML) 和/或独立的 YAML 文件来定义元数据和结构化规则。
1. **Block 意识:** 在 Markdown 文档中鼓励或强制使用逻辑块（通过 Headers 或特定标记），并为关键块附加元数据。
1. **Rule Item 化:** 将具体的、可执行的静态规则定义为独立的 Item，推荐使用 YAML 格式。
1. **可管理性:** Prompt 和模板应易于人类理解和维护，同时方便机器解析。

---

**模板体系 (Templates)**

**模板 1: 通用知识文档 (Markdown - **`**.md**`**)**

- **用途:** 用于存储原则、指南、最佳实践、流程描述、架构文档等偏向描述性的知识。
- **结构:**

```markdown
---
# 文档级元数据 (YAML Front Matter)
id: doc-arch-overview-v1  # 全局唯一且持久的 ID
title: "系统架构概览 V1"
type: architecture_document # 类型: principle, guideline, process, architecture, best_practice, etc.
status: active # active, draft, deprecated, archived
version: "1.0"
tags: [architecture, overview, backend, frontend]
related_items: # 关联的其他文档或规则 ID
  - doc-security-principles-v1
  - rule-deployment-std-001
replaces: # 如果废弃，此文档替代了哪个旧文档 ID
  - doc-arch-overview-v0.9
# 可选: 如果文档本身定义了几个核心静态规则
embedded_rules:
  - id: rule-arch-layering-001
    description: "系统必须遵循经典三层架构（表现层、业务逻辑层、数据访问层）。"
    severity: mandatory
    tags: [layering, design]
---

# {文档标题}

<!-- BLOCK START id=arch-overview-intro type=introduction -->
**引言/背景**

(在此处写入引言内容。每个逻辑块应相对独立，聚焦一个主题。)
本块描述了文档的目标读者和主要目的...
<!-- BLOCK END -->

## 核心架构原则 {#core-principles}

<!-- BLOCK START id=arch-principle-modularity type=principle -->
**P1: 模块化 (Modularity)**

*   描述模块化原则的具体要求...
*   例子...
*   **关联规则:** `[[rule-code-module-std-001]]` (使用内部链接语法引用规则 Item)
<!-- BLOCK END -->

<!-- BLOCK START id=arch-principle-scalability type=principle -->
**P2: 可扩展性 (Scalability)**

*   描述可扩展性原则...
<!-- BLOCK END -->

## 主要组件 {#main-components}

<!-- BLOCK START id=arch-component-frontend type=component_description -->
### 前端 (Frontend)

*   使用的技术栈...
*   关键职责...
*   与其他组件的交互方式... 参考 `[[doc-api-spec-v2#frontend-api]]` (链接到其他文档的特定 Block)
<!-- BLOCK END -->

<!-- BLOCK START id=arch-component-backend type=component_description -->
### 后端 (Backend)

*   ...
<!-- BLOCK END -->

## 部署策略 {#deployment-strategy}

<!-- BLOCK START id=arch-deployment-overview type=process_description -->
(描述部署流程概览...)
参考具体部署规则: `[[rule-deployment-std-001]]`
<!-- BLOCK END -->

---
_元注释: `<!-- BLOCK START/END -->` 标记是推荐的，用于精确控制块边界和附加块级元数据 (id, type)。`id` 应在文档内唯一。这有助于 RAG 更精确地检索和引用。如果没有显式标记，索引器可以默认按 Markdown 的 Header (##, ###) 或段落进行分块。内部链接 `[[item_id]]` 或 `[[doc_id#block_id]]` 用于交叉引用。_

```

**模板 2: 结构化规则集 (YAML - **`**.rules.yaml**`**)**

- **用途:** 用于存储一系列离散的、结构化的静态规则 Item。特别适合条件-动作型规则、配置标准、检查清单等。
- **结构:**

```yaml
# 文件级元数据 (可选，也可通过文件名约定)
# filename: security_rules.rules.yaml
# description: "系统安全相关的核心规则"

rules:
  - id: rule-sec-authn-001 # 全局唯一且持久的 ID
    description: "所有面向用户的接口必须强制执行身份认证。"
    type: security_policy # 类型: policy, standard, check, configuration, etc.
    scope: # 规则适用范围
      api_type: external_user_facing
    condition: null # 触发条件 (如果通用则为 null)
    action: # 执行动作或要求
      enforce: authentication
    severity: mandatory # mandatory, recommended, optional
    tags: [security, authentication, api]
    rationale: "防止未授权访问核心功能。" # 设立此规则的原因
    source_doc: doc-security-principles-v1 # 关联的原则性文档 ID (可选)
    status: active

  - id: rule-sec-passwd-complexity-001
    description: "用户密码必须满足最小长度和复杂度要求。"
    type: security_standard
    scope:
      user_context: password_setting
    condition: null
    action:
      require_min_length: 10
      require_complexity: [uppercase, lowercase, number, symbol]
    severity: mandatory
    tags: [security, password, complexity]
    rationale: "增加密码破解难度。"
    status: active

  - id: rule-infra-port-limit-001
    description: "生产环境服务器仅允许开放必要的端口 (e.g., 80, 443)。"
    type: configuration_standard
    scope:
      environment: production
      resource_type: server
    condition: null
    action:
      allowed_ports: [80, 443]
      default_policy: deny
    severity: mandatory
    tags: [infrastructure, security, firewall, port]
    status: active

  - id: rule-code-logging-std-001
    description: "所有关键业务操作和错误必须记录日志。"
    type: coding_standard
    scope:
      language: python # 可限定语言
      code_area: business_logic
    condition: "operation_criticality == high || is_error == true" # 简化的条件示例
    action:
      log_level: INFO # for critical ops
      log_level_error: ERROR # for errors
      include_in_log: [timestamp, user_id, request_id, operation_details, outcome]
    severity: mandatory
    tags: [coding, logging, observability]
    status: active

# ... more rules

```

---

[📑 CDDRG 引擎开发的 AI 辅助工作流](1ca73a85-7f76-8017-a1a2-f6010f964baa)

---

**版本:** 1.0
**日期:** 2023年10月27日
**作者:** [你的名字/团队] & AI 助手

**1. 概述 (Overview)**

**1.1 背景:**
开发 `cddrg_engine` 库本身就是一个复杂的软件工程项目。为了提高开发效率、保证代码质量、确保与设计原则的一致性，并实践我们所倡导的 "vibe coding" 理念，我们提议构建一个专门的 AI 辅助开发工作流来支持 `cddrg_engine` 的开发过程。

**1.2 目标产品:**
本 PRD 描述的是一个基于 **LangGraph** 和 **CodeAct** 理念的 **开发助手 Agent (DevAgent)**。这个 DevAgent 将遵循一套面向软件开发的源命令，并通过一个（可能是正在开发中的）**元 CDDRG 引擎**获取动态生成的规则和指导，来辅助完成 `cddrg_engine` 库的编码、测试、文档编写、重构等任务。

**1.3 核心理念:**
我们将 CDDRG 的核心原则（命令驱动、动态规则生成、知识循环、人机协作）应用于 `cddrg_engine` 自身的开发。DevAgent 作为开发者的智能伙伴，根据高级指令和动态生成的开发规则，执行或辅助执行具体的开发任务，并将开发过程中的产出和学习反哺回项目的知识库。

**1.4 解决的问题:**

- 加速 `cddrg_engine` 的开发迭代速度。
- 确保开发过程遵循既定的架构设计、编码规范和最佳实践（通过动态规则强制）。
- 减少开发者在重复性任务（如生成样板代码、编写基础测试、格式化文档）上花费的时间。
- 促进开发知识（设计决策、代码模式、测试策略）的显性化和沉淀。
- 作为 CDDRG 范式本身的“吃狗粮” (dogfooding) 实践。
**2. 目标与目的 (Goals and Objectives)**

- **主要目标:** 构建一个能显著提升 `cddrg_engine` 开发效率和质量的 DevAgent 工作流。
- **次要目标:**
- 实现基于 LangGraph 的开发任务流程自动化（部分）。
- 利用 CodeAct 能力安全地生成和执行代码片段（用于实现、测试）。
- 通过元 CDDRG 引擎动态生成与开发任务相关的规则（编码规范、测试要求、文档模板）。
- 建立包含代码库、设计文档、开发日志的开发知识库，并实现知识循环。
- 验证 CDDRG 范式在软件开发场景下的有效性。
- **衡量指标 (示例):**
- 减少特定类型开发任务（如创建新模块骨架、生成基础测试）的平均耗时 X%。
- 提高代码规范检查通过率 Y%。
- 提高单元测试覆盖率 Z%。
- 开发者对 DevAgent 辅助效率的主观满意度评分。
**3. 目标用户 (Target Audience)**

- 参与 `cddrg_engine` 库开发的软件工程师和架构师。
**4. 范围 (Scope)**

**4.1 In-Scope (DevAgent & Meta-Engine 功能):**

- **开发命令解析:** 理解面向开发的命令（见下文 Use Cases）。
- **元规则生成:** 元 CDDRG 引擎根据开发命令和上下文，动态生成开发规则（如文件结构、类/函数签名建议、测试点、文档要求）。
- **代码生成辅助 (CodeAct):** 基于生成的规则，起草函数/类/模块的样板代码、测试用例骨架。
- **代码执行 (CodeAct - 安全):** 在沙箱环境中执行生成的代码片段（如运行测试、验证代码片段）。
- **测试辅助:** 根据规则生成测试用例描述，或直接生成可执行的测试代码框架 (基于 `pytest`)。
- **文档辅助:** 根据代码和规则生成 Docstring 草稿、README 更新建议、或基础的 API 文档片段。
- **重构建议:** 基于规则（如代码复杂度、设计模式）和知识库中的最佳实践，提出重构建议。
- **版本控制集成 (基础):** 辅助执行简单的 Git 操作（如创建分支、暂存更改）。
- **流程编排 (LangGraph):** 管理多步骤开发任务（如 实现 -> 测试 -> 文档）的状态和流转。
- **开发知识索引:** 索引 `cddrg_engine` 代码库、PRD、设计文档、开发日志等。
- **人机交互节点:** 在需要决策或审核的环节（如代码评审前、合并前）暂停并请求开发者介入。
**4.2 Out-of-Scope (不包含功能):**

- **完全取代开发者:** DevAgent 是辅助工具，不是自主开发者。
- **最终决策权:** 所有关键设计决策、代码合并、发布由人类开发者负责。
- **复杂的项目管理功能:** 不取代 Jira、Trello 等项目管理工具。
- **部署流水线:** 不负责 CI/CD 部署流程（但可生成配置）。
- **用户界面:** 初期可能以命令行交互为主，不包含复杂的 GUI。
**5. 用例 (Use Cases - 面向开发任务)**

- **UC-DEV-01: 规划新功能实现**
- **User:** `/plan_feature "Implement Cache Manager" based_on prd_section_6.5 requires [sqlite, cachetools]`
- **DevAgent (Guided by Meta-Engine):**

1. 请求 `/plan_feature` 规则 (生成任务分解、文件结构建议、核心类/接口定义规则)。
1. 生成规划草稿 (e.g., 创建 `cache/manager.py`, `cache/storage.py`, 定义 `CacheManager` 接口, 列出核心方法 `get`, `set`, `invalidate`, `_build_key`)。
1. 呈现给开发者确认/修改。

- **UC-DEV-02: 实现函数/方法**
- **User:** `/implement_function CacheManager.get in /cache/manager.py with_logic "Check cache first, if miss, return None"`
- **DevAgent (Guided by Meta-Engine):**

1. 请求 `/implement_function` 规则 (生成编码规范、错误处理模式、日志记录要求、必要的 import)。
1. (CodeAct) 生成函数骨架和核心逻辑代码片段。
1. (可选 CodeAct) 尝试执行简单验证或类型检查。
1. 呈现代码建议给开发者。

- **UC-DEV-03: 编写单元测试**
- **User:** `/write_tests for CacheManager.set in /cache/manager.py cover [basic_set, overwrite, expiry]`
- **DevAgent (Guided by Meta-Engine):**

1. 请求 `/write_tests` 规则 (生成测试用例设计原则、`pytest` 结构模板、Mocking 指南、覆盖率目标)。
1. 生成测试文件骨架 (`/tests/cache/test_manager.py`) 和针对指定场景的测试函数框架 (e.g., `test_set_basic`, `test_set_overwrite`, `test_set_with_ttl`)。
1. (可选 CodeAct) 尝试运行空的测试文件确保结构正确。
1. 呈现给开发者填充具体断言。

- **UC-DEV-04: 生成文档字符串**
- **User:** `/generate_docstring for CacheManager class in /cache/manager.py`
- **DevAgent (Guided by Meta-Engine):**

1. 请求 `/generate_docstring` 规则 (生成 Docstring 风格指南 - e.g., Google Style, reStructuredText)。
1. 分析类定义和方法签名。
1. 生成符合规范的 Docstring 草稿。
1. 呈现给开发者确认/修改。

- **UC-DEV-05: 辅助代码评审**
- **User:** `/review_code pull_request <pr_url_or_branch>`
- **DevAgent (Guided by Meta-Engine):**

1. 请求 `/review_code` 规则 (应用静态分析规则 - Ruff, Mypy, 应用项目特定编码规范, 检查常见错误模式 - 从知识库学习)。
1. 分析代码变更。
1. 生成评审评论草稿，高亮潜在问题点。
1. 呈现给人类 Reviewer 作为参考。
**6. 功能需求 (Functional Requirements - DevAgent & Meta-Engine)**

- **FR-DEV-CMD-01:** DevAgent 必须能解析上述定义的面向开发的源命令及其参数。
- **FR-META-RULE-01:** 元 CDDRG 引擎必须能根据开发命令和上下文（如代码文件路径、PRD 章节、技术栈），动态生成与软件开发任务相关的具体规则。
- **FR-META-KNOW-01:** 知识索引管道必须能处理 Python 代码文件、Markdown 文档（PRD、设计）、YAML 配置文件等，并建立代码结构（类、函数）与文档之间的关联。
- **FR-AGENT-GRAPH-01:** DevAgent 的核心工作流必须使用 LangGraph 构建，以管理状态和多步骤任务。
- **FR-AGENT-CODEACT-01:** DevAgent 必须集成 CodeAct 能力，能在安全的沙箱环境中生成和执行 Python 代码片段。
- **FR-AGENT-TOOL-01:** DevAgent 必须集成必要的开发工具接口（Git、Pytest、Ruff/Linters）。
- **FR-AGENT-INTERACT-01:** DevAgent 必须在关键节点（如计划确认、代码提交前、测试用例生成后）提供清晰的输出并等待开发者确认。
- **FR-KNOW-LOOP-01:** 开发过程中产生的代码变更、测试结果、评审意见应能被捕获并反馈到知识库中（至少通过日志或 commit message 的索引）。
**7. 非功能需求 (Non-Functional Requirements)**

- **NFR-DEV-PERF-01:** DevAgent 响应时间应足够快，避免打断开发者的心流。
- **NFR-DEV-REL-01:** DevAgent 生成的代码和建议应可靠，不能频繁引入错误或破坏现有代码。CodeAct 执行必须安全。
- **NFR-DEV-USAB-01:** 与 DevAgent 的交互（可能通过 CLI 或 IDE 插件）应简单直观。
- **NFR-DEV-MAINT-01:** DevAgent 和元引擎本身的代码应遵循高标准，易于维护和扩展（因为它本身就是项目的一部分）。
**8. 数据需求 (Data Requirements)**

- **元知识库:** `cddrg_engine` 项目代码、`.md` (PRD, Arch Docs), `.yaml` (Config, Static Rules), 开发日志, 测试结果。
- **元规则格式:** 动态生成的开发规则需要定义 Schema (e.g., JSON)，包含步骤、代码模板、检查项、规范引用等。
- **DevAgent 状态:** LangGraph 的状态对象，需要包含当前任务、文件路径、代码片段、测试结果等。
**9. 架构 (Conceptual)**

- **DevAgent:** 基于 LangGraph 的 Python 应用。
- **Nodes:** 命令解析、元规则请求、代码生成 (CodeAct)、代码执行 (CodeAct Sandbox)、测试执行 (Pytest Tool)、文档生成、Git 操作、用户交互等待。
- **Edges:** 条件逻辑，流程控制。
- **State:** 存储任务上下文、中间产物。
- **Meta CDDRG Engine:**
- **核心:** 可以是正在开发中的 `cddrg_engine` 实例自身（引导启动），或者是为其定制的一个简化版本。
- **知识库:** 指向 `cddrg_engine` 项目的本地文件系统。
- **功能:** 接收 DevAgent 的请求，执行 RAG（在项目代码和文档上），调用 LLM 生成开发规则。
- **工具:** GitPython, pytest, Ruff API, OS/Filesystem libs。
**10. 假设与依赖 (Assumptions and Dependencies)**

- 假设开发环境已配置好 Python, uv, Git, Docker (用于沙箱)。
- 假设可以访问 LLM API。
- 依赖 Langchain, LangGraph, `cddrg_engine` (自身)。
**11. 未来的考虑/开放问题 (Future Considerations / Open Questions)**

- 如何更有效地从代码变更历史和评审意见中学习？
- DevAgent 如何处理更复杂的重构任务？
- 如何实现更流畅的 IDE 集成？
- Meta CDDRG Engine 如何随着 `cddrg_engine` 本身的开发而演进和更新？（引导问题）
- 如何评估 DevAgent 对实际开发效率和质量的真实影响？

---

[📑 管理知识源的 Prompts (面向与 Agent 的交互)](1cb73a85-7f76-80dd-8ec1-fa52f4aff201)

这些 Prompt 用于指导用户（通过 Agent）创建、更新或查询这些结构化的知识源。Agent 在后台调用 `cddrg_engine` 或直接的文件/数据库操作来完成任务。

**Prompt 1: 创建新的知识文档**

```plain text
/create knowledge_document

请提供新知识文档的详细信息：

1.  **文档标题 (Title):** (例如: "微服务部署最佳实践")
2.  **文档类型 (Type):** (从 [principle, guideline, process, architecture, best_practice, cheatsheet, postmortem] 中选择或输入新的)
3.  **核心内容要点 (Key Points / Outline):** (请分点列出文档将涵盖的主要内容或章节)
4.  **主要标签 (Tags):** (逗号分隔, 例如: microservices, deployment, kubernetes, best_practice)
5.  **(可选) 关联的现有文档或规则 ID:** (逗号分隔)
6.  **(可选) 此文档将替代的旧文档 ID:**

我将根据这些信息，使用【通用知识文档模板】，为你生成文档草稿框架，并分配一个唯一的 ID。请准备填充详细内容。

```

**Prompt 2: 在文档中添加/更新内容块 (Block)**

```plain text
/update knowledge_document <document_id> add_block

请提供要添加到文档 `{document_id}` 的新内容块信息：

1.  **块的标题/主题 (Block Title/Topic):** (将作为 Markdown Header 或 Block 描述)
2.  **块的类型 (Block Type):** (例如: introduction, principle, component_description, process_step, example, warning)
3.  **块的内容 (Content):** (请在此处输入详细内容，支持 Markdown 格式)
4.  **(可选) 建议的块 ID (Suggested Block ID):** (例如: `ms-deploy-blue-green`，如果留空将自动生成)
5.  **(可选) 插入位置:** (例如: 在块 `existing-block-id` 之后，或在章节 `## Main Components` 下)

我将使用【通用知识文档模板】的块结构，将此内容添加到文档中。

```

**Prompt 3: 创建新的结构化规则 Item**

```plain text
/create rule_item

请提供新规则 Item 的详细信息 (请参考【结构化规则集模板】)：

1.  **规则描述 (Description):** (清晰描述规则内容)
2.  **规则类型 (Type):** (policy, standard, check, configuration, etc.)
3.  **适用范围 (Scope):** (描述规则在何时何地适用，例如: `environment=production`, `api_type=external`)
4.  **(可选) 触发条件 (Condition):** (规则生效的条件，如果通用则留空)
5.  **执行动作/要求 (Action):** (规则的具体要求或执行内容)
6.  **严重性 (Severity):** (mandatory, recommended, optional)
7.  **标签 (Tags):** (逗号分隔)
8.  **(可选) 设立原因 (Rationale):** (为什么需要这条规则?)
9.  **(可选) 关联的文档 ID (Source Doc):**

我将为这条规则分配一个唯一的 ID，并将其添加到相应的规则集文件 (或根据类型创建新的)。

```

**Prompt 4: 查找相关的知识/规则**

```plain text
/find knowledge about "<search_topic>" [type <document_type_or_rule_type>] [tag <tag_name>]

请描述你想查找的主题 `{search_topic}`。你可以选择性地通过类型或标签进行过滤。

例如:
/find knowledge about "database connection pooling" type best_practice tag java
/find knowledge about "password complexity" type rule

我将搜索知识库（包括文档块和规则 Item），并返回最相关的内容摘要和链接。

```

**Prompt 5: 标记文档/规则为废弃**

```plain text
/deprecate <item_id> [replaced_by <new_item_id>] [reason "<deprecation_reason>"]

请提供要废弃的文档或规则的 ID (`{item_id}`)。

*   **(可选)** 如果有新的文档/规则替代它，请提供新项的 ID (`{new_item_id}`)。
*   **(可选)** 请简述废弃的原因 (`{deprecation_reason}`)。

我将更新 `{item_id}` 的状态为 'deprecated'，并记录相关信息。

```

---

**使用流程:**

1. **知识创建/更新:** 用户使用 `/create` 或 `/update` 等 Prompt 与 Agent 交互。Agent (可能借助 LLM 理解用户输入) 按照模板格式化信息，并调用后端逻辑（直接写文件/数据库，或通过 `cddrg_engine` 的管理接口）来创建或修改知识源文件（.md 或 .rules.yaml）。
1. **知识索引:** `cddrg_engine` 的知识索引管道定期或按需运行，扫描知识源目录，解析 Markdown（识别 Front Matter 和 Block）和 YAML 文件，将内容分块、向量化，并存储索引和元数据。
1. **知识使用:** 用户通过 `/plan`, `/execute` 等命令与 Agent 交互。Agent 调用 `cddrg_engine.generate_rules()`。引擎内部的 `Knowledge Retriever` 利用索引（向量+元数据）查找相关的文档块和规则 Item，然后用于生成动态规则。
这套体系通过结构化的模板和引导性的 Prompt，旨在使静态知识源的管理更加规范、高效，并为 CDDRG 引擎提供高质量的、易于处理的输入。
