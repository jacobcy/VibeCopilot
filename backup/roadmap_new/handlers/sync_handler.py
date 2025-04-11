"""
路线图同步命令处理程序

处理从GitHub同步路线图数据的命令逻辑。
"""

from typing import Any, Dict


def handle_sync_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图同步命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    repository = args.get("repository")
    theme = args.get("theme")
    branch = args.get("branch", "main")
    verbose = args.get("verbose", False)

    if not repository:
        return {"status": "error", "message": "必须提供GitHub仓库，格式: 所有者/仓库名", "summary": "同步失败: 缺少仓库信息"}

    # 调用服务执行同步
    try:
        sync_result = service.sync_from_github(repository, theme, branch)

        if sync_result.get("success", False):
            return {"status": "success", "message": f"成功从 {repository} 同步路线图数据", "summary": f"已从 {repository} 成功同步路线图数据", "data": sync_result}
        else:
            return {"status": "error", "message": sync_result.get("error", "同步过程中发生未知错误"), "summary": "同步失败", "data": sync_result}

    except Exception as e:
        return {"status": "error", "message": f"同步过程中发生异常: {str(e)}", "summary": "同步过程中发生异常", "data": {"error": str(e)}}
