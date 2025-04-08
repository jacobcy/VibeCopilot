"""
规则管理命令模块

处理规则相关的命令，包括创建、查看、修改、删除规则等操作。
"""

import logging
from typing import Any, Dict, List

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.cli.commands.rule.core import RuleCommandExecutor, parse_rule_args
from src.cli.commands.rule.rule_command_utils import convert_result, show_help
from src.templates.core.rule_generator import RuleGenerator
from src.templates.core.template_engine import TemplateEngine
from src.templates.core.template_manager import TemplateManager
from src.workflow.workflow_utils import get_session

logger = logging.getLogger(__name__)


class RuleCommand(BaseCommand, Command):
    """规则管理命令处理器"""

    def __init__(self):
        super().__init__("rule", "规则管理命令")
        self.template_engine = TemplateEngine()
        # 获取数据库会话并使用它初始化TemplateManager
        self.session = get_session()
        self.template_manager = TemplateManager(session=self.session)
        self.rule_generator = RuleGenerator(template_engine=self.template_engine)

        # 初始化命令执行器
        self.command_executor = RuleCommandExecutor(
            session=self.session, template_engine=self.template_engine, template_manager=self.template_manager, rule_generator=self.rule_generator
        )

    # 实现新接口
    @classmethod
    def get_command(cls) -> str:
        return "rule"

    @classmethod
    def get_description(cls) -> str:
        return "规则管理命令"

    @classmethod
    def get_help(cls) -> str:
        return """
规则管理命令

用法:
    rule list                  列出所有规则
    rule list [--type=<rule_type>] [--verbose]     列出特定类型的规则
    rule show <id> [--format=<json|text>]         显示规则详情
    rule create <template_type> <n> [--vars=<json>]  创建新规则
    rule update <id> [--vars=<json>]       更新规则
    rule delete <id> [--force]          删除规则
    rule validate <id> [--all]         验证规则
    rule export <id> [--output=<path>] [--format=<format>]  导出规则
    rule import <file_path> [--overwrite]       导入规则

参数:
    <id>                  规则ID
    <template_type>       模板类型
    <n>                规则名称
    <file_path>           规则文件路径

选项:
    --type=<rule_type>    规则类型
    --format=<format>     输出格式 (json或text)
    --vars=<json>         变量值（JSON格式）
    --output=<path>       输出路径
    --force               强制执行危险操作
    --verbose             显示详细信息
    --all                 处理所有规则
    --overwrite           覆盖已存在的规则
"""

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        return parse_rule_args(args)

    def execute(self, args) -> None:
        """执行命令 - 适配新接口"""
        # 处理参数
        parsed_args = {}
        if isinstance(args, list):
            # 如果是列表参数，首先解析成字典
            if not args or "--help" in args or "-h" in args:
                print(self.get_help())
                return
            parsed_args = self.parse_args(args)
        elif isinstance(args, dict):
            # 如果已经是字典，直接使用
            parsed_args = args
            # 处理帮助标识
            if not parsed_args or parsed_args.get("show_help", False):
                print(self.get_help())
                return
        else:
            # 不支持其他类型参数
            print("错误: 不支持的参数类型")
            return

        # 执行命令并获取结果
        result = self._execute_impl(parsed_args)

        # 格式化输出
        if isinstance(result, dict):
            if result.get("success", False):
                # 输出结果
                if "message" in result:
                    print(result["message"])
                if "data" in result:
                    data = result["data"]
                    # 根据数据类型选择合适的输出方式
                    if isinstance(data, list):
                        for item in data:
                            print(convert_result(item))
                    else:
                        print(convert_result(data))
            else:
                # 输出错误
                error_message = result.get("error", "未知错误")
                print(f"错误: {error_message}")

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        实现命令执行逻辑

        Args:
            args: 命令参数

        Returns:
            执行结果
        """
        return self.command_executor.execute_command(args)
