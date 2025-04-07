# VibeCopilot 工作流开发者指南

## 架构概述

VibeCopilot 工作流模块是一个轻量级的解释器系统，它将规则文件解析为结构化的工作流定义，并为用户提供上下文和指导。本开发者指南将详细说明工作流模块的架构、核心组件和扩展方法。

### 系统架构

工作流模块由以下主要组件构成：

1. **解释器 (Interpreter)**：
   - `RuleParser`: 解析 .mdc 规则文件，提取结构化信息
   - `FlowConverter`: 将规则数据转换为工作流定义
   - `ContextProvider`: 为代理提供当前工作流上下文

2. **模型 (Models)**：
   - `WorkflowDefinition`: 工作流定义的数据结构
   - `WorkflowContext`: 工作流上下文的数据结构

3. **导出工具 (Exporters)**：
   - `JsonExporter`: 工作流的 JSON 序列化与反序列化
   - `MermaidExporter`: 将工作流导出为 Mermaid 流程图

4. **命令接口 (Commands)**：
   - `FlowCommand`: CLI 命令处理逻辑
   - `flow_cmd.py`: 简单的命令行入口

## 目录结构

```
src/workflow/
├── __init__.py             # 模块初始化
├── README.md               # 项目说明
├── flow_cmd.py             # 命令行工具
├── docs/                   # 文档
│   ├── user_guide.md       # 用户指南
│   └── developer_guide.md  # 开发者指南
├── interpreter/            # 解释器模块
│   ├── __init__.py         # 初始化
│   ├── rule_parser.py      # 规则解析
│   ├── flow_converter.py   # 流程转换
│   └── context_provider.py # 上下文提供
├── models/                 # 数据模型
│   ├── __init__.py         # 初始化
│   ├── workflow_definition.py # 工作流定义
│   └── workflow_context.py # 工作流上下文
├── exporters/              # 导出工具
│   ├── __init__.py         # 初始化
│   ├── json_exporter.py    # JSON导出
│   └── mermaid_exporter.py # Mermaid导出
├── templates/              # 模板目录
│   └── flow_templates/     # 流程模板
└── workflows/              # 工作流存储
```

## 核心组件详解

### 1. 规则解析器 (RuleParser)

规则解析器负责从 .mdc 规则文件中提取结构化信息：

```python
# 使用示例
from src.workflow.interpreter.rule_parser import RuleParser

parser = RuleParser()
rule_data = parser.parse_rule_file(".cursor/rules/flow-rules/test-flow.mdc")
```

规则数据结构包括：

- `metadata`: 规则元数据 (从 front matter 提取)
- `sections`: 规则主要段落
- `raw_content`: 原始内容
- `source_file`: 源文件路径
- `rule_id`: 规则ID

### 2. 流程转换器 (FlowConverter)

流程转换器负责将规则数据转换为工作流定义：

```python
# 使用示例
from src.workflow.interpreter.flow_converter import FlowConverter

converter = FlowConverter()
workflow = converter.convert_rule_to_workflow(rule_data)
```

转换逻辑：

- 从规则段落创建工作流阶段
- 提取每个阶段的检查清单和交付物
- 建立阶段之间的转换关系

### 3. 上下文提供器 (ContextProvider)

上下文提供器负责生成工作流状态的实时上下文：

```python
# 使用示例
from src.workflow.interpreter.context_provider import ContextProvider

provider = ContextProvider()
progress_data = {
    "current_stage": "test_execution",
    "completed_items": ["准备测试环境", "编写测试用例"]
}
context = provider.provide_context_to_agent("test-workflow", progress_data)
```

上下文包括：

- 工作流信息
- 当前阶段详情
- 已完成和未完成的检查项
- 下一步任务
- 后续阶段预览

### 4. 导出工具 (Exporters)

#### JSON导出器 (JsonExporter)

负责工作流的序列化和反序列化：

```python
from src.workflow.exporters.json_exporter import JsonExporter

exporter = JsonExporter()
# 保存工作流
exporter.export_workflow(workflow, "my-workflow.json")
# 加载工作流
workflow = exporter.load_workflow("test-workflow")
# 列出所有工作流
workflows = exporter.list_workflows()
```

#### Mermaid导出器 (MermaidExporter)

将工作流转换为 Mermaid 流程图：

```python
from src.workflow.exporters.mermaid_exporter import MermaidExporter

exporter = MermaidExporter()
mermaid_code = exporter.export_workflow(workflow)
```

## 扩展开发指南

### 添加新的工作流类型

1. 创建新的规则文件，如 `.cursor/rules/flow-rules/custom-flow.mdc`
2. 使用规则解析器提取规则数据
3. 使用流程转换器生成工作流定义
4. 保存工作流到 workflows 目录

```python
rule_parser = RuleParser()
converter = FlowConverter()
exporter = JsonExporter()

rule_data = rule_parser.parse_rule_file(".cursor/rules/flow-rules/custom-flow.mdc")
workflow = converter.convert_rule_to_workflow(rule_data)
exporter.export_workflow(workflow)
```

### 自定义工作流解析逻辑

如果需要自定义解析逻辑，可以扩展 `FlowConverter` 类：

```python
from src.workflow.interpreter.flow_converter import FlowConverter

class CustomFlowConverter(FlowConverter):
    def _extract_checklist(self, content: str) -> List[str]:
        # 自定义检查清单提取逻辑
        pass
```

### 添加新的导出格式

可以创建新的导出器实现不同格式的导出：

