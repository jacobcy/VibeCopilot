# 工作流模型说明

## 目录结构说明

本目录下的模型仅用于表示与用户界面交互相关的上下文和临时数据结构，**不用于数据持久化**。

数据持久化相关的模型已迁移到`src/models/db`目录下，按照下表对应关系进行使用：

| 旧模型 | 新模型 | 说明 |
|-------|-------|------|
| `src/workflow/models/workflow_definition.py` 中的 `WorkflowStage` | `src/models/db/stage.py` 中的 `Stage` | 工作流阶段模型 |
| `src/workflow/models/workflow_definition.py` 中的 `WorkflowTransition` | `src/models/db/transition.py` 中的 `Transition` | 工作流转换模型 |
| `src/workflow/models/workflow_definition.py` 中的 `WorkflowDefinition` | `src/models/db/workflow_definition.py` 中的 `WorkflowDefinition` | 工作流定义模型 |
| `src/models/workflow.py` 中的 `Workflow` | `src/models/db/workflow.py` 中的 `Workflow` | 工作流模型 |
| `src/models/workflow.py` 中的 `WorkflowStep` | `src/models/db/workflow.py` 中的 `WorkflowStep` | 工作流步骤模型 |
| `src/models/workflow.py` 中的 `WorkflowExecution` | `src/models/db/workflow.py` 中的 `WorkflowExecution` | 工作流执行模型 |

## 当前模型说明

本目录下仅保留了以下模型文件：

1. `workflow_context.py` - 包含工作流上下文相关的临时数据结构，用于界面交互：
   - `ChecklistItem` - 检查清单项
   - `NextTask` - 下一步任务
   - `StageContext` - 阶段上下文
   - `WorkflowContext` - 工作流上下文

## 数据模型重构说明

根据`docs/dev/workflow-refactoring.md`文档中的设计，我们已完成了工作流数据结构的重构。主要变更包括：

1. 统一了工作流相关模型的位置，全部放在`src/models/db`目录下
2. 增加了`Stage`和`Transition`模型，完善了工作流状态流转的数据结构
3. 移除了重复定义的模型，确保数据结构的一致性
4. 在模型间建立了合理的关系，便于数据查询和管理

## 开发建议

1. 新的开发工作请直接使用`src/models/db`目录下的数据库模型
2. 界面交互相关的临时数据结构可以使用本目录下的模型
3. 如需定义新的上下文模型，请添加到本目录，并在`__init__.py`中导出
