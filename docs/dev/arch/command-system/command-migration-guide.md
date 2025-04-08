# VibeCopilot 命令系统重构规划

## 1. 目标

重构 VibeCopilot 命令系统，实现以下目标：

1. 建立清晰统一的命令接口和类继承体系
2. 统一参数解析、验证和错误处理机制
3. 标准化帮助信息和用户交互方式
4. 提高代码可维护性和可扩展性
5. 优化用户体验
6. **适配AI Agent调用**：设计机器友好的输出格式，使命令系统能被AI Agent高效准确地调用和处理
7. **提供清晰反馈**：标准化的结果输出，为Agent提供明确的执行状态和后续行动指引

## 2. 架构设计

### 2.1 核心组件

```
CommandInterface (接口)
  ↑
AbstractCommand (抽象基类)
  ↑
BaseCommand (公共基类)
  ↑
具体命令类
```

### 2.2 组件职责

| 组件 | 职责 |
|------|------|
| CommandInterface | 定义命令的基本接口和契约 |
| AbstractCommand | 实现命令执行的标准流程骨架 |
| BaseCommand | 提供常用功能的默认实现 |
| 具体命令类 | 实现特定命令的业务逻辑 |
| CommandResult | 封装命令执行结果 |
| CommandRegistry | 管理命令注册和查找 |
| CommandDispatcher | 解析用户输入并调用对应命令 |

### 2.3 目录结构

```
src/cli/
  |-- command.py           # 接口定义
  |-- abstract_command.py  # 抽象基类
  |-- base_command.py      # 公共基类
  |-- command_registry.py  # 命令注册
  |-- command_dispatcher.py # 命令分发
  |-- command_result.py    # 结果类定义
  |-- commands/            # 具体命令
      |-- __init__.py      # 导出所有命令
      |-- rule/            # 规则命令
      |-- flow/            # 流程命令
      |-- status/          # 状态命令
      |-- memory/          # 记忆命令
      |-- task/            # 任务命令
      |-- ...
  |-- main.py              # 主入口
```

## 3. 标准实现规范

### 3.1 命令类规范

```python
class XxxCommand(BaseCommand):
    def __init__(self):
        super().__init__("xxx", "Xxx命令描述")
        self.required_args = ["required_arg1"]
        self.optional_args = {"optional_arg1": default_value1}

    def get_help(self) -> str:
        # 标准帮助格式
        pass

    def parse_args(self, args: List[str]) -> Dict[str, Any]:
        # 标准参数解析
        pass

    def execute_command(self, args: Dict[str, Any]) -> CommandResult:
        # 命令执行逻辑
        pass
```

### 3.2 参数处理规范

- 长选项格式：`--option=value` 或 `--option value`
- 短选项格式：`-o value`
- 布尔选项：`--flag` (存在表示 True，不存在表示 False)
- 位置参数：按顺序解析非选项参数

### 3.3 错误处理规范

- 使用 CommandResult 封装结果
- 始终包含 success 标志和消息
- 错误信息应清晰指明问题和可能的解决方案

### 3.4 帮助信息格式

```
命令名称 - 简短描述

用法:
  命令 <必需参数> [可选参数]

参数:
  <必需参数>         参数描述
  --选项, -o         选项描述

示例:
  命令 参数 --选项=值
  命令 参数 -o 值
```

### 3.5 Agent适配规范

#### 3.5.1 标准输出结构

所有命令应返回结构化输出，包含以下字段：

```json
{
  "status": "success|error|warning",
  "code": 0,  // 0表示成功，非0表示错误码
  "message": "人类可读的消息",
  "data": {},  // 命令执行的实际数据结果
  "meta": {    // 元数据
    "command": "执行的命令",
    "duration_ms": 123,  // 执行时间
    "next_actions": ["可选的后续命令建议数组"]
  }
}
```

#### 3.5.2 错误和建议机制

当命令执行失败时，应提供：

1. **明确的错误代码**：用于Agent程序化处理
2. **详细的错误描述**：包含错误原因和上下文
3. **可行的解决方案**：针对特定错误提供1-3个可能的解决建议
4. **相关命令建议**：提供可能有助于解决问题的相关命令

