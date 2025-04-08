# 管理知识源的 Prompts (面向与 Agent 的交互)

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
