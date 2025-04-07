"""
Cursor命令处理器模块

负责：
- 处理Cursor IDE命令
- 集成规则系统
- 管理IDE交互
"""

import logging
from typing import Any, Dict, List, Tuple

from src.cli.command_parser import CommandParser
from src.core.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


class CursorCommandHandler:
    """Cursor命令处理器类"""

    def __init__(self):
        """初始化命令处理器"""
        self.command_parser = CommandParser()
        self.rule_engine = RuleEngine()
        self._register_handlers()

    def _register_handlers(self):
        """注册命令处理器
        注意：命令处理器现在通过CommandParser自动注册
        """
        pass

    def handle_command(self, command: str) -> Dict[str, Any]:
        """处理命令

        Args:
            command: The command string like "/check --type=task --id=T2.1"

        Returns:
            Dict[str, Any]: Processing result with structured feedback for AI agent
        """
        logger.info(f"收到命令: {command}")

        try:
            # 首先尝试使用规则引擎处理
            rule_result = self.rule_engine.process_command(command)
            if rule_result.get("handled", False):
                logger.info(f"规则引擎处理结果: {rule_result}")
                # 增强AI友好的结果反馈
                return self._enhance_result_for_agent(rule_result)

            # 如果规则引擎未处理，解析命令结构
            command_name, args = self._parse_command(command)
            logger.debug(f"解析结果 - 命令: {command_name}, 参数: {args}")

            # 使用命令解析器执行命令
            result = self.command_parser.execute_command(command_name, args)
            logger.info(f"命令执行结果: {result}")
            # 增强AI友好的结果反馈
            return self._enhance_result_for_agent(result)

        except ValueError as ve:
            error_msg = f"命令格式错误: {str(ve)}"
            logger.error(error_msg)
            # 返回结构化的错误信息，包含建议
            return {
                "success": False,
                "error": error_msg,
                "error_type": "ValueError",
                "suggestions": self._get_command_suggestions(command),
                "verbose": self._get_verbose_error_info(ve),
            }
        except Exception as e:
            error_msg = f"处理命令失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # 返回结构化的错误信息，包含建议和详细信息
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__,
                "suggestions": self._get_error_suggestions(e),
                "verbose": self._get_verbose_error_info(e),
            }

    def _enhance_result_for_agent(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """增强结果以便AI agent更好地处理

        Args:
            result: 原始结果字典

        Returns:
            Dict[str, Any]: 增强后的结果字典
        """
        # 如果结果已经包含成功标志
        if "success" not in result:
            result["success"] = True

        # 如果操作失败，添加建议
        if result.get("success") is False and "suggestions" not in result:
            if "error" in result:
                result["suggestions"] = self._get_error_suggestions_from_message(result["error"])

        # 添加进度信息（如果有）
        if "progress" in result and isinstance(result["progress"], (int, float)):
            progress = result["progress"]
            progress_bar = self._generate_progress_bar(progress)
            result["progress_display"] = progress_bar

        # 添加AI友好的摘要
        if "summary" not in result:
            result["summary"] = self._generate_summary(result)

        return result

    def _generate_progress_bar(self, progress: float, width: int = 20) -> str:
        """生成进度条显示

        Args:
            progress: 进度百分比 (0-100)
            width: 进度条宽度

        Returns:
            str: 文本进度条
        """
        filled = int(width * progress / 100)
        bar = "=" * filled + ">" + " " * (width - filled - 1)
        return f"[{bar}] {progress:.1f}%"

    def _generate_summary(self, result: Dict[str, Any]) -> str:
        """从结果生成简洁摘要

        Args:
            result: 结果字典

        Returns:
            str: 摘要文本
        """
        if not result.get("success", True):
            return f"❌ 操作失败: {result.get('error', '未知错误')}"

        command = result.get("command", "")
        if "created" in result:
            return f"✅ 已创建: {result['created']}"
        elif "updated" in result:
            return f"✅ 已更新: {result['updated']}"
        elif "deleted" in result:
            return f"✅ 已删除: {result['deleted']}"
        elif "list" in result:
            count = len(result["list"]) if isinstance(result["list"], list) else "多个"
            return f"📋 已列出 {count} 个项目"
        else:
            return f"✅ 命令执行成功"

    def _get_command_suggestions(self, command: str) -> List[str]:
        """根据错误的命令提供建议

        Args:
            command: 输入的命令

        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        try:
            # 基本命令格式建议
            if not command.startswith("/"):
                suggestions.append("命令必须以'/'开头，例如: /help")

            parts = command.strip().split()
            if len(parts) > 0:
                cmd = parts[0].lstrip("/")

                # 检查是否是已知命令
                available_commands = self.get_available_commands()
                command_names = [c["name"] for c in available_commands]

                # 如果不是已知命令，推荐相似命令
                if cmd not in command_names:
                    similar = self._get_similar_commands(cmd, command_names)
                    if similar:
                        suggestions.append(f"您是否想使用: {', '.join(['/' + s for s in similar])}")

                # 添加命令帮助提示
                suggestions.append(f"尝试使用 '/help {cmd}' 获取命令帮助")

        except Exception:
            # 如果建议生成过程出错，提供通用建议
            suggestions.append("尝试使用 '/help' 查看所有可用命令")

        if not suggestions:
            suggestions.append("尝试使用 '/help' 查看所有可用命令")

        return suggestions

    def _get_similar_commands(self, cmd: str, command_list: List[str]) -> List[str]:
        """查找相似命令

        Args:
            cmd: 用户输入的命令
            command_list: 可用命令列表

        Returns:
            List[str]: 相似命令列表
        """
        similar = []
        for available_cmd in command_list:
            # 简单的相似度检查 - 可以用更复杂的算法替代
            if cmd in available_cmd or available_cmd in cmd:
                similar.append(available_cmd)

        return similar[:3]  # 限制最多3个建议

    def _get_error_suggestions(self, error: Exception) -> List[str]:
        """根据异常提供建议

        Args:
            error: 捕获的异常

        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        error_type = type(error).__name__
        error_msg = str(error)

        # 根据错误类型提供特定建议
        if error_type == "ConnectionError":
            suggestions.append("检查网络连接是否正常")
            suggestions.append("确认API服务是否在运行")
        elif error_type == "PermissionError":
            suggestions.append("检查文件或资源的访问权限")
        elif error_type == "FileNotFoundError":
            suggestions.append("检查文件路径是否正确")
            suggestions.append("确认文件是否存在")
        elif "timeout" in error_msg.lower():
            suggestions.append("操作超时，请稍后重试")
            suggestions.append("检查网络连接速度")
        elif "database" in error_msg.lower():
            suggestions.append("检查数据库连接配置")
            suggestions.append("尝试运行 '/db init' 初始化数据库")

        # 添加通用建议
        if not suggestions:
            suggestions.append("尝试使用 '--verbose' 参数获取更多信息")
            suggestions.append("检查命令参数是否正确")

        return suggestions

    def _get_error_suggestions_from_message(self, error_msg: str) -> List[str]:
        """从错误消息文本生成建议

        Args:
            error_msg: 错误消息

        Returns:
            List[str]: 建议列表
        """
        suggestions = []

        # 分析错误消息关键词
        if "未找到" in error_msg or "not found" in error_msg.lower():
            suggestions.append("检查ID或名称是否正确")
            suggestions.append("先列出可用项，确认目标存在")
        elif "已存在" in error_msg or "already exists" in error_msg.lower():
            suggestions.append("使用不同的名称或ID")
            suggestions.append("或使用 '--force' 参数覆盖现有项")
        elif "缺少参数" in error_msg or "missing" in error_msg.lower():
            suggestions.append("检查是否提供了所有必需参数")
        elif "格式错误" in error_msg or "invalid format" in error_msg.lower():
            suggestions.append("检查参数格式是否正确")

        # 添加通用建议
        if not suggestions:
            suggestions.append("尝试使用 '--verbose' 参数获取更多信息")

        return suggestions

    def _get_verbose_error_info(self, error: Exception) -> Dict[str, Any]:
        """获取详细的错误信息

        Args:
            error: 捕获的异常

        Returns:
            Dict[str, Any]: 详细错误信息
        """
        return {
            "error_type": type(error).__name__,
            "error_msg": str(error),
            "traceback": logger.handlers[0].formatter.formatException(error.__traceback__)
            if hasattr(error, "__traceback__")
            else None,
        }

    def _parse_command(self, command_str: str) -> Tuple[str, Dict[str, Any]]:
        """解析命令字符串，返回命令名称和参数字典

        Args:
            command_str: 命令字符串，如 "/check --type=task --id=T2.1"

        Returns:
            Tuple[str, Dict[str, Any]]: 命令名称和参数字典
        """
        if not command_str.startswith("/"):
            raise ValueError("命令必须以'/'开头")

        parts = command_str[1:].strip().split()
        if not parts:
            raise ValueError("无效的命令格式")

        command_name = parts[0]
        args = {}

        # 解析参数
        for part in parts[1:]:
            if part.startswith("--"):
                if "=" in part:
                    key, value = part[2:].split("=", 1)
                    args[key] = self._convert_arg_value(value)
                else:
                    args[part[2:]] = True
            elif "=" in part and not part.startswith("-"):
                # 支持不带--前缀的key=value格式
                key, value = part.split("=", 1)
                args[key] = self._convert_arg_value(value)

        # 检查是否有verbose标志
        if "verbose" in args:
            args["verbose"] = True

        return command_name, args

    def _convert_arg_value(self, value: str) -> Any:
        """尝试将参数值转换为适当的类型

        Args:
            value: 参数值字符串

        Returns:
            转换后的参数值
        """
        # 尝试转换为布尔值
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # 尝试转换为整数
        try:
            return int(value)
        except ValueError:
            pass

        # 尝试转换为浮点数
        try:
            return float(value)
        except ValueError:
            pass

        # 保持字符串类型
        return value

    def get_available_commands(self) -> List[Dict[str, str]]:
        """获取所有可用命令的列表

        Returns:
            List[Dict[str, str]]: 可用命令列表，每个命令包含名称和描述
        """
        return self.command_parser.get_available_commands()

    def get_command_help(self, command_name: str) -> Dict[str, Any]:
        """获取指定命令的帮助信息

        Args:
            command_name: 命令名称

        Returns:
            Dict[str, Any]: 命令帮助信息，包含命令用法和示例
        """
        help_info = self.command_parser.get_command_help(command_name)

        # 增强帮助信息，添加示例用法
        if help_info and "examples" not in help_info:
            help_info["examples"] = self._get_command_examples(command_name)

        return help_info

    def _get_command_examples(self, command_name: str) -> List[str]:
        """获取命令示例用法

        Args:
            command_name: 命令名称

        Returns:
            List[str]: 示例用法列表
        """
        # 基础命令示例
        basic_examples = {
            "help": ["/help", "/help rule", "/help --verbose"],
            "rule": ["/rule list", "/rule show rule_id", "/rule create template_type 名称"],
            "flow": ["/flow list", "/flow show workflow_id", "/flow run --type=story"],
            "roadmap": ["/roadmap list", "/roadmap show roadmap_id", "/roadmap switch roadmap_id"],
            "task": [
                "/task list",
                "/task create --title=任务标题",
                "/task update task_id --status=进行中",
            ],
            "status": ["/status show", "/status flow", "/status update --phase=开发"],
            "memory": [
                "/memory list",
                "/memory search --query=关键词",
                "/memory create --title=标题 --folder=目录",
            ],
            "db": ["/db list --type=rule", "/db show --type=task --id=1", "/db backup"],
        }

        return basic_examples.get(command_name, [f"/{command_name}"])
