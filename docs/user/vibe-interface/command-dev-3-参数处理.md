# VibeCopilot 命令系统开发指南 - 参数处理与模块交互篇

## 5. 命令参数处理

### 5.1 参数验证

命令参数验证是确保命令正确执行的关键步骤：

```python
def validate_args(self, args: Dict[str, Any]) -> bool:
    """验证命令参数"""
    # 必需参数检查
    required_args = ["type"]
    for arg in required_args:
        if arg not in args:
            logging.warning(f"缺少必需参数: {arg}")
            return False

    # 参数值验证
    valid_types = ["task", "milestone", "project"]
    if args.get("type") not in valid_types:
        logging.warning(f"无效的类型值: {args.get('type')}")
        return False

    return True
```

### 5.2 参数转换

某些参数可能需要类型转换或标准化：

```python
def _prepare_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """准备和转换参数"""
    result = args.copy()

    # 布尔值转换
    if "force" in result:
        if isinstance(result["force"], str):
            result["force"] = result["force"].lower() in ["true", "yes", "1"]

    # 数值转换
    if "limit" in result:
        try:
            result["limit"] = int(result["limit"])
        except ValueError:
            result["limit"] = 10  # 默认值

    # 枚举值标准化
    if "status" in result:
        status_map = {
            "todo": "todo",
            "in_progress": "in_progress",
            "in-progress": "in_progress",
            "done": "completed",
            "completed": "completed"
        }
        result["status"] = status_map.get(result["status"].lower(), result["status"])

    return result
```

## 6. 命令模块交互

### 6.1 调用其他模块

命令处理器通常需要调用项目的其他功能模块：

```python
from src.core.config import ConfigManager
from scripts.github_project.api.github_client import GitHubClient

def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """执行更新命令"""
    # 准备参数
    prepared_args = self._prepare_args(args)

    # 读取配置
    config = ConfigManager().get_config()

    # 初始化客户端
    github_client = GitHubClient(token=config.get("github_token"))

    # 执行操作
    if "github" in prepared_args:
        result = github_client.update_issue(
            issue_id=prepared_args.get("id"),
            status=prepared_args.get("status")
        )

    # 返回结果
    return {
        "success": True,
        "message": "更新成功",
        "data": result
    }
```

### 6.2 返回结果格式

命令处理结果应遵循一致的格式：

```python
{
    "success": bool,          # 是否成功
    "message": str,           # 简短消息
    "data": Dict[str, Any],   # 详细数据（可选）
    "error": str              # 错误信息（失败时）
}
```