示例：
```json
{
  "status": "error",
  "code": 1001,
  "message": "无法创建规则：rule_id 'tech/backend' 已存在",
  "data": null,
  "meta": {
    "command": "rule create tech backend",
    "duration_ms": 45,
    "next_actions": [
      "rule update tech/backend --vars='{...}'",
      "rule delete tech/backend --force",
      "rule show tech/backend"
    ]
  }
}
```

#### 3.5.3 进度反馈机制

对于长时间运行的命令，提供机器可读的进度信息：

```json
{
  "status": "in_progress",
  "code": 0,
  "message": "正在同步知识库...",
  "data": {
    "progress": 0.45,  // 0-1之间的进度值
    "current_step": "处理文件 (45/100)",
    "estimated_remaining_seconds": 120
  },
  "meta": {
    "command": "memory sync",
    "started_at": "2023-08-15T14:35:12Z"
  }
}
```

#### 3.5.4 自动补全和参数提示

命令应提供专门为Agent设计的参数预测和补全API：

```json
{
  "suggestions": [
    {
      "command": "rule create",
      "params": [
        {"name": "template_type", "required": true, "choices": ["tech", "flow", "role"]},
        {"name": "name", "required": true}
      ]
    }
  ]
}
```

#### 3.5.5 解释器模式与指引机制

命令系统采用**解释器模式**，特别是工作流相关命令，它们不直接执行任务，而是指引Agent完成工作：

1. **上下文提供**：提供当前状态、阶段信息和工作环境
2. **任务分解**：将复杂任务分解为可执行步骤
3. **检查清单**：提供当前阶段需要完成的检查项
4. **交付物指南**：明确说明当前阶段应该产出的交付物
5. **进度跟踪**：记录工作流进度，但不干预具体执行

示例响应格式：
```json
{
  "status": "success",
  "code": 0,
  "message": "已获取编码阶段上下文",
  "data": {
    "current_stage": {
      "id": "implementation",
      "name": "代码实现",
      "description": "编写功能代码",
      "progress": 0.3
    },
    "checklist": [
      "遵循代码风格指南",
      "为关键功能编写单元测试",
      "确保代码可读性和可维护性"
    ],
    "deliverables": [
      "功能代码实现",
      "单元测试",
      "必要的文档注释"
    ],
    "context": {
      "task": "实现用户登录功能",
      "branch": "feature/user-login",
      "related_files": ["auth/login.js", "models/user.js"]
    }
  },
  "meta": {
    "command": "flow context coding-workflow",
    "next_actions": [
      {
        "command": "status update --stage=implementation --progress=0.5",
        "description": "更新实现阶段进度"
      },
      {
        "command": "task show TASK-123",
        "description": "查看当前任务详情"
      }
    ]
  }
}
```

## 4. 命令表

请参考 `docs/dev/architecture/command-list.md` 中的命令表，该表详细列出了所有可用的命令及其用法。

## 5. 实施计划

### 5.1 阶段划分

| 阶段 | 重点任务 | 预期时间 |
|------|---------|---------|
| **准备阶段** | 确认设计、创建核心组件 | 2天 |
| **基础阶段** | 实现基础架构 | 3天 |
| **迁移阶段** | 迁移现有命令 | 5天 |
| **完善阶段** | 测试与文档 | 3天 |

### 5.2 详细任务

1. **准备阶段**
   - 细化设计文档
   - 与团队确认设计
   - 创建项目分支

2. **基础阶段**
   - 实现 CommandInterface
   - 实现 AbstractCommand
   - 实现 BaseCommand
   - 实现 CommandResult
   - 实现 CommandRegistry
   - 实现 CommandDispatcher

3. **迁移阶段**
   - 迁移 RuleCommand (模板命令)
   - 迁移 FlowCommand
   - 迁移其他现有命令
   - 添加新命令

4. **完善阶段**
   - 编写单元测试
   - 进行集成测试
   - 编写开发文档
   - 编写用户文档

## 6. 预期成果

1. 清晰统一的命令接口和类继承体系
2. 一致的命令行体验
3. 更易维护和扩展的代码结构
4. 完整的命令集
5. 详尽的文档和示例
6. **Agent友好的交互界面**：命令系统可被AI Agent高效调用，输出格式统一且结构化
7. **智能错误恢复**：提供清晰的错误诊断和建议，帮助Agent自动恢复错误状态

