# VibeCopilot 命令行工具

本目录包含VibeCopilot项目的命令行工具，用于简化项目管理和开发流程。

## 可用工具

### 1. GitHub CLI工具 (`github_cli.py`)

简化的命令行接口，用于执行GitHub相关操作。

**使用方法:**

```bash
# 查看帮助信息
python scripts/github_cli.py

# 检查路线图状态
python scripts/github_cli.py --action=check --type=roadmap

# 列出特定里程碑的任务
python scripts/github_cli.py --action=list --type=task --milestone=M2

# 更新任务状态
python scripts/github_cli.py --action=update --type=task --id=T2.1 --status=completed

# 创建新任务
python scripts/github_cli.py --action=story --type=task --title="实现新功能" --milestone=M2 --priority=P1

# 同步数据
python scripts/github_cli.py --action=sync --direction=to-github
```

### 2. GitHub项目管理工具 (`github/manage_project.py`)

交互式项目管理工具，提供更丰富的界面和功能。

**使用方法:**

```bash
# 运行交互式模式
python scripts/github/manage_project.py --interactive

# 检查路线图状态
python scripts/github/manage_project.py --check

# 列出特定里程碑的任务
python scripts/github/manage_project.py --list M2

# 更新任务状态
python scripts/github/manage_project.py --update T2.1 completed

# 创建新任务
python scripts/github/manage_project.py --create "实现新功能" M2 P1 "这是一个新功能的描述"

# 同步数据
python scripts/github/manage_project.py --sync to-github
```

## 命令系统架构

这些工具基于VibeCopilot的命令处理系统实现。命令处理流程如下：

1. 用户输入命令字符串（例如 `/github --action=check`）
2. `CursorCommandHandler` 解析命令并找到对应的命令处理类
3. 命令处理类验证参数并执行操作
4. 返回标准化的结果

## 开发新命令

要添加新命令，按照以下步骤操作：

1. 在 `src/cli/commands/` 目录下创建新的命令类
2. 继承 `BaseCommand` 类并实现 `_execute_impl` 方法
3. 在命令类的构造函数中注册命令参数
4. 将命令类注册到 `CommandParser` 中

示例：

```python
from src.cli.commands.base_command import BaseCommand

class MyCommand(BaseCommand):
    def __init__(self):
        super().__init__("mycommand", "执行我的自定义操作")
        self.register_parameter("action", required=True, help="要执行的操作")
        self.register_parameter("type", required=True, help="操作类型")

    def _execute_impl(self):
        action = self.get_parameter("action")
        type = self.get_parameter("type")

        # 实现命令逻辑
        result = {"message": f"执行了 {action} 操作，类型为 {type}"}

        return result

    def get_examples(self):
        return [
            "/mycommand --action=check --type=status",
            "/mycommand --action=update --type=config"
        ]
```
