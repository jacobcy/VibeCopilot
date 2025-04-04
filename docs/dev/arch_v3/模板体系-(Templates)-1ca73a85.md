# 模板体系 (Templates)

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

