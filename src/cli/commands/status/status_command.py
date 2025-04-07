"""
状态命令模块

提供查询和管理系统状态的命令实现
"""

import argparse
import json
import logging
from typing import Any, Dict, List, Optional

from src.cli.command import Command
from src.status import StatusService

logger = logging.getLogger(__name__)


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
            parser.add_argument(
                "--type", choices=["all", "summary", "critical"], default="summary", help="状态类型"
            )
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
        """处理show子命令"""
        status_type = args.get("type", "summary")
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")

        try:
            if status_type == "all":
                result = service.get_system_status(detailed=True)
            elif status_type == "critical":
                result = service.get_critical_status()
            else:  # summary
                result = service.get_system_status(detailed=False)

            self._output_result(result, output_format, "system", verbose)
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

        try:
            result = service.get_domain_status("task")
            self._output_result(result, output_format, "domain", verbose)
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

    def _output_result(
        self, result: Any, output_format: str, result_type: str, verbose: bool = False
    ) -> None:
        """格式化输出结果"""
        if output_format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return

        # 文本格式输出
        if result_type == "system":
            self._format_system_status(result, verbose)
        elif result_type == "domain":
            self._format_domain_status(result, verbose)
        elif result_type == "entity":
            self._format_entity_status(result, verbose)

    def _format_system_status(self, result: Dict, verbose: bool = False) -> None:
        """格式化系统状态输出"""
        print("\n=== 系统状态 ===")

        # 基本信息
        system_info = result.get("system_info", {})
        if system_info:
            print("\n系统信息:")
            self._print_dict(system_info, indent=2)

        # 核心状态
        critical = result.get("critical", [])
        if critical:
            print("\n需要注意的事项:")
            for item in critical:
                print(f"  ⚠️ {item.get('message')}")

        # 各领域状态
        domains = result.get("domains", [])
        print(f"\n可用领域: {len(domains)}")

        domain_status = result.get("status", {})
        for domain, status in domain_status.items():
            domain_icon = "✅" if status.get("health", 100) >= 80 else "⚠️"
            print(f"\n--- {domain_icon} {domain} 状态 ---")

            health = status.get("health", 0)
            print(f"  健康度: {health}%")

            if not verbose:
                # 简要状态
                print(f"  当前阶段: {status.get('current_phase', '未知')}")
                print(f"  活动项目: {status.get('active_items', 0)}")
            else:
                # 详细状态
                self._print_dict(status, indent=2)

    def _format_domain_status(self, result: Dict, verbose: bool = False) -> None:
        """格式化领域状态输出"""
        if "error" in result:
            self._error(result["error"])
            return

        domain = result.get("domain", "未知领域")
        health = result.get("health", 0)
        health_icon = "✅" if health >= 80 else "⚠️" if health >= 50 else "❌"

        print(f"\n=== {domain} 状态 {health_icon} ===")
        print(f"健康度: {health}%")

        # 当前状态
        current_phase = result.get("current_phase")
        if current_phase:
            print(f"当前阶段: {current_phase}")

        # 活动项目
        active_items = result.get("active_items", [])
        if active_items:
            print(f"\n活动项目 ({len(active_items)}):")
            for item in active_items:
                print(f"  - {item.get('id')}: {item.get('name')} ({item.get('status')})")

        # 详细信息
        if verbose:
            details = result.get("details", {})
            if details:
                print("\n详细信息:")
                self._print_dict(details, indent=2)

        # 建议操作
        suggestions = result.get("suggestions", [])
        if suggestions:
            print("\n建议操作:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")

    def _format_entity_status(self, result: Dict, verbose: bool = False) -> None:
        """格式化实体状态输出"""
        if "error" in result:
            self._error(result["error"])
            return

        entity_id = result.get("id", "未知ID")
        name = result.get("name") or result.get("title") or "未命名"
        status = result.get("status", "未知状态")

        status_icon = (
            "✅"
            if status in ["COMPLETED", "SUCCESS"]
            else "⚠️"
            if status in ["IN_PROGRESS", "PENDING"]
            else "❌"
        )
        print(f"\n=== {entity_id} - {name} {status_icon} ===")
        print(f"状态: {status}")

        # 详细信息
        if verbose:
            # 移除基本信息字段再打印
            result_copy = result.copy()
            for field in ["id", "name", "title", "status"]:
                if field in result_copy:
                    result_copy.pop(field, None)

            if result_copy:
                print("\n详细信息:")
                self._print_dict(result_copy, indent=2)

    def _print_dict(self, data: Dict, indent: int = 0, verbose: bool = False) -> None:
        """打印字典内容"""
        for key, value in data.items():
            if isinstance(value, dict):
                print(" " * indent + f"{key}:")
                self._print_dict(value, indent + 2, verbose)
            elif isinstance(value, list):
                print(" " * indent + f"{key}: [{len(value)} 项]")
                if value and not isinstance(value[0], dict):
                    print(" " * (indent + 2) + ", ".join(str(v) for v in value))
                elif verbose and value:
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            print(" " * (indent + 2) + f"项目 {i+1}:")
                            self._print_dict(item, indent + 4, verbose)
                        else:
                            print(" " * (indent + 2) + f"项目 {i+1}: {item}")
            else:
                print(" " * indent + f"{key}: {value}")

    def _error(self, message: str) -> None:
        """打印错误信息"""
        print(f"错误: {message}")
