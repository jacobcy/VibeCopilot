"""
路线图初始化数据模块

从.ai/roadmap目录加载YAML文件，并导入到数据库作为初始路线图
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

from src.core.config import get_app_dir
from src.roadmap import RoadmapService

logger = logging.getLogger(__name__)


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """加载YAML文件

    Args:
        file_path: YAML文件路径

    Returns:
        Dict[str, Any]: YAML文件内容
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载YAML文件 {file_path} 失败: {e}")
        return {}


def get_roadmap_files() -> List[str]:
    """获取路线图文件列表

    Returns:
        List[str]: 路线图文件路径列表
    """
    roadmap_dir = Path(get_app_dir()) / ".ai" / "roadmap"

    if not roadmap_dir.exists():
        logger.warning(f"路线图目录不存在: {roadmap_dir}")
        return []

    # 获取所有.yaml文件
    yaml_files = list(roadmap_dir.glob("*.yaml"))
    yaml_files.extend(list(roadmap_dir.glob("*.yml")))

    return [str(file) for file in yaml_files]


def _run_async_import(roadmap_service: RoadmapService, file_path: str) -> Dict[str, Any]:
    """在一个事件循环中运行异步导入"""

    async def do_import():
        return await roadmap_service.yaml_sync.import_from_yaml(file_path)

    try:
        return asyncio.run(do_import())
    except RuntimeError as e:
        # 处理嵌套事件循环错误
        if "cannot run event loop while another loop is running" in str(e):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(do_import())
        else:
            raise


def init_roadmaps() -> Dict[str, int]:
    """初始化路线图数据"""
    logger.info("开始初始化路线图数据...")
    success_count = 0
    fail_count = 0

    # 获取路线图文件列表
    roadmap_files = get_roadmap_files()
    if not roadmap_files:
        logger.warning("没有找到路线图文件，跳过路线图初始化")
        return {"success": success_count, "failed": fail_count}

    # 创建路线图服务
    try:
        roadmap_service = RoadmapService()

        # 导入每个路线图文件
        for file_path in roadmap_files:
            logger.info(f"正在导入路线图文件: {file_path}")

            try:
                # 使用助手函数运行异步导入
                import_result = _run_async_import(roadmap_service, file_path)

                if import_result.get("success"):
                    roadmap_id = import_result.get("roadmap_id")
                    logger.info(f"成功导入路线图 (ID: {roadmap_id}) 从文件: {file_path}")
                    success_count += 1
                else:
                    error = import_result.get("error", "未知错误")
                    logger.error(f"导入路线图文件 {file_path} 失败: {error}")
                    fail_count += 1
            except Exception as e:
                logger.error(f"导入路线图文件 {file_path} 时出错: {e}", exc_info=True)
                fail_count += 1

        logger.info(f"路线图数据初始化完成: 成功 {success_count}, 失败 {fail_count}")
    except Exception as e:
        logger.error(f"初始化路线图时出错: {e}", exc_info=True)

    return {"success": success_count, "failed": fail_count}
