# VibeCopilot 命令系统

VibeCopilot的命令系统提供了一个统一的接口，用于执行各种操作和管理项目。本文档介绍命令系统的设计、实现和使用方法。

## 核心组件

命令系统由以下核心组件组成：

### 1. 命令处理器 (`CursorCommandHandler`)

`CursorCommandHandler` 是命令系统的入口点，负责接收命令字符串，解析命令，并调用相应的命令处理类。

**主要职责：**

- 接收和解析命令字符串
- 查找对应的命令处理类
- 执行命令并返回结果
- 提供命令帮助信息

### 2. 命令解析器 (`CommandParser`)

`CommandParser` 负责解析命令字符串，并找到对应的命令处理类。

**主要职责：**

- 注册可用命令
- 解析命令字符串和参数
- 验证命令格式和参数
- 提供命令列表和帮助信息

### 3. 基础命令类 (`BaseCommand`)

`BaseCommand` 是所有命令处理类的基类，提供了参数处理、验证和执行的通用逻辑。

**主要职责：**

- 定义命令接口和生命周期
- 管理命令参数（注册、验证、获取）
- 提供帮助和示例信息
- 实现命令执行流程

### 4. 具体命令类

每个具体命令都是 `BaseCommand` 的子类，实现特定的命令逻辑。

**常见命令：**

- `CheckCommand`: 检查项目状态
- `UpdateCommand`: 更新项目信息
- `GitHubCommand`: 执行GitHub相关操作

## 命令执行流程

1. 用户输入命令字符串（如 `/github --action=check`）
2. `CursorCommandHandler` 接收命令并转发给 `CommandParser`
3. `CommandParser` 解析命令，找到对应的命令处理类（如 `GitHubCommand`）
4. 命令处理类验证参数并执行 `_execute_impl` 方法
5. 返回标准化的结果

## 命令格式

命令遵循以下格式：

```
/命令名 --参数1=值1 --参数2=值2 ...
```

例如：

```
/github --action=check --type=roadmap
/github --action=list --type=task --milestone=M2
/update --id=T2.1 --status=completed
```

## 标准化结果

所有命令都返回标准化的结果格式：

```json
{
  "success": true|false,
  "command": "命令名",
  "data": {
    // 命令的执行结果
  },
  "error": "错误信息（如果失败）"
}
```

## 添加新命令

要添加新命令，需要执行以下步骤：

1. 在 `src/cli/commands/` 目录下创建新的命令类
2. 继承 `BaseCommand` 类
3. 在 `__init__` 方法中注册命令和参数
4. 实现 `_execute_impl` 方法
5. 实现 `get_examples` 方法

示例：

```python
from typing import List, Dict, Any
from src.cli.commands.base_command import BaseCommand

class NewCommand(BaseCommand):
    def __init__(self):
        super().__init__("newcomm", "执行新命令操作")

        # 注册参数
        self.register_parameter("action", required=True, help="要执行的操作")
        self.register_parameter("id", required=False, help="操作ID")

    def _execute_impl(self) -> Dict[str, Any]:
        # 获取参数
        action = self.get_parameter("action")
        item_id = self.get_parameter("id")

        # 执行命令逻辑
        result = {
            "message": f"执行了 {action} 操作"
        }

        if item_id:
            result["id"] = item_id

        return result

    def get_examples(self) -> List[str]:
        return [
            "/newcomm --action=test",
            "/newcomm --action=run --id=123"
        ]
```

6. 在 `CommandParser` 中注册新命令：

```python
parser.register_command(NewCommand())
```

## 使用工具

VibeCopilot提供了两个主要工具来使用命令系统：

1. **GitHub CLI工具** (`scripts/github_cli.py`)：简化的命令行接口
2. **GitHub项目管理工具** (`scripts/github/manage_project.py`)：交互式项目管理工具

详细使用方法请参考 `scripts/README.md`。

## 最佳实践

1. **命令参数验证**：在执行命令前，确保所有必需参数都已提供
2. **错误处理**：命令执行时捕获异常，确保返回友好的错误信息
3. **参数命名**：使用清晰一致的参数命名规范
4. **命令文档**：提供完整的命令描述和示例
5. **测试**：对每个命令编写单元测试，确保功能正确性
