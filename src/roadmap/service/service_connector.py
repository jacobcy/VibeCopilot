"""
路线图服务连接器模块

解决RoadmapService和StatusService之间的循环依赖问题
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 全局变量，避免循环导入
_roadmap_service = None
_status_service = None


def set_roadmap_service(service):
    """设置全局RoadmapService实例"""
    global _roadmap_service
    _roadmap_service = service
    logger.debug("RoadmapService实例已注册到连接器")
    # 尝试连接
    connect_services()


def set_status_service(service):
    """设置全局StatusService实例"""
    global _status_service
    _status_service = service
    logger.debug("StatusService实例已注册到连接器")
    # 尝试连接
    connect_services()


def get_roadmap_service():
    """获取全局RoadmapService实例"""
    global _roadmap_service
    return _roadmap_service


def get_status_service():
    """获取全局StatusService实例"""
    global _status_service
    return _status_service


def connect_services():
    """连接RoadmapService和StatusService

    当两个服务都已注册时，建立它们之间的连接
    """
    global _roadmap_service, _status_service

    if not _roadmap_service or not _status_service:
        return  # 两个服务都需要注册才能连接

    try:
        # 获取RoadmapStatusProvider
        roadmap_provider = _status_service.provider_manager.get_provider("roadmap")

        if roadmap_provider:
            # 建立双向连接
            roadmap_provider.set_service(_roadmap_service)
            logger.info("成功连接RoadmapService和RoadmapStatusProvider")

            # 确保RoadmapService中的status_provider也是正确的
            _roadmap_service.status_provider = roadmap_provider
            logger.info("已在RoadmapService中设置正确的status_provider")
        else:
            logger.error("未找到roadmap提供者，无法连接RoadmapService")
    except Exception as e:
        logger.error(f"连接RoadmapService和StatusService时出错: {e}", exc_info=True)


def force_connect():
    """强制尝试连接服务，无论服务是否已注册

    在服务初始化后主动调用此方法，可以解决某些情况下连接不成功的问题
    """
    global _roadmap_service, _status_service

    # 如果任一服务未注册，尝试延迟导入
    if not _roadmap_service:
        try:
            # 尝试导入RoadmapService
            from src.roadmap.service.roadmap_service import RoadmapService

            # 获取实例（假设它使用单例模式）
            _roadmap_service = RoadmapService()
            logger.info("强制连接: 已创建并注册RoadmapService实例")
        except Exception as e:
            logger.error(f"强制连接: 无法创建RoadmapService实例: {e}")

    if not _status_service:
        try:
            # 尝试导入StatusService
            from src.status.service import StatusService

            # 获取实例
            _status_service = StatusService.get_instance()
            logger.info("强制连接: 已获取并注册StatusService实例")
        except Exception as e:
            logger.error(f"强制连接: 无法获取StatusService实例: {e}")

    # 尝试连接
    if _roadmap_service and _status_service:
        try:
            connect_services()
            logger.info("强制连接成功")
            return True
        except Exception as e:
            logger.error(f"强制连接失败: {e}")
            return False
    else:
        return False


def force_connect_services():
    """强制尝试连接服务，并尝试确保GitHub信息正确传递

    更完善的服务连接修复函数，尝试解决"状态服务未返回有效的GitHub信息"警告
    """
    global _roadmap_service, _status_service

    # 首先尝试普通的force_connect
    success = force_connect()
    if not success:
        logger.warning("常规force_connect失败，尝试更深入的修复")

    # 确保我们有一个RoadmapService实例
    if not _roadmap_service:
        try:
            from src.roadmap.service.roadmap_service import RoadmapService

            _roadmap_service = RoadmapService()
            logger.info("已创建新的RoadmapService实例")
        except Exception as e:
            logger.error(f"创建RoadmapService实例失败: {e}")
            return False

    # 确保我们有一个StatusService实例
    if not _status_service:
        try:
            from src.status.service import StatusService

            _status_service = StatusService.get_instance()
            logger.info("已获取StatusService实例")
        except Exception as e:
            logger.error(f"获取StatusService实例失败: {e}")
            return False

    # 确保我们有一个正确配置的GitHub信息提供者
    try:
        from src.status.providers.github_info_provider import GitHubInfoProvider

        github_provider = _status_service.provider_manager.get_provider("github_info")
        if not github_provider:
            github_provider = GitHubInfoProvider()
            _status_service.provider_manager.register_provider(github_provider)
            logger.info("已创建并注册新的GitHub信息提供者")

        # 获取GitHub信息状态
        github_info = github_provider.get_status()
        logger.info(f"GitHub信息状态: {github_info}")

        # 检查是否有有效的GitHub配置
        if not github_info.get("effective_owner") or not github_info.get("effective_repo"):
            logger.error("GitHub配置不完整，无法连接服务")
            return False

        # 获取Roadmap提供者
        roadmap_provider = _status_service.provider_manager.get_provider("roadmap")
        if roadmap_provider:
            # 重新建立双向连接
            roadmap_provider.set_service(_roadmap_service)
            _roadmap_service.status_provider = roadmap_provider
            logger.info("已重新建立RoadmapService和RoadmapStatusProvider之间的连接")
        else:
            logger.error("未找到RoadmapStatusProvider")
            return False

        # 尝试主动将GitHub信息添加到路线图
        try:
            roadmap_id = _roadmap_service.active_roadmap_id
            if roadmap_id:
                logger.info(f"尝试更新路线图 {roadmap_id} 的GitHub信息")
                roadmap = _roadmap_service.roadmap_repo.get_roadmap(roadmap_id)
                if roadmap:
                    # 获取有效的GitHub配置
                    owner = github_info.get("effective_owner")
                    repo = github_info.get("effective_repo")
                    project_id = github_info.get("effective_project_id")
                    roadmap_title = github_info.get("roadmap_title", "VibeCopilot Project")

                    # 添加GitHub链接到路线图
                    github_link_data = {
                        "owner": owner,
                        "repo": repo,
                        "project_id": project_id,
                        "roadmap_title": roadmap_title,
                        "url": f"https://github.com/{owner}/{repo}/projects/{project_id}",
                    }

                    # 更新路线图
                    roadmap["github_link"] = github_link_data
                    _roadmap_service.roadmap_repo.update_roadmap(roadmap_id, roadmap)
                    logger.info(f"已成功更新路线图 {roadmap_id} 的GitHub信息")
            else:
                logger.warning("无法获取活动路线图ID")
        except Exception as e:
            logger.error(f"尝试更新路线图的GitHub信息时出错: {e}")

        return True
    except Exception as e:
        logger.error(f"force_connect_services失败: {e}")
        return False
