# VibeCopilot 命令系统开发指南 - 集成与规则篇

## 7. 命令系统与 Cursor Rules 的集成

VibeCopilot 的命令行工具与 Cursor IDE 命令系统可以协同工作，共享底层功能逻辑。以下是两个系统的集成方式：

### 7.1 共享代码模式

命令行工具和 Cursor Rules 可以共享核心业务逻辑，只在接口层面有区别：

```python
# 共享的业务逻辑 (src/core/rule_manager.py)
class RuleManager:
    """规则管理的核心业务逻辑"""

    def list_rules(self, filter_type=None):
        """列出规则"""
        # 实现规则列出逻辑
        return rules_list

    def create_rule(self, template_type, name, variables):
        """创建规则"""
        # 实现规则创建逻辑
        return created_rule

# 命令行工具使用方式 (src/cli/commands/rule_command.py)
from src.rule_manager import RuleManager

class RuleCommand(BaseCommand):
    def __init__(self):
        super().__init__("rule", "规则管理")
        self.rule_manager = RuleManager()

    def _list_rules(self, args):
        filter_type = args.get("type")
        rules = self.rule_manager.list_rules(filter_type)
        return {"success": True, "data": rules}

# Cursor Rules 处理函数 (src/cursor/rule_functions.py)
from src.rule_manager import RuleManager

def handle_list_rules(args):
    """处理 /rule list 命令"""
    manager = RuleManager()
    filter_type = args.get("type")
    rules = manager.list_rules(filter_type)
    return format_rule_list_for_display(rules)
```

### 7.2 命令调用关系

在某些情况下，Cursor IDE 命令可能会调用命令行工具进行操作：

```python
def handle_rule_command(command_str):
    """处理 /rule 命令 (在 Cursor Rules 中)"""
    # 解析命令
    args = parse_command(command_str)

    # 调用命令行工具的相应功能
    from subprocess import run, PIPE
    cmd = ["vibecopilot", "rule"]

    # 转换参数
    for k, v in args.items():
        if v is True:
            cmd.append(f"--{k}")
        else:
            cmd.append(f"--{k}={v}")

    # 执行命令
    result = run(cmd, stdout=PIPE, text=True)
    return result.stdout
```

### 7.3 两种方式的选择指南

在开发时，需要考虑命令应该如何实现：

1. **仅作为命令行工具**：适用于纯操作性功能，不需要 AI 协助
2. **仅作为 Cursor IDE 命令**：适用于需要深度 AI 理解和上下文的功能
3. **两种方式都实现**：大多数核心功能应该两种方式都支持

无论选择哪种实现方式，都应尽量共享底层业务逻辑，减少代码重复。
