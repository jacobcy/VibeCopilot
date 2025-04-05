# VibeCopilot 命令系统开发指南 - 实际应用示例篇

## 10. 实际应用示例

### 10.1 GitHub集成命令

```python
# src/cli/commands/github_command.py
import logging
from typing import Dict, Any

from src.cli.base_command import BaseCommand
from scripts.github_project.api.github_client import GitHubClient
from src.core.config import ConfigManager

class GitHubCommand(BaseCommand):
    """GitHub操作命令处理器"""

    def __init__(self):
        super().__init__("github", "GitHub项目管理")
        self.client = None

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """验证GitHub命令参数"""
        if not args:
            return False

        # 验证子命令
        valid_subcommands = ["list", "create", "update", "close", "show"]
        subcommand = next((key for key in args if key in valid_subcommands), None)

        if not subcommand:
            return False

        # 验证项目参数
        if subcommand != "list" and "project" not in args:
            return False

        return True

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行GitHub命令"""
        # 初始化客户端
        self._init_client()

        # 执行子命令
        if "list" in args:
            return self._list_resources(args)

        if "create" in args:
            return self._create_resource(args)

        if "update" in args:
            return self._update_resource(args)

        if "close" in args:
            return self._close_resource(args)

        if "show" in args:
            return self._show_resource(args)

        return {"success": False, "error": "未知的子命令"}

    def _init_client(self):
        """初始化GitHub客户端"""
        if not self.client:
            config = ConfigManager().get_config()
            token = config.get("github_token")

            if not token:
                raise ValueError("未配置GitHub令牌")

            self.client = GitHubClient(token=token)

    def _list_resources(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """列出GitHub资源"""
        resource_type = args.get("type", "issues")
        project = args.get("project")

        if resource_type == "issues":
            issues = self.client.list_issues(project)
            return {
                "success": True,
                "message": f"项目 {project} 的问题列表",
                "data": {"issues": issues}
            }

        if resource_type == "projects":
            projects = self.client.list_projects()
            return {
                "success": True,
                "message": "项目列表",
                "data": {"projects": projects}
            }

        return {"success": False, "error": f"不支持的资源类型: {resource_type}"}

    # 其他方法实现...
```

### 10.2 调用外部服务

```python
from src.external.weather_service import WeatherService

def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """执行天气命令"""
    city = args.get("city", "北京")

    # 调用外部服务
    weather_service = WeatherService()
    weather_data = weather_service.get_weather(city)

    if not weather_data:
        return {"success": False, "error": f"无法获取{city}的天气信息"}

    return {
        "success": True,
        "message": f"{city}的天气情况",
        "data": weather_data
    }
```

## 结语

通过本指南，您应该了解了如何在VibeCopilot命令系统中开发新的命令处理器。遵循这些最佳实践，可以确保您的命令处理器能够与Cursor Rules系统无缝集成，并为用户提供一致、可靠的命令体验。

如有任何问题或需要进一步的帮助，请随时联系开发团队。
