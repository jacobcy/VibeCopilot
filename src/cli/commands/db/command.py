"""
数据库命令主模块

整合所有数据库命令处理器，提供统一命令接口
"""

import argparse
import logging
from typing import Any, Dict, List

from src.cli.commands.db.backup_handler import BackupHandler
from src.cli.commands.db.base import BaseDatabaseCommand
from src.cli.commands.db.create_handler import CreateHandler
from src.cli.commands.db.delete_handler import DeleteHandler
from src.cli.commands.db.init_handler import InitHandler
from src.cli.commands.db.list_handler import ListHandler
from src.cli.commands.db.query_handler import QueryHandler
from src.cli.commands.db.restore_handler import RestoreHandler
from src.cli.commands.db.show_handler import ShowHandler
from src.cli.commands.db.update_handler import UpdateHandler

logger = logging.getLogger(__name__)


class DatabaseCommand(BaseDatabaseCommand):
    """数据库命令处理器"""

    def __init__(self):
        """初始化数据库命令"""
        super().__init__()
        self._handlers = {
            "init": InitHandler(),
            "list": ListHandler(),
            "show": ShowHandler(),
            "query": QueryHandler(),
            "create": CreateHandler(),
            "update": UpdateHandler(),
            "delete": DeleteHandler(),
            "backup": BackupHandler(),
            "restore": RestoreHandler(),
        }

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """实现命令执行逻辑

        Args:
            args: 命令参数

        Returns:
            执行结果
        """
        # 解析参数并执行子命令
        result_code = self.execute(args)
        # 返回执行结果
        return {"code": result_code, "success": result_code == 0}

    @classmethod
    def get_help(cls) -> str:
        return """
数据库管理命令

用法:
  vibecopilot db init                          - 初始化数据库
  vibecopilot db list --type=<entity_type>     - 列出数据库内容
  vibecopilot db show --type=<entity_type> --id=<id> - 显示数据库条目
  vibecopilot db query --type=<类型>           - 查询实体列表或单个实体
  vibecopilot db create --type=<类型> --data='json字符串'  - 创建实体
  vibecopilot db update --type=<类型> --id=<ID> --data='json字符串'  - 更新实体
  vibecopilot db delete --type=<类型> --id=<ID>  - 删除实体
  vibecopilot db backup [--output=<备份路径>]  - 备份数据库
  vibecopilot db restore <备份文件>            - 恢复数据库

参数:
  --type      实体类型(epic/story/task/label/template)
  --id        实体ID
  --data      JSON格式的数据
  --format    输出格式(text/json)，默认为text
  --query     查询字符串
  --verbose   显示详细信息
  --output    备份文件输出路径
  --force     强制执行操作，不提示确认
"""

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        if not args or "--help" in args or "-h" in args:
            parsed["show_help"] = True
            return parsed

        # 获取子命令
        subcommand = args.pop(0)
        parsed["subcommand"] = subcommand

        # 解析子命令参数
        parser = argparse.ArgumentParser(prog=f"db {subcommand}", add_help=False)

        if subcommand == "init":
            # 初始化子命令不需要其他参数
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
            parser.add_argument("--force", action="store_true", help="强制重新初始化数据库")

        elif subcommand == "list":
            parser.add_argument(
                "--type", required=True, help="实体类型(epic/story/task/label/template)"
            )
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
            parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")

        elif subcommand == "show":
            parser.add_argument(
                "--type", required=True, help="实体类型(epic/story/task/label/template)"
            )
            parser.add_argument("--id", required=True, help="实体ID")
            parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")

        elif subcommand == "query":
            parser.add_argument("--type", required=True, help="实体类型")
            parser.add_argument("--id", help="实体ID")
            parser.add_argument("--query", help="查询字符串")
            parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        elif subcommand == "create":
            parser.add_argument("--type", required=True, help="实体类型")
            parser.add_argument("--data", required=True, help="JSON格式的数据")
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        elif subcommand == "update":
            parser.add_argument("--type", required=True, help="实体类型")
            parser.add_argument("--id", required=True, help="实体ID")
            parser.add_argument("--data", required=True, help="JSON格式的数据")
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        elif subcommand == "delete":
            parser.add_argument("--type", required=True, help="实体类型")
            parser.add_argument("--id", required=True, help="实体ID")
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
            parser.add_argument("--force", action="store_true", help="强制删除，不提示确认")

        elif subcommand == "backup":
            parser.add_argument("--output", help="备份文件输出路径")
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        elif subcommand == "restore":
            parser.add_argument("backup_file", help="备份文件路径")
            parser.add_argument("--force", action="store_true", help="强制恢复，不提示确认")
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        else:
            raise ValueError(f"未知子命令: {subcommand}")

        # 解析子命令参数
        subcommand_args = parser.parse_args(args)
        parsed.update(vars(subcommand_args))

        return parsed

    def execute(self, args) -> int:
        """执行命令"""
        # 处理参数
        parsed_args = {}
        if isinstance(args, list):
            # 如果是列表参数，首先解析成字典
            if not args or "--help" in args or "-h" in args:
                print(self.get_help())
                return 0
            try:
                parsed_args = self.parse_args(args)
                if parsed_args.get("show_help", False):
                    print(self.get_help())
                    return 0
            except ValueError as e:
                logger.error(str(e))
                print(f"错误: {str(e)}")
                print(self.get_help())
                return 1
        elif isinstance(args, dict):
            # 如果已经是字典，直接使用
            parsed_args = args
            # 处理帮助标识
            if not parsed_args or parsed_args.get("show_help", False):
                print(self.get_help())
                return 0
        else:
            # 不支持其他类型参数
            logger.error("不支持的参数类型")
            print("错误: 不支持的参数类型")
            return 1

        # 获取子命令
        subcommand = parsed_args.get("subcommand")

        # 确保数据库服务已初始化
        self._init_services()

        # 执行对应的子命令
        try:
            if subcommand in self._handlers:
                # 将数据库服务传递给处理器
                handler = self._handlers[subcommand]
                handler.db_service = self.db_service
                return handler.handle(parsed_args)
            else:
                logger.error(f"未知子命令: {subcommand}")
                print(f"错误: 未知子命令: {subcommand}")
                print(self.get_help())
                return 1
        except Exception as e:
            logger.exception(f"执行数据库命令时出错: {str(e)}")
            print(f"错误: {str(e)}")
            return 1
