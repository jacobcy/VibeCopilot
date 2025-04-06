#!/usr/bin/env python
"""
路线图模块基本使用示例

本示例演示了如何创建和使用路线图服务，包括路线图的创建、查询和更新。
"""

import logging
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.roadmap import RoadmapService

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """演示路线图模块的基本使用"""
    logger.info("开始路线图示例")

    # 创建路线图服务实例
    service = RoadmapService()

    # 创建新路线图
    logger.info("创建新路线图")
    result = service.create_roadmap("产品开发路线图", "产品功能开发计划", "1.0")
    if result["success"]:
        roadmap_id = result["roadmap_id"]
        logger.info(f"创建成功: {result['roadmap_name']} (ID: {roadmap_id})")
    else:
        logger.error(f"创建失败: {result.get('error')}")
        return

    # 列出所有路线图
    logger.info("列出所有路线图")
    roadmaps = service.list_roadmaps()
    logger.info(f"找到 {len(roadmaps['roadmaps'])} 个路线图")
    logger.info(f"当前活跃路线图: {roadmaps['active_id']}")

    # 获取路线图信息
    logger.info(f"获取路线图信息: {roadmap_id}")
    info = service.get_roadmap_info(roadmap_id)
    logger.info(f"路线图名称: {info['roadmap']['name']}")
    logger.info(f"里程碑数量: {info['stats']['milestones_count']}")
    logger.info(f"任务数量: {info['stats']['tasks_count']}")
    logger.info(f"进度: {info['stats']['progress']:.1f}%")

    # 导出到YAML文件
    logger.info("导出路线图到YAML文件")
    export_result = service.export_to_yaml(roadmap_id)
    if export_result["success"]:
        logger.info(f"导出成功: {export_result['file_path']}")
    else:
        logger.error(f"导出失败: {export_result.get('error')}")

    # 检查路线图状态
    logger.info("检查路线图状态")
    status = service.check_roadmap_status("roadmap", roadmap_id=roadmap_id)
    logger.info(f"里程碑数量: {status['status'].get('milestones', 0)}")
    logger.info(f"任务数量: {status['status'].get('tasks', 0)}")

    logger.info("路线图示例结束")


if __name__ == "__main__":
    main()
