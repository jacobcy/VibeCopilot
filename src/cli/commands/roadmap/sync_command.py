"""
路线图同步命令模块

提供在本地数据库和GitHub之间同步路线图数据的命令实现
"""

from typing import Dict, List

from src.cli.command import Command
from src.roadmap import RoadmapService


class SyncCommand(Command):
    """路线图同步命令"""

    @classmethod
    def get_command(cls) -> str:
        return "sync"

    @classmethod
    def get_description(cls) -> str:
        return "同步路线图数据"

    @classmethod
    def get_help(cls) -> str:
        return """
        同步路线图数据

        用法:
            sync github push          将路线图数据推送到GitHub
            sync github pull          从GitHub拉取路线图数据
            sync yaml export          将路线图导出为YAML文件
            sync yaml import <文件>    从YAML文件导入路线图

        参数:
            github                    GitHub相关操作
            yaml                      YAML文件相关操作

        操作:
            push                      推送数据
            pull                      拉取数据
            export                    导出数据
            import <文件>              导入数据

        选项:
            --roadmap <id>            指定路线图ID，不提供则使用当前活跃路线图
        """

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        if not args:
            return parsed

        # 解析同步目标（github或yaml）
        sync_target = args.pop(0)
        if sync_target in ["github", "yaml"]:
            parsed["target"] = sync_target
        else:
            raise ValueError(f"未知的同步目标: {sync_target}")

        # 如果没有更多参数，返回
        if not args:
            return parsed

        # 解析操作类型
        operation = args.pop(0)
        if sync_target == "github" and operation in ["push", "pull"]:
            parsed["operation"] = operation
        elif sync_target == "yaml" and operation in ["export", "import"]:
            parsed["operation"] = operation
            # 如果是import操作，还需要文件路径
            if operation == "import":
                if args:
                    parsed["file_path"] = args.pop(0)
                else:
                    raise ValueError("导入操作需要提供YAML文件路径")
        else:
            valid_ops = "push, pull" if sync_target == "github" else "export, import"
            raise ValueError(f"无效的操作: {operation}，对于{sync_target}，有效操作为: {valid_ops}")

        # 解析选项
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--roadmap":
                if i + 1 < len(args):
                    parsed["roadmap_id"] = args[i + 1]
                    i += 2
                else:
                    raise ValueError("--roadmap选项需要提供路线图ID")
            else:
                i += 1

        return parsed

    def execute(self, parsed_args: Dict) -> None:
        """执行命令"""
        service = RoadmapService()

        # 如果没有指定目标，显示帮助信息
        if "target" not in parsed_args:
            print(self.get_help())
            return

        target = parsed_args.get("target")
        operation = parsed_args.get("operation")
        roadmap_id = parsed_args.get("roadmap_id")

        try:
            if target == "github":
                if operation == "push":
                    # 推送到GitHub
                    result = service.sync_to_github(roadmap_id)
                    if result.get("success", False):
                        print(f"已成功将路线图数据推送到GitHub")
                    else:
                        print(f"推送到GitHub失败: {result.get('error', '未知错误')}")

                elif operation == "pull":
                    # 从GitHub拉取
                    result = service.sync_from_github(roadmap_id)
                    if result.get("success", False):
                        print(f"已成功从GitHub拉取路线图数据")
                    else:
                        print(f"从GitHub拉取失败: {result.get('error', '未知错误')}")

                else:
                    print(f"未指定操作，可用操作: push, pull")

            elif target == "yaml":
                if operation == "export":
                    # 导出到YAML
                    result = service.export_to_yaml(roadmap_id)
                    if result.get("success", False):
                        print(f"已成功将路线图数据导出到: {result.get('file_path')}")
                    else:
                        print(f"导出到YAML失败: {result.get('error', '未知错误')}")

                elif operation == "import":
                    # 从YAML导入
                    file_path = parsed_args.get("file_path")
                    if not file_path:
                        print("导入操作需要提供YAML文件路径")
                        return

                    result = service.import_from_yaml(file_path, roadmap_id)
                    if result.get("success", False):
                        print(f"已成功从 {file_path} 导入路线图数据")
                    else:
                        print(f"从YAML导入失败: {result.get('error', '未知错误')}")

                else:
                    print(f"未指定操作，可用操作: export, import")

            else:
                print(f"未知的同步目标: {target}")

        except Exception as e:
            print(f"错误: {str(e)}")