## 7. 风险与对策

| 风险 | 可能性 | 影响 | 对策 |
|------|-------|------|------|
| 兼容性问题 | 中 | 高 | 确保旧命令行为保持不变，提供过渡措施 |
| 重构范围扩大 | 中 | 中 | 严格控制范围，分阶段实施 |
| 测试不充分 | 低 | 高 | 编写全面的单元测试和集成测试 |
| 文档不完善 | 低 | 中 | 确保文档与代码同步更新 |

## 8. 工作流解释器工作机制

工作流解释器被重新设计为轮次(Round)驱动的执行引擎，采用`workflow_name:stage_name`的统一格式组织工作流阶段。

#### 轮次(Round)作为核心抽象

轮次(Round)是工作流执行的基本单位，每个轮次对应一个特定工作流的特定阶段。通过使用统一的轮次抽象，解释器可以以一致的方式处理不同类型的工作流和阶段。

```
工作流类型(workflow_name) + 阶段类型(stage_name) = 轮次
例如: dev:story, dev:coding, doc:research
```

#### 轮次的结构

每个轮次包含:

- **工作流名称**: 工作流的名称(如dev, doc)
- **阶段名称**: 阶段的名称(如story, coding, research)
- **检查清单**: 本阶段需要完成的项目列表
- **交付物**: 本阶段需要产出的内容列表
- **上下文**: 包含前序阶段信息和当前状态
- **描述**: 阶段的详细说明

#### 常见轮次类型

| 工作流名称 | 阶段名称 | 对应的交付物 |
|------------|--------|-------------|
| dev | story | 用户故事、验收标准 |
| dev | spec | 技术规格、API设计 |
| dev | coding | 实现代码、单元测试 |
| dev | test | 测试报告、覆盖率报告 |
| dev | review | 代码审查报告、优化建议 |
| doc | research | 研究笔记、参考资料 |
| doc | outline | 文档大纲、章节划分 |
| doc | draft | 初稿文档 |
| doc | review | 审查意见、修订建议 |

#### 解释器的角色

工作流解释器的主要职责是:

1. 提供工作流的定义和结构
2. 加载和管理工作流上下文
3. 引导工作流的执行过程
4. 记录和跟踪工作流的状态
5. 输出阶段性交付物

解释器不直接执行工作，而是提供指引和环境，由开发者或其他工具去执行具体任务。

#### 命令格式

工作流命令统一为以下格式:

```bash
vc flow run <workflow_name>:<stage_name> [--name=<实例名称>] [--completed=<已完成项>]
```

例如:
```bash
vc flow run dev:coding --name="实现登录功能" --completed="需求分析,设计方案"
```

创建工作流:
```bash
vc flow create <workflow_name> --name="名称"
```

获取上下文:
```bash
vc flow context <workflow_id> [<stage_id>]
```

导出工作流:
```bash
vc flow export <workflow_id> [--format=<格式>]
```

#### 命令执行模式

工作流命令遵循以下执行流程:

1. 解析命令参数
2. 加载相关工作流定义
3. 创建或加载阶段上下文
4. 执行阶段操作
5. 更新工作流状态
6. 返回执行结果

#### 优势

1. **统一接口**: 所有工作流阶段通过相同的命令格式执行
2. **依赖关系清晰**: 阶段间的依赖和数据流动更加明确
3. **可扩展性**: 新工作流和阶段可以轻松添加而不需要修改核心代码
4. **上下文管理**: 提供一致的上下文处理机制
5. **生命周期管理**: 支持阶段的完整生命周期管理

## 9. 结论

通过本次重构，我们将建立一个更为健壮、一致和可扩展的命令系统，为开发者提供更好的工具支持，同时为用户提供更一致的使用体验。特别是对于工作流解释器，我们引入了泛化的stage概念，提供了高度可扩展的架构，使解释器能够适应不同类型的工作流，并通过统一的接口提供指导。这种设计确保了命令系统成为AI Agent的得力助手，提供清晰的上下文和引导，协助Agent完成复杂的开发任务。这将大大提高VibeCopilot的整体质量，并为未来功能扩展奠定坚实基础。
