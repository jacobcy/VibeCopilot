# Workflow 模块

## 概述

Workflow 模块是 VibeCopilot 项目的工作流管理系统，提供了创建、管理和执行自动化工作流的功能。该模块支持与 n8n 工作流平台集成，实现了本地工作流状态与外部自动化系统的双向同步。

## 核心功能

- **工作流管理**：创建、查看、更新和删除工作流
- **工作流执行**：执行工作流并跟踪执行状态
- **n8n 集成**：与 n8n 工作流平台双向集成
- **状态报告**：通过状态提供者接口集成到 VibeCopilot 状态系统中

## 模块结构

```
workflow/
├── __init__.py
├── workflow_manager.py       # 命令行工具入口
├── workflow_operations.py    # 操作函数汇总
├── workflow_utils.py         # 工具函数
└── operations/               # 操作实现
    ├── crud_operations.py    # 创建、更新、删除操作
    ├── list_operations.py    # 列表和查看操作
    └── execution_operations.py # 执行和同步操作
```

## 数据模型

工作流模块使用以下数据模型：

- **Workflow**：工作流定义，包含基本信息和 n8n 关联信息
- **WorkflowStep**：工作流步骤，包含步骤顺序、类型和配置
- **WorkflowExecution**：工作流执行记录，跟踪执行状态和结果
- **WorkflowStepExecution**：步骤执行记录，跟踪每个步骤的执行情况

## 命令行使用

工作流模块提供了命令行接口进行管理和操作：

```bash
# 列出所有工作流
python -m src.workflow.workflow_manager list

# 查看工作流详情
python -m src.workflow.workflow_manager view <workflow_id>

# 创建工作流
python -m src.workflow.workflow_manager create "新工作流" -d "工作流描述" --active

# 关联 n8n 工作流
python -m src.workflow.workflow_manager update <workflow_id> --n8n-id <n8n_workflow_id>

# 执行工作流
python -m src.workflow.workflow_manager execute <workflow_id> -c '{"param1": "value1"}'

# 同步 n8n 工作流
python -m src.workflow.workflow_manager sync --import-workflows --update-from-n8n
```

## 与 n8n 集成

### n8n 关联

工作流可以关联到 n8n 工作流，通过以下方式：

1. 创建工作流时指定 n8n ID：`create "工作流名称" --n8n-id <n8n_workflow_id>`
2. 更新工作流添加 n8n ID：`update <workflow_id> --n8n-id <n8n_workflow_id>`
3. 从 n8n 导入工作流：`sync --import-workflows`

### 执行流程

当执行关联了 n8n 的工作流时：

1. 创建本地执行记录
2. 通过 n8n 适配器提交执行请求到 n8n
3. n8n 执行工作流并返回执行 ID
4. 可选择等待执行完成或异步执行
5. 执行完成后同步状态和结果

## 状态集成

工作流模块通过 `WorkflowStatusProvider` 实现了 `IStatusProvider` 接口，集成到 VibeCopilot 状态系统：

- 提供工作流状态查询
- 支持工作流执行状态更新
- 允许外部系统订阅工作流状态变更

## 开发指南

### 添加新的工作流类型

1. 在 `operations/crud_operations.py` 中扩展 `create_workflow` 函数，支持新的工作流类型
2. 在 `models/db/workflow.py` 中更新 `WorkflowStep` 模型，增加新的步骤类型
3. 在 `operations/execution_operations.py` 中实现新类型工作流的执行逻辑

### 扩展 n8n 集成

1. 修改 `adapters/n8n.py` 添加新的 API 方法
2. 在 `operations/execution_operations.py` 中更新 `sync_n8n` 函数

### 添加本地执行引擎

目前工作流主要通过 n8n 执行，如需开发本地执行引擎：

1. 创建 `workflow/engine` 目录实现本地执行引擎
2. 在 `operations/execution_operations.py` 中添加本地执行逻辑
3. 实现工作流步骤执行器

## 最佳实践

1. **工作流命名**：使用简洁明了的名称，表达工作流的用途
2. **工作流描述**：详细说明工作流的功能、输入和预期输出
3. **n8n 集成**：复杂的工作流应优先使用 n8n 实现，利用其可视化编辑器
4. **状态监控**：使用 `view` 命令定期检查执行状态
5. **错误处理**：工作流设计时应考虑错误处理和重试机制

## 未来计划

- 实现本地工作流执行引擎
- 增强工作流步骤类型，支持更多自动化场景
- 添加工作流模板系统
- 支持工作流版本控制
- 开发工作流可视化编辑器
