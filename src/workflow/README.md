# VibeCopilot 工作流系统

## 概述

VibeCopilot 工作流系统提供了一套完整的工作流定义、管理和执行功能。系统支持从描述性文件创建工作流、通过模板指导工作流生成、使用LLM解析工作流结构，并提供丰富的命令行界面进行工作流的管理和操作。

## 核心特性

- **工作流创建**：支持通过描述性文件和模板创建工作流
- **LLM解析**：使用OpenAI解析描述性内容为结构化工作流
- **工作流验证**：确保工作流定义的完整性和一致性
- **工作流管理**：提供全面的CRUD操作
- **短ID标识**：使用8字符的短UUID作为工作流标识
- **可视化支持**：支持以Mermaid格式导出工作流图表
- **阶段执行**：支持执行工作流的特定阶段
- **上下文管理**：提供阶段执行的上下文信息
- **会话管理**：支持工作流执行会话
- **任务集成**：工作流会话与任务系统紧密集成，每个会话专注于一个具体任务

## 目录结构

```
src/workflow/
├── __init__.py                   # 模块入口点和导出定义
├── README.md                     # 本文档
├── workflow_operations.py        # 工作流基本操作 (CRUD)
├── workflow_template.py          # 工作流模板相关功能
├── workflow_advanced_operations.py # 高级工作流操作
├── analytics/                    # 工作流分析模块
│   └── workflow_analytics.py     # 工作流统计分析功能
├── search/                       # 工作流搜索模块
│   └── workflow_search.py        # 工作流搜索和模糊匹配功能
├── execution/                    # 工作流执行模块
│   └── workflow_execution.py     # 工作流执行引擎
├── flow_cmd/                     # 工作流命令行功能
│   ├── workflow_creator.py       # 工作流创建器
│   └── helpers.py                # 命令行辅助函数
└── interpreter/                  # 工作流解释器
    └── flow_converter.py         # 工作流转换器
```

## 命令行接口

工作流系统提供了丰富的命令行接口：

```bash
# 列出所有工作流
vibecopilot flow list [--type TYPE] [--verbose]

# 创建工作流
vibecopilot flow create --source SOURCE [--template TEMPLATE] [--name NAME] [--output OUTPUT] [--verbose]

# 查看工作流
vibecopilot flow show WORKFLOW_ID [--format {json,text,mermaid}] [--diagram] [--verbose]

# 更新工作流
vibecopilot flow update ID [--name NAME] [--desc DESCRIPTION] [--verbose]

# 删除工作流
vibecopilot flow delete WORKFLOW_ID [--force] [--verbose]

# 导出工作流
vibecopilot flow export WORKFLOW_ID [--format {json,mermaid}] [--output OUTPUT] [--verbose]

# 导入工作流
vibecopilot flow import FILE_PATH [--overwrite] [--verbose]

# 可视化工作流
vibecopilot flow visualize ID [--session] [--format {mermaid,text}] [--output OUTPUT] [--verbose]

# 运行工作流阶段
vibecopilot flow run STAGE [--workflow-id WORKFLOW_ID] [--name NAME] [--completed COMPLETED] [--session SESSION] [--task TASK_ID] [--verbose]

# 获取工作流阶段上下文
vibecopilot flow context WORKFLOW_ID STAGE_ID [--session SESSION] [--completed COMPLETED] [--format {json,text}] [--verbose]

# 获取下一阶段建议
vibecopilot flow next SESSION_ID [--current CURRENT] [--format {json,text}] [--verbose]

# 管理工作流会话
vibecopilot flow session list [--verbose]
vibecopilot flow session create --workflow WORKFLOW_ID [--name NAME] [--task TASK_ID]
vibecopilot flow session show SESSION_ID
vibecopilot flow session close SESSION_ID
```

## 实体关系与集成

VibeCopilot工作流系统与路线图系统紧密集成，通过清晰的实体关系模型连接工作流、任务和故事：

### Story → Task → Session 关系模型

- **一对多关系**：一个故事(Story)可以包含多个任务(Task)，一个任务可以关联多个会话(Session)
- **专注原则**：每个会话专注于一个特定任务，明确工作目标
- **数据引用**：Session引用Task (`Session.task_id`)，Task引用Story (`Task.story_id`)

### 关系应用场景

- **工作流跟踪**：一个任务可能需要多次不同类型的工作流才能完成
- **进度可视化**：通过查看任务关联的所有会话，了解具体工作进度
- **数据追溯**：从会话可以追溯到相关任务和故事，形成完整工作链条

### 集成命令示例

