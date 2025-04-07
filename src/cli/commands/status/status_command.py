"""
状态命令模块

提供查询和管理系统状态的命令实现
"""

import argparse
import json
import logging
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from src.cli.command import Command
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository
from src.status import StatusService

logger = logging.getLogger(__name__)
console = Console()


class StatusCommand(Command):
    """状态命令"""

    @classmethod
    def get_command(cls) -> str:
        return "status"

    @classmethod
    def get_description(cls) -> str:
        return "项目状态管理命令"

    @classmethod
    def get_help(cls) -> str:
        return """
项目状态管理命令

用法:
    status show [--type=<status_type>] [--verbose]     显示项目状态概览
    status flow [--verbose]                           显示流程状态
    status roadmap [--verbose]                        显示路线图状态
    status task [--verbose]                           显示任务状态
    status update --phase=<phase>                    更新项目阶段
    status init [--name=<project_name>]              初始化项目状态

选项:
    --type=<status_type>    状态类型 (all, summary, critical)
    --verbose               显示详细信息
    --format=<format>       输出格式 (json或text)
    --phase=<phase>         项目阶段
    --name=<project_name>   项目名称
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
        parser = argparse.ArgumentParser(prog=f"status {subcommand}", add_help=False)

        if subcommand == "show":
            parser.add_argument("--type", choices=["all", "summary", "critical"], default="summary", help="状态类型")
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
            parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")

        elif subcommand in ["flow", "roadmap", "task"]:
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
            parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")

        elif subcommand == "update":
            parser.add_argument("--phase", required=True, help="项目阶段")
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
            parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")

        elif subcommand == "init":
            parser.add_argument("--name", help="项目名称")
            parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
            parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")

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

        # 获取子命令和参数
        subcommand = parsed_args.get("subcommand")

        # 执行对应的子命令
        try:
            service = StatusService.get_instance()

            if subcommand == "show":
                return self._handle_show(service, parsed_args)
            elif subcommand == "flow":
                return self._handle_flow(service, parsed_args)
            elif subcommand == "roadmap":
                return self._handle_roadmap(service, parsed_args)
            elif subcommand == "task":
                return self._handle_task(service, parsed_args)
            elif subcommand == "update":
                return self._handle_update(service, parsed_args)
            elif subcommand == "init":
                return self._handle_init(service, parsed_args)
            else:
                logger.error(f"未知子命令: {subcommand}")
                print(f"错误: 未知子命令: {subcommand}")
                print(self.get_help())
                return 1
        except Exception as e:
            logger.exception(f"执行状态命令时出错: {str(e)}")
            print(f"错误: {str(e)}")
            return 1

    def _handle_show(self, service: StatusService, args: Dict) -> int:
        """处理show子命令 (集成 Task 摘要)"""
        status_type = args.get("type", "summary")
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")

        try:
            # Get base system status
            if status_type == "all":
                result = service.get_system_status(detailed=True)
            elif status_type == "critical":
                result = service.get_critical_status()
            else:  # summary
                result = service.get_system_status(detailed=False)

            # --- Get and merge Task Summary ---
            try:
                # Assuming get_domain_status('task') returns a dict like {'total': N, 'open': X, ...}
                task_summary = service.get_domain_status("task")
                # Remove potential error key before merging
                task_summary.pop("error", None)
                result["task_summary"] = task_summary
            except Exception as task_e:
                logger.warning(f"获取任务摘要时出错: {task_e}", exc_info=True)
                result["task_summary"] = {"error": f"获取任务摘要失败: {task_e}"}
            # ---------------------------------

            self._output_result(result, output_format, "system_with_tasks", verbose)
            return 0
        except Exception as e:
            logger.error(f"获取系统状态时出错: {str(e)}")
            print(f"错误: {str(e)}")
            return 1

    def _handle_flow(self, service: StatusService, args: Dict) -> int:
        """处理flow子命令"""
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")

        try:
            result = service.get_domain_status("workflow")
            self._output_result(result, output_format, "domain", verbose)
            return 0
        except Exception as e:
            logger.error(f"获取流程状态时出错: {str(e)}")
            print(f"错误: {str(e)}")
            return 1

    def _handle_roadmap(self, service: StatusService, args: Dict) -> int:
        """处理roadmap子命令"""
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")

        try:
            result = service.get_domain_status("roadmap")

            # 检查是否存在错误
            if "error" in result:
                print(f"错误: {result['error']}")

                # 显示错误代码
                if "code" in result:
                    print(f"错误代码: {result['code']}")

                # 显示自定义建议
                if "suggestions" in result and isinstance(result["suggestions"], list):
                    print("\n修复建议:")
                    for suggestion in result["suggestions"]:
                        print(f"  - {suggestion}")
                    return 1
                else:
                    # 使用通用建议
                    print("\n通用建议:")
                    print("  - 检查 roadmap 健康状态并解决问题")
                    print("  - 查看日志获取详细错误信息")
                    return 1

            self._output_result(result, output_format, "domain", verbose)
            return 0
        except Exception as e:
            logger.error(f"获取路线图状态时出错: {str(e)}")
            print(f"错误: {str(e)}")
            return 1

    def _handle_task(self, service: StatusService, args: Dict) -> int:
        """处理task子命令"""
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")
        logger.info("获取任务状态...")
        try:
            result = service.get_domain_status("task")
            if "error" in result:
                logger.error(f"获取任务状态失败: {result['error']}")
                print(f"错误: {result['error']}")
                return 1

            self._output_result(result, output_format, "task", verbose)
            return 0
        except Exception as e:
            logger.error(f"获取任务状态时出错: {str(e)}")
            print(f"错误: {str(e)}")
            return 1

    def _handle_update(self, service: StatusService, args: Dict) -> int:
        """处理update子命令"""
        phase = args.get("phase")
        output_format = args.get("format", "text")

        if not phase:
            logger.error("缺少必要参数: --phase")
            print("错误: 缺少必要参数: --phase")
            return 1

        try:
            result = service.update_project_phase(phase)
            print(f"✅ 已更新项目阶段为: {phase}")

            if output_format == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))

            return 0
        except Exception as e:
            logger.error(f"更新项目阶段时出错: {str(e)}")
            print(f"错误: {str(e)}")
            return 1

    def _handle_init(self, service: StatusService, args: Dict) -> int:
        """处理init子命令"""
        project_name = args.get("name", "VibeCopilot")
        output_format = args.get("format", "text")

        try:
            result = service.initialize_project(project_name)
            print(f"✅ 已初始化项目: {project_name}")

            if output_format == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))

            return 0
        except Exception as e:
            logger.error(f"初始化项目状态时出错: {str(e)}")
            print(f"错误: {str(e)}")
            return 1

    def _output_result(self, result: Dict, output_format: str, context_type: str, verbose: bool):
        """格式化并输出结果 (需要扩展以处理 Task)"""
        if output_format == "json":
            console.print(Syntax(json.dumps(result, indent=2, ensure_ascii=False), "json", theme="default"))
        else:
            # --- Text Output Logic (Needs Refinement) ---
            console.print(f"[bold underline]{context_type.replace('_', ' ').title()} Status:[/bold underline]")

            if context_type == "system_with_tasks":
                # Print general system status parts
                console.print(f"  项目阶段: {result.get('project_phase', 'N/A')}")
                console.print(f"  活动工作流: {result.get('active_workflow', '无')}")
                # ... print other system status fields ...

                # Print Task Summary
                task_summary = result.get("task_summary", {})
                if task_summary.get("error"):
                    console.print(f"  [red]任务摘要错误:[/red] {task_summary['error']}")
                elif task_summary:
                    console.print("  任务概览:")
                    console.print(f"    - 总计: {task_summary.get('total', 0)}")
                    # Print counts for key statuses
                    for status in ["open", "in_progress", "review", "done", "closed"]:
                        if status in task_summary:
                            console.print(f"    - {status.capitalize()}: {task_summary[status]}")
                else:
                    console.print("  任务概览: N/A")

            elif context_type == "task":
                # Detailed Task Status output
                console.print(f"  任务总数: {result.get('total', 0)}")
                if result.get("by_status"):
                    console.print("  按状态分布:")
                    status_table = Table(box=None)
                    status_table.add_column("Status", style="magenta")
                    status_table.add_column("Count", style="dim", justify="right")
                    for status, count in sorted(result["by_status"].items()):
                        status_table.add_row(status, str(count))
                    console.print(status_table)
                # Add other details if verbose

            elif context_type == "domain":  # Existing handler for flow/roadmap
                console.print(f"  领域: {result.get('domain', 'N/A')}")
                console.print(f"  状态: {result.get('status', 'N/A')}")
                if verbose and result.get("details"):
                    console.print("  详情:", json.dumps(result["details"], indent=2, ensure_ascii=False))
            else:
                # Default fallback for unknown context type
                console.print(json.dumps(result, indent=2, ensure_ascii=False))
            # ----------------------------------------------
