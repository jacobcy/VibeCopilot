"""
路线图GitHub同步处理器模块

提供路线图与GitHub项目的同步处理逻辑。
"""

from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


class RoadmapSyncHandlers:
    """路线图GitHub同步处理器"""

    VALID_OPERATIONS = ["push", "pull"]

    @staticmethod
    def handle_sync_command(args: Dict[str, Any], service) -> Dict[str, Any]:
        """处理同步命令

        Args:
            args: 命令参数
            service: 路线图服务实例

        Returns:
            Dict[str, Any]: 处理结果
        """
        source = args["repository"]
        operation = args.get("operation", "pull")
        roadmap_id = args.get("roadmap")
        force = args.get("force", False)
        verbose = args.get("verbose", False)
        theme = args.get("theme")

        # 验证参数
        if operation and operation not in RoadmapSyncHandlers.VALID_OPERATIONS:
            return {"status": "error", "summary": f"无效的操作类型: {operation}，有效值为: {', '.join(RoadmapSyncHandlers.VALID_OPERATIONS)}"}

        # 处理GitHub同步
        if source.startswith("github:"):
            repo_path = source[7:]  # 移除 "github:" 前缀
            if operation == "push":
                return RoadmapSyncHandlers.handle_github_push(repo_path, roadmap_id, force, theme, service)
            else:  # pull 或未指定
                return RoadmapSyncHandlers.handle_github_pull(repo_path, roadmap_id, force, theme, service)

        # 处理YAML文件同步
        return RoadmapSyncHandlers.handle_yaml_sync(source, roadmap_id, force, service)

    @staticmethod
    def handle_github_sync(repo_name: str, branch: str, theme: str, service) -> Dict[str, Any]:
        """处理GitHub同步（向后兼容）"""
        return RoadmapSyncHandlers.handle_github_pull(repo_name, None, False, theme, service)

    @staticmethod
    def handle_github_pull(repo_name: str, roadmap_id: Optional[str], force: bool, theme: Optional[str], service) -> Dict[str, Any]:
        """处理从GitHub拉取更新"""
        try:
            from src.roadmap.service.roadmap_operations import sync_from_github

            result = sync_from_github(service, repo_name, roadmap_id=roadmap_id, force=force, theme=theme)
            if result.get("success", False):
                return {"status": "success", "summary": f"成功从GitHub仓库拉取更新: {repo_name}", "details": result}
            else:
                return {"status": "error", "summary": f"从GitHub拉取失败: {result.get('error', '未知错误')}", "details": result}
        except Exception as e:
            return {"status": "error", "summary": f"GitHub拉取过程出错: {str(e)}", "details": {"error": str(e)}}

    @staticmethod
    def handle_github_push(repo_name: str, roadmap_id: Optional[str], force: bool, theme: Optional[str], service) -> Dict[str, Any]:
        """处理推送更新到GitHub"""
        try:
            from src.roadmap.service.roadmap_operations import sync_to_github

            result = sync_to_github(service, repo_name, roadmap_id=roadmap_id, force=force, theme=theme)
            if result.get("success", False):
                return {"status": "success", "summary": f"成功推送更新到GitHub仓库: {repo_name}", "details": result}
            else:
                return {"status": "error", "summary": f"推送到GitHub失败: {result.get('error', '未知错误')}", "details": result}
        except Exception as e:
            return {"status": "error", "summary": f"GitHub推送过程出错: {str(e)}", "details": {"error": str(e)}}

    @staticmethod
    def handle_yaml_sync(file_path: str, roadmap_id: Optional[str], force: bool, service) -> Dict[str, Any]:
        """处理YAML文件同步"""
        try:
            result = service.sync_from_yaml(file_path, roadmap_id=roadmap_id, force=force)
            if result.get("success", False):
                return {"status": "success", "summary": f"成功从YAML文件同步: {file_path}", "details": result}
            else:
                return {"status": "error", "summary": f"YAML同步失败: {result.get('error', '未知错误')}", "details": result}
        except Exception as e:
            return {"status": "error", "summary": f"YAML同步过程出错: {str(e)}", "details": {"error": str(e)}}
