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
        return "查询和管理系统状态"

    @classmethod
    def get_help(cls) -> str:
        return """
        查询和管理系统状态

        用法:
            status                     查看系统整体状态
            status <domain>            查看特定领域的状态
            status <domain> <id>       查看特定实体的状态
            status <domain> <id> <new_status> 更新特定实体的状态

        参数:
            domain                     领域名称，如 'roadmap', 'workflow'
            id                         实体ID
            new_status                 新状态

        选项:
            --format json              以JSON格式输出
            --list                     列出实体
            --status <status>          筛选特定状态
        """

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parser = argparse.ArgumentParser(prog="status", add_help=False)
        parser.add_argument("domain", nargs="?", help="领域名称")
        parser.add_argument("entity_id", nargs="?", help="实体ID")
        parser.add_argument("new_status", nargs="?", help="新状态")
        parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
        parser.add_argument("--list", action="store_true", help="列出实体")
        parser.add_argument("--status", help="筛选特定状态")

        return vars(parser.parse_args(args))

    def execute(self, parsed_args: Dict) -> None:
        """执行命令"""
        service = StatusService.get_instance()

        domain = parsed_args.get("domain")
        entity_id = parsed_args.get("entity_id")
        new_status = parsed_args.get("new_status")
        output_format = parsed_args.get("format", "text")
        list_entities = parsed_args.get("list", False)
        status_filter = parsed_args.get("status")

        try:
            result = None

            # 列出实体
            if list_entities:
                if not domain:
                    self._error("缺少领域名称")
                    return
                result = service.list_entities(domain, status_filter)
                self._output_result(result, output_format, "entities")
                return

            # 更新状态
            if new_status and domain and entity_id:
                result = service.update_status(domain, entity_id, new_status)
                self._output_result(result, output_format, "update")
                return

            # 查询特定实体状态
            if domain and entity_id:
                result = service.get_domain_status(domain, entity_id)
                self._output_result(result, output_format, "entity")
                return

            # 查询特定领域状态
            if domain:
                result = service.get_domain_status(domain)
                self._output_result(result, output_format, "domain")
                return

            # 查询系统整体状态
            result = service.get_system_status()
            self._output_result(result, output_format, "system")

        except Exception as e:
            logger.error(f"执行状态命令时出错: {e}")
            self._error(f"错误: {str(e)}")

    def _output_result(self, result: Any, output_format: str, result_type: str) -> None:
        """格式化输出结果"""
        if output_format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return

        # 文本格式输出
        if result_type == "system":
            self._format_system_status(result)
        elif result_type == "domain":
            self._format_domain_status(result)
        elif result_type == "entity":
            self._format_entity_status(result)
        elif result_type == "update":
            self._format_update_result(result)
        elif result_type == "entities":
            self._format_entities_list(result)

    def _format_system_status(self, result: Dict) -> None:
        """格式化系统状态输出"""
        print("\n=== 系统状态 ===")

        domains = result.get("domains", [])
        print(f"领域数量: {len(domains)}")
        print(f"可用领域: {', '.join(domains)}")

        status = result.get("status", {})
        for domain, domain_status in status.items():
            print(f"\n--- {domain} 状态 ---")
            self._print_dict(domain_status, indent=2)

    def _format_domain_status(self, result: Dict) -> None:
        """格式化领域状态输出"""
        if "error" in result:
            self._error(result["error"])
            return

        domain = result.get("domain", "未知领域")
        print(f"\n=== {domain} 状态 ===")

        # 移除domain字段再打印
        result_copy = result.copy()
        if "domain" in result_copy:
            del result_copy["domain"]

        self._print_dict(result_copy)

    def _format_entity_status(self, result: Dict) -> None:
        """格式化实体状态输出"""
        if "error" in result:
            self._error(result["error"])
            return

        entity_id = result.get("id", "未知ID")
        name = result.get("name") or result.get("title") or "未命名"

        print(f"\n=== {entity_id} - {name} ===")

        # 移除id和name字段再打印
        result_copy = result.copy()
        for field in ["id", "name", "title"]:
            if field in result_copy:
                del result_copy[field]

        self._print_dict(result_copy)

    def _format_update_result(self, result: Dict) -> None:
        """格式化更新结果输出"""
        if "error" in result:
            self._error(result["error"])
            return

        if result.get("updated", False):
            print("✅ 状态更新成功")
        else:
            print("❌ 状态更新失败")

        self._print_dict(result)

    def _format_entities_list(self, entities: List[Dict]) -> None:
        """格式化实体列表输出"""
        if not entities:
            print("没有找到实体")
            return

        print(f"\n=== 找到 {len(entities)} 个实体 ===")

        for entity in entities:
            entity_id = entity.get("id", "未知ID")
            name = entity.get("name") or entity.get("title") or "未命名"
            status = entity.get("status", "未知状态")

            print(f"- {entity_id}: {name} ({status})")

    def _print_dict(self, data: Dict, indent: int = 0) -> None:
        """打印字典内容"""
        for key, value in data.items():
            if isinstance(value, dict):
                print(" " * indent + f"{key}:")
                self._print_dict(value, indent + 2)
            elif isinstance(value, list):
                print(" " * indent + f"{key}: [{len(value)} 项]")
                if value and not isinstance(value[0], dict):
                    print(" " * (indent + 2) + ", ".join(str(v) for v in value))
            else:
                print(" " * indent + f"{key}: {value}")

    def _error(self, message: str) -> None:
        """打印错误信息"""
        print(f"错误: {message}")