```python
# 创建 SVG 导出器
class SvgExporter:
    def export_workflow(self, workflow: Dict[str, Any], output_path: str = None) -> Optional[str]:
        # 将工作流转换为 SVG
        pass
```

### 集成现有系统

工作流模块可以与 VibeCopilot 的其他组件集成：

1. **与状态系统集成**：

```python
from src.workflow.interpreter.context_provider import ContextProvider
from src.status.service import StatusService

context = ContextProvider().provide_context_to_agent("test-workflow", progress_data)
status_service = StatusService()
status_service.update_status("test", context["current_stage"]["stage_name"], context["current_stage"]["progress"])
```

2. **与命令系统集成**：

添加自定义命令到 `flow_command.py`。

## 数据模型

### WorkflowDefinition

工作流定义的核心数据结构：

```python
@dataclass
class WorkflowStage:
    id: str
    name: str
    description: str
    order: int
    checklist: List[str]
    deliverables: List[str]

@dataclass
class WorkflowTransition:
    id: str
    from_stage: str
    to_stage: str
    condition: str
    description: str

@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str
    version: str
    source_rule: str
    stages: List[WorkflowStage]
    transitions: List[WorkflowTransition]
```

### WorkflowContext

提供给代理的上下文数据：

```python
@dataclass
class ChecklistItem:
    text: str
    completed: bool = False

@dataclass
class NextTask:
    text: str
    priority: str
    stage_id: str

@dataclass
class StageContext:
    stage_id: str
    stage_name: str
    stage_description: str
    progress: float
    checklist: List[ChecklistItem]
    deliverables: List[str]

@dataclass
class WorkflowContext:
    workflow: Dict[str, Any]
    current_stage: StageContext
    next_tasks: List[NextTask]
    next_stages: Optional[List[Dict[str, Any]]] = None
```

## 最佳实践

### 规则文件编写

为了得到良好的工作流转换效果，规则文件应遵循以下结构：

1. 使用 Front Matter 提供元数据
2. 使用标题划分阶段
3. 使用列表定义检查项
4. 明确标注交付物

```markdown
---
title: 测试流程
description: 测试流程指南
version: 1.0.0
---

# 测试准备

准备测试环境和测试计划。

- 理解需要测试的功能和预期行为
- 准备测试环境和测试数据
- 确认测试工具和框架可用
- 制定测试计划和测试用例

交付物: 测试计划文档, 测试用例列表, 测试环境配置完成

# 测试执行

执行各类测试并记录结果。

- 执行单元测试并验证覆盖率
- 执行集成测试验证组件交互
- 执行端到端测试验证整体功能
- 记录测试过程和发现的问题

交付物: 测试执行记录, 测试覆盖率报告, 问题跟踪记录
```

### 性能考量

- 工作流定义应保持轻量，避免过于复杂的结构
- 缓存常用工作流，避免频繁解析
- 按需加载工作流阶段内容

### 错误处理

确保对各种异常情况进行适当处理：

```python
try:
    rule_data = rule_parser.parse_rule_file(rule_path)
    if not rule_data:
        logger.error(f"解析规则文件失败: {rule_path}")
        return None

    workflow = converter.convert_rule_to_workflow(rule_data)
    if not workflow:
        logger.error("创建工作流失败")
        return None

    # 继续处理...
except Exception as e:
    logger.exception(f"处理工作流时发生错误: {str(e)}")
    return None
```

## 测试

### 单元测试

为每个核心组件编写单元测试：

```python
def test_rule_parser():
    parser = RuleParser()
    rule_data = parser.parse_rule_file("tests/fixtures/test-flow.mdc")
    assert rule_data is not None
    assert "metadata" in rule_data
    # 更多断言...

def test_flow_converter():
    converter = FlowConverter()
    workflow = converter.convert_rule_to_workflow(rule_data)
    assert workflow is not None
    assert "stages" in workflow
    assert len(workflow["stages"]) > 0
    # 更多断言...
```

### 集成测试

测试完整流程：

```python
def test_workflow_lifecycle():
    # 1. 解析规则
    rule_data = rule_parser.parse_rule_file("tests/fixtures/test-flow.mdc")

    # 2. 转换为工作流
    workflow = converter.convert_rule_to_workflow(rule_data)

    # 3. 导出工作流
    file_path = exporter.export_workflow(workflow, "test-output.json")

    # 4. 重新加载工作流
    loaded_workflow = exporter.load_workflow("test-workflow")

    # 5. 获取上下文
    context = provider.provide_context_to_agent("test-workflow", {"current_stage": "test_preparation"})

    # 验证
    assert workflow["id"] == loaded_workflow["id"]
    assert context["current_stage"]["stage_id"] == "test_preparation"
```

## CLI 命令集成

`FlowCommand` 类处理 CLI 命令，集成到 VibeCopilot 的命令系统：

```python
# 在 src/cli/main.py 中注册命令
commands: Dict[str, Type[Command]] = {
    "roadmap": RoadmapCommands,
    "rule": RuleCommand,
    "flow": FlowCommand,
    "help": HelpCommand,
}
```

## 未来扩展方向

1. **可视化编辑器**：开发一个基于 Web 的工作流编辑器
2. **工作流模板库**：创建更多预定义工作流模板
3. **状态跟踪**：增强与状态系统的集成
4. **自动执行**：支持自动执行简单任务
5. **通知系统**：添加工作流进度通知
6. **历史记录**：跟踪工作流执行历史
7. **团队协作**：支持多人协作的工作流

---

本指南仅涵盖了工作流模块的核心开发内容。如有特定技术问题或需要更深入的代码示例，请参考源代码或联系开发团队。
