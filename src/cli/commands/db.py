"""
数据库命令处理模块

提供数据库管理操作的命令接口，集成数据库服务功能。
"""

import json
import logging
import os
from typing import Any, Dict, List

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.db.service import DatabaseService

logger = logging.getLogger(__name__)


class DatabaseCommand(BaseCommand, Command):
    """数据库命令处理器"""

    def __init__(self):
        """初始化数据库命令"""
        super().__init__(name="db", description="管理数据库")

        # 注册参数
        self.register_args(
            required=["action"],
            optional={
                "type": None,  # 操作的实体类型(epic/story/task/label/template)
                "id": None,  # 实体ID
                "data": None,  # JSON格式的数据
                "format": "text",  # 输出格式(text/json)
                "query": None,  # 查询字符串
                "tags": None,  # 标签列表，逗号分隔
            },
        )

        # 初始化服务实例
        self.db_service = None

    def _init_services(self) -> None:
        """初始化数据库服务"""
        if not self.db_service:
            self.db_service = DatabaseService()

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据库命令

        Args:
            args: 命令参数
                - action: 要执行的操作(init/query/create/update/delete)
                - type: 实体类型(可选)
                - id: 实体ID(可选)
                - data: JSON格式的数据(可选)
                - format: 输出格式(可选)
                - query: 查询字符串(可选)
                - tags: 标签列表，逗号分隔(可选)

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 初始化服务
        self._init_services()

        # 获取参数
        action = args["action"]

        # 根据操作类型执行不同逻辑
        if action == "init":
            return self._handle_init(args)
        elif action == "query":
            return self._handle_query(args)
        elif action == "create":
            return self._handle_create(args)
        elif action == "update":
            return self._handle_update(args)
        elif action == "delete":
            return self._handle_delete(args)
        else:
            return {"success": False, "error": f"未知操作: {action}"}

    def _handle_init(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化操作"""
        logger.info("初始化数据库")

        try:
            # 数据库已通过服务初始化
            self._init_services()

            # 仅初始化
            return {
                "success": True,
                "message": "已初始化数据库",
            }
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            return {"success": False, "error": f"初始化数据库失败: {e}"}

    def _handle_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理查询操作"""
        entity_type = args.get("type")
        entity_id = args.get("id")
        query = args.get("query")
        tags_str = args.get("tags")

        # 处理标签
        tags = None
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(",")]

        if not entity_type:
            return {
                "success": False,
                "error": "请指定查询类型(--type=epic/story/task/label/template)",
            }

        try:
            # 特殊处理模板查询
            if entity_type == "template" and query:
                data = self.db_service.search_templates(query=query, tags=tags)
                return {
                    "success": True,
                    "message": f"已查询模板列表",
                    "count": len(data),
                    "data": data,
                }

            if entity_id:
                # 查询单个实体
                if entity_type == "epic":
                    data = self.db_service.get_epic(entity_id)
                elif entity_type == "story":
                    data = self.db_service.get_story(entity_id)
                elif entity_type == "task":
                    data = self.db_service.get_task(entity_id)
                elif entity_type == "label":
                    data = self.db_service.get_label(entity_id)
                elif entity_type == "template":
                    data = self.db_service.get_template(entity_id)
                else:
                    return {"success": False, "error": f"未知实体类型: {entity_type}"}

                if not data:
                    return {"success": False, "error": f"未找到{entity_type}: {entity_id}"}

                return {
                    "success": True,
                    "message": f"已查询{entity_type}: {entity_id}",
                    "data": data,
                }
            else:
                # 查询列表
                if entity_type == "epic":
                    data = self.db_service.list_epics()
                elif entity_type == "story":
                    data = self.db_service.list_stories()
                elif entity_type == "task":
                    data = self.db_service.list_tasks()
                elif entity_type == "label":
                    data = self.db_service.list_labels()
                elif entity_type == "template":
                    data = self.db_service.list_templates()
                else:
                    return {"success": False, "error": f"未知实体类型: {entity_type}"}

                return {
                    "success": True,
                    "message": f"已查询{entity_type}列表",
                    "count": len(data),
                    "data": data,
                }
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return {"success": False, "error": f"查询失败: {e}"}

    def _handle_create(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理创建操作"""
        entity_type = args.get("type")
        data_str = args.get("data")

        if not entity_type:
            return {
                "success": False,
                "error": "请指定实体类型(--type=epic/story/task/label/template)",
            }

        if not data_str:
            return {"success": False, "error": "请提供数据(--data='json字符串')"}

        try:
            # 解析JSON数据
            data = json.loads(data_str)

            # 创建实体
            if entity_type == "epic":
                result = self.db_service.create_epic(data)
            elif entity_type == "story":
                result = self.db_service.create_story(data)
            elif entity_type == "task":
                result = self.db_service.create_task(data)
            elif entity_type == "label":
                result = self.db_service.create_label(data)
            elif entity_type == "template":
                result = self.db_service.create_template(data)
            else:
                return {"success": False, "error": f"未知实体类型: {entity_type}"}

            return {"success": True, "message": f"已创建{entity_type}", "data": result}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析失败: {e}"}
        except Exception as e:
            logger.error(f"创建失败: {e}")
            return {"success": False, "error": f"创建失败: {e}"}

    def _handle_update(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理更新操作"""
        entity_type = args.get("type")
        entity_id = args.get("id")
        data_str = args.get("data")

        if not entity_type:
            return {
                "success": False,
                "error": "请指定实体类型(--type=epic/story/task/label/template)",
            }

        if not entity_id:
            return {"success": False, "error": "请指定实体ID(--id=xxx)"}

        if not data_str:
            return {"success": False, "error": "请提供数据(--data='json字符串')"}

        try:
            # 解析JSON数据
            data = json.loads(data_str)

            # 更新实体
            if entity_type == "epic":
                result = self.db_service.update_epic(entity_id, data)
            elif entity_type == "story":
                result = self.db_service.update_story(entity_id, data)
            elif entity_type == "task":
                result = self.db_service.update_task(entity_id, data)
            elif entity_type == "label":
                result = self.db_service.update_label(entity_id, data)
            elif entity_type == "template":
                result = self.db_service.update_template(entity_id, data)
            else:
                return {"success": False, "error": f"未知实体类型: {entity_type}"}

            if not result:
                return {"success": False, "error": f"未找到{entity_type}: {entity_id}"}

            return {
                "success": True,
                "message": f"已更新{entity_type}: {entity_id}",
                "data": result,
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析失败: {e}"}
        except Exception as e:
            logger.error(f"更新失败: {e}")
            return {"success": False, "error": f"更新失败: {e}"}

    def _handle_delete(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理删除操作"""
        entity_type = args.get("type")
        entity_id = args.get("id")

        if not entity_type:
            return {
                "success": False,
                "error": "请指定实体类型(--type=epic/story/task/label/template)",
            }

        if not entity_id:
            return {"success": False, "error": "请指定实体ID(--id=xxx)"}

        try:
            # 删除实体
            if entity_type == "epic":
                result = self.db_service.delete_epic(entity_id)
            elif entity_type == "story":
                result = self.db_service.delete_story(entity_id)
            elif entity_type == "task":
                result = self.db_service.delete_task(entity_id)
            elif entity_type == "label":
                result = self.db_service.delete_label(entity_id)
            elif entity_type == "template":
                result = self.db_service.delete_template(entity_id)
            else:
                return {"success": False, "error": f"未知实体类型: {entity_type}"}

            if not result:
                return {"success": False, "error": f"未找到{entity_type}: {entity_id}"}

            return {"success": True, "message": f"已删除{entity_type}: {entity_id}"}
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return {"success": False, "error": f"删除失败: {e}"}

    # 实现新接口
    @classmethod
    def get_command(cls) -> str:
        return "db"

    @classmethod
    def get_description(cls) -> str:
        return "管理数据库"

    @classmethod
    def get_help(cls) -> str:
        return """
        数据库管理命令

        用法:
            db init                    初始化数据库
            db query --type=epic       查询所有epic
            db query --type=epic --id=123  查询特定epic
            db create --type=task --data='{"name":"测试任务"}'  创建任务
            db update --type=task --id=123 --data='{"status":"completed"}'  更新任务
            db delete --type=task --id=123  删除任务

        参数:
            action                     要执行的操作(init/query/create/update/delete)

        选项:
            --type <type>              实体类型(epic/story/task/label/template)
            --id <id>                  实体ID
            --data <json>              JSON格式的数据
            --format <format>          输出格式(text/json)
            --query <query>            查询字符串
            --tags <tags>              标签列表，逗号分隔
        """

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        if not args:
            return parsed

        # 处理action参数
        parsed["action"] = args.pop(0)

        # 处理选项
        i = 0
        while i < len(args):
            arg = args[i]

            if arg.startswith("--"):
                option = arg[2:]  # 去掉--前缀

                if "=" in option:
                    # 处理--option=value形式
                    option_name, option_value = option.split("=", 1)
                    parsed[option_name] = option_value
                    i += 1
                elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                    # 处理--option value形式
                    parsed[option] = args[i + 1]
                    i += 2
                else:
                    # 处理--option形式（布尔选项）
                    parsed[option] = True
                    i += 1
            else:
                # 跳过未识别的参数
                i += 1

        return parsed

    def execute(self, parsed_args: Dict) -> None:
        """执行命令 - 适配新接口"""
        result = super().execute(parsed_args)

        # 如果是字典结果，格式化输出
        if isinstance(result, dict):
            if result.get("success", False):
                # 成功结果
                if "message" in result:
                    print(result["message"])

                # 输出数据
                if "data" in result:
                    data = result["data"]
                    output_format = parsed_args.get("format", "text")

                    if output_format == "json":
                        # JSON格式输出
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    else:
                        # 文本格式输出
                        if isinstance(data, list):
                            for item in data:
                                print(json.dumps(item, ensure_ascii=False))
                        else:
                            print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                # 错误结果
                print(f"错误: {result.get('error', '未知错误')}")

                # 如果有帮助信息，显示
                if "help" in result:
                    print(result["help"])


# 命令实例
command = DatabaseCommand()