```bash
# 创建关联到特定任务的会话
vibecopilot flow session create --workflow dev_workflow --task task_123

# 查看特定任务的所有相关会话
vibecopilot task show task_123 --sessions
```

## 工作流数据结构

工作流定义的核心数据结构：

```json
{
  "id": "workflow1",                   // 工作流唯一ID (8字符)
  "name": "样例工作流",                 // 工作流名称
  "description": "这是一个样例工作流",   // 工作流描述
  "version": "1.0.0",                  // 工作流版本
  "stages": [                          // 工作流阶段列表
    {
      "id": "stage1",                  // 阶段唯一ID
      "name": "第一阶段",               // 阶段名称
      "description": "这是第一个阶段",   // 阶段描述
      "order": 1,                      // 阶段顺序
      "checklist": [                   // 阶段检查项
        "检查项1",
        "检查项2"
      ],
      "deliverables": [                // 阶段交付物
        "交付物1",
        "交付物2"
      ]
    }
  ],
  "transitions": [                     // 阶段转换列表
    {
      "from": "stage1",                // 源阶段ID
      "to": "stage2",                  // 目标阶段ID
      "condition": "完成第一阶段"        // 转换条件
    }
  ],
  "metadata": {                        // 元数据
    "created_at": "2025-04-10T07:17:08.734722",
    "updated_at": "2025-04-10T07:17:08.734722"
  }
}
```

## 工作流模板

系统支持通过模板创建工作流。默认模板路径为 `templates/flow/default_flow.json`。模板定义了工作流的基本结构和字段要求，用于指导LLM解析过程。

## 验证机制

`WorkflowValidator` 负责验证工作流定义的完整性，包括：

- 必要字段验证 (id, name, description, stages, transitions)
- 阶段ID唯一性验证
- 转换引用有效性验证
- 工作流完整性验证（确保每个阶段都有入口和出口）
- 循环依赖检测

## 未来开发方向

1. **工作流模板管理**：完善模板管理功能，支持创建、更新和删除模板
2. **工作流版本控制**：实现工作流版本管理，支持回滚和比较
3. **工作流执行记录**：增强执行历史记录和统计功能
4. **工作流权限控制**：添加用户权限管理，控制工作流访问和操作权限
5. **工作流触发器**：支持基于事件或条件自动触发工作流
6. **工作流导入/导出增强**：支持更多格式和转换选项
7. **工作流图表编辑器**：提供可视化编辑器创建和修改工作流
8. **API接口**：提供REST API接口供其他系统集成
9. **工作流状态监控**：实时监控工作流执行状态和进度
10. **任务集成增强**：深化与任务系统的集成，支持基于任务优先级和依赖关系的工作流推荐

## 使用示例

### 创建工作流

```bash
# 从文本文件创建工作流
vibecopilot flow create --source descriptions/workflow_desc.txt --name "测试工作流"

# 使用自定义模板创建工作流
vibecopilot flow create --source descriptions/workflow_desc.txt --template templates/flow/custom_template.json
```

### 管理工作流

```bash
# 列出所有工作流
vibecopilot flow list

# 查看工作流详情
vibecopilot flow show workflow1

# 删除工作流
vibecopilot flow delete workflow1 --force
```

### 运行工作流

```bash
# 运行工作流的特定阶段
vibecopilot flow run stage1 --workflow-id workflow1

# 获取阶段上下文
vibecopilot flow context workflow1 stage1
```

### 与任务集成

```bash
# 创建关联到特定任务的会话
vibecopilot flow session create --workflow dev_workflow --task task_123

# 在任务上下文中运行工作流
vibecopilot flow run stage1 --task task_123

# 查看特定任务的所有相关会话
vibecopilot task show task_123 --sessions
```

## 重要更新：架构变更

通过 `src.workflow.utils` 模块统一导入和使用：

- `src.workflow.flow_cmd`：包含工作流命令相关功能
  - `workflow_search.py`：工作流搜索功能
  - `workflow_context.py`：工作流上下文处理
  - `workflow_manager.py`：工作流管理功能
  - `filesystem.py`：文件系统操作支持

```python
from src.workflow.utils import (
    get_workflow,                      # 获取工作流
    list_workflows,                    # 列出工作流
    create_workflow,                   # 创建工作流
    update_workflow,                   # 更新工作流
    delete_workflow,                   # 删除工作流
    ensure_directory_exists,           # 确保目录存在
    get_workflow_context,              # 获取工作流上下文
    format_workflow_stages,            # 格式化工作流阶段
    create_workflow_from_rule,         # 从规则创建工作流
    create_workflow_from_template_with_vars  # 使用变量从模板创建工作流
)
```

此重构使代码更加模块化并降低了耦合度。
