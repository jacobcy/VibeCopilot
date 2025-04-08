# VibeCopilot 命令系统开发指南 - 测试与最佳实践篇

## 8. 测试与调试

### 8.1 单元测试

为命令处理器编写单元测试：

```python
# tests/cli/commands/test_task_command.py
import pytest
from src.cli.commands.task_command import TaskCommand

def test_task_command_validation():
    """测试任务命令参数验证"""
    command = TaskCommand()

    # 测试有效参数
    assert command.validate_args({"list": True}) is True
    assert command.validate_args({"id": "T1.1"}) is True

    # 测试无效参数
    assert command.validate_args({}) is False

def test_task_command_execution():
    """测试任务命令执行"""
    command = TaskCommand()

    # 测试列出任务
    result = command.execute({"list": True})
    assert result["success"] is True
    assert "tasks" in result["data"]

    # 测试更新任务
    result = command.execute({"id": "T1.1", "status": "completed"})
    assert result["success"] is True
    assert result["data"]["id"] == "T1.1"
    assert result["data"]["status"] == "completed"
```

### 8.2 集成测试

测试命令系统与其他组件的集成：

```python
# tests/integration/test_command_system.py
import pytest
from src.cursor.command_handler import CursorCommandHandler

def test_command_handler_integration():
    """测试命令处理器集成"""
    handler = CursorCommandHandler()

    # 测试检查命令
    result = handler.handle_command("/check --type=task")
    assert result["success"] is True

    # 测试任务命令
    result = handler.handle_command("/task --list")
    assert result["success"] is True
    assert "tasks" in result["data"]
```

### 8.3 调试技巧

调试命令处理问题：

1. 开启详细日志：

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. 单独测试命令解析：

   ```python
   from src.cli.command_parser import CommandParser

   parser = CommandParser()
   name, args = parser.parse_command("/task --id=T1.1 --status=completed")
   print(f"命令名称: {name}")
   print(f"命令参数: {args}")
   ```

3. 直接调用命令处理器：

   ```python
   from src.cli.commands.task_command import TaskCommand

   task_command = TaskCommand()
   result = task_command.execute({"id": "T1.1", "status": "completed"})
   print(result)
   ```

## 9. 最佳实践

### 9.1 错误处理

命令处理器应实现全面的错误处理：

```python
def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # 验证必要条件
        if not self._check_prerequisites():
            return {"success": False, "error": "前置条件未满足"}

        # 执行操作
        result = self._perform_operation(args)
        return {"success": True, "data": result}

    except ValueError as e:
        # 参数错误
        return {"success": False, "error": f"参数错误: {str(e)}"}

    except ConnectionError as e:
        # 网络错误
        return {"success": False, "error": f"网络错误: {str(e)}"}

    except Exception as e:
        # 未预期的错误
        logging.error(f"命令执行异常: {str(e)}", exc_info=True)
        return {"success": False, "error": f"执行失败: {str(e)}"}
```

### 9.2 命令设计原则

设计高质量命令的原则：

1. **单一职责**：每个命令应专注于一个功能点
2. **参数验证**：详细验证所有参数
3. **清晰反馈**：提供明确的成功/失败信息
4. **幂等性**：相同命令多次执行应产生相同结果
5. **错误恢复**：失败时不应留下部分状态变更

### 9.3 文档和注释

为命令处理器添加完整的文档和注释：

```python
class TaskCommand(BaseCommand):
    """
    任务管理命令处理器

    负责处理与项目任务相关的操作，包括：
    - 列出任务 (/task --list)
    - 更新任务 (/task --id=<任务ID> --status=<状态>)
    - 分配任务 (/task --id=<任务ID> --assignee=<用户名>)

    示例:
        /task --list
        /task --id=T1.1 --status=completed
        /task --id=T2.1 --assignee=<username>
    """

    def __init__(self):
        super().__init__("task", "管理项目任务")
```
