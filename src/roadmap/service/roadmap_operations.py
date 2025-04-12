"""
路线图操作模块

提供路线图的创建、更新、删除和同步功能。
"""

import logging
import os
from typing import Any, Dict, List, Optional

from src.validation.roadmap_validation import RoadmapValidator

logger = logging.getLogger(__name__)


def create_roadmap(self, title: str, description: str = "", version: str = "1.0", roadmap_id: Optional[str] = None) -> Dict[str, Any]:
    """
    创建路线图

    Args:
        title: 路线图标题
        description: 路线图描述
        version: 路线图版本
        roadmap_id: 可选的自定义路线图ID，如不提供则自动生成

    Returns:
        Dict[str, Any]: 创建结果
    """
    try:
        # 检查路线图标题是否为空
        if not title:
            return {"success": False, "error": "路线图标题不能为空"}

        # 如果未提供roadmap_id，则基于标题生成ID
        if not roadmap_id:
            roadmap_slug = title.lower().replace(" ", "-")
            roadmap_id = f"roadmap-{roadmap_slug}"

        # 检查ID是否存在
        existing_roadmap = self.roadmap_repo.get_by_id(roadmap_id)
        if existing_roadmap:
            return {
                "success": False,
                "error": f"路线图ID已存在: {roadmap_id}",
                "existing_roadmap": existing_roadmap,
            }

        # 创建路线图对象
        roadmap = {
            "id": roadmap_id,
            "title": title,
            "description": description,
            "version": version,
            "status": "active",
            "created_at": str(self.get_now()),
            "updated_at": str(self.get_now()),
        }

        # 保存到数据库
        result = self.roadmap_repo.create(roadmap)

        # 自动设置为活跃路线图（如果是第一个路线图）
        if not self.active_roadmap_id:
            self.set_active_roadmap(roadmap_id)

        # 返回创建成功信息
        return {"success": True, "roadmap_id": roadmap_id, "roadmap": result}

    except Exception as e:
        # 记录错误并返回错误信息
        logger.error(f"创建路线图失败: {str(e)}")
        return {"success": False, "error": f"创建路线图失败: {str(e)}"}


def delete_roadmap(service, roadmap_id: str) -> Dict[str, Any]:
    """
    删除路线图

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID

    Returns:
        Dict[str, Any]: 删除结果
    """
    try:
        # 检查路线图是否存在
        roadmap = service.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

        # 检查是否是活跃路线图
        active_id = service.active_roadmap_id
        if roadmap_id == active_id:
            return {"success": False, "error": "不能删除当前活跃路线图，请先切换到其他路线图"}

        # 删除路线图及其所有内容
        roadmap_name = roadmap.get("title")
        try:
            if service.roadmap_repo.delete(roadmap_id):
                logger.info(f"删除路线图: {roadmap_name} (ID: {roadmap_id})")
                return {"success": True, "roadmap_id": roadmap_id, "roadmap_name": roadmap_name}
            else:
                return {"success": False, "error": "删除路线图失败"}
        except Exception as e:
            logger.error(f"删除路线图时出错: {e}")
            return {"success": False, "error": str(e)}

    except Exception as e:
        logger.error(f"删除路线图出错: {e}")
        return {"success": False, "error": str(e)}


def update_roadmap_status(
    service,
    element_id: str,
    element_type: str = "task",
    status: Optional[str] = None,
    roadmap_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    更新路线图元素状态

    Args:
        service: 路线图服务实例
        element_id: 元素ID
        element_type: 元素类型
        status: 新状态
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        Dict[str, Any]: 更新结果
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 更新状态
    result = service.status.update_element(element_id, element_type, status, roadmap_id)

    return {"success": result.get("updated", False), "element": result}


def update_roadmap(service, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
    """
    更新路线图数据

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        Dict[str, Any]: 更新结果
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 更新路线图
    result = service.updater.update_roadmap(roadmap_id)

    return result


def sync_to_github(service, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
    """
    同步路线图到GitHub

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        Dict[str, Any]: 同步结果
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 同步到GitHub
    result = service.github_sync.sync_roadmap_to_github(roadmap_id)

    return result


def sync_from_github(service, repo_name: str, branch: str = "main", theme: Optional[str] = None, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
    """
    从GitHub同步数据到路线图

    Args:
        service: 路线图服务实例
        repo_name: GitHub仓库名称（格式：owner/repo）
        branch: 要同步的分支名称，默认为main
        theme: GitHub项目主题标签，用于筛选特定主题的问题
        roadmap_id: 路线图ID，不提供则使用活跃路线图或创建新路线图

    Returns:
        Dict[str, Any]: 同步结果
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 从GitHub同步
    result = service.github_sync.sync_from_github(repo_name, branch, theme, roadmap_id)

    return result


def export_to_yaml(service, roadmap_id: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    导出路线图到YAML文件

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图
        output_path: 输出文件路径，不提供则使用默认路径

    Returns:
        Dict[str, Any]: 导出结果
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 导出到YAML
    result = service.yaml_sync.export_to_yaml(roadmap_id, output_path)

    return result


async def import_from_yaml(service, file_path: str, roadmap_id: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    从YAML文件导入路线图

    采用两阶段导入流程：
    1. 验证YAML文件格式是否有效
    2. 如果无效，先尝试基本修复，再尝试LLM修复

    Args:
        service: 路线图服务实例
        file_path: YAML文件路径
        roadmap_id: 路线图ID，可选
        verbose: 是否输出详细日志

    Returns:
        Dict[str, Any]: 导入结果
    """
    import yaml

    from src.parsing.processors.roadmap_processor import RoadmapProcessor

    logger.info(f"开始从YAML导入路线图: {file_path}")

    if not os.path.exists(file_path):
        return {"success": False, "error": f"文件不存在: {file_path}"}

    try:
        # 阶段1: 尝试直接解析YAML文件
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            # 解析YAML
            data = yaml.safe_load(content)

            # 使用验证器检查结构
            validator = RoadmapValidator()
            is_valid, warnings, errors = validator.validate_file(file_path)

            if is_valid:
                # YAML有效，直接导入
                return _process_valid_yaml(service, data, file_path, roadmap_id, verbose)

        except yaml.YAMLError as ye:
            logger.warning(f"YAML解析失败: {str(ye)}")
            # 继续到修复阶段

        # 阶段2: 尝试修复YAML并再次导入
        processor = RoadmapProcessor()
        success, result = processor.fix_file(file_path)

        if success:
            logger.info(f"YAML修复成功，使用修复后的文件: {result}")

            # 用修复后的文件重新尝试导入
            with open(result, "r", encoding="utf-8") as f:
                fixed_content = f.read()

            try:
                fixed_data = yaml.safe_load(fixed_content)

                # 验证修复后的数据
                validator = RoadmapValidator()
                if validator.validate(fixed_data):
                    return _process_valid_yaml(service, fixed_data, result, roadmap_id, verbose)
                else:
                    errors = validator.get_errors()
                    return {"success": False, "error": f"修复后的YAML仍然无效: {', '.join(errors)}"}

            except yaml.YAMLError as ye:
                return {"success": False, "error": f"修复后的YAML解析失败: {str(ye)}"}
        else:
            # 无法修复
            return {"success": False, "error": f"无法修复YAML文件: {result}"}

    except Exception as e:
        logger.exception(f"导入过程中出错: {str(e)}")
        return {"success": False, "error": f"导入过程中出错: {str(e)}"}


def _process_valid_yaml(service, data: Dict[str, Any], file_path: str, roadmap_id: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """处理验证通过的YAML数据

    注意: 当前实现会重复验证YAML文件，因为import_from_yaml方法会再次验证。
    在将来的版本中应优化这个过程，使用传入的data参数而不是重新解析文件。
    """
    try:
        # 延迟导入以避免循环依赖
        from src.roadmap.sync import YamlSyncService

        sync_service = YamlSyncService(service)
        # 使用import_service而不是直接创建导入器
        importer = sync_service.import_service
        # 使用import_from_yaml方法而不是import_data
        # 传递data参数的需求移至下一版本实现
        result = importer.import_from_yaml(file_path, roadmap_id, verbose)

        if result.get("success", False):
            logger.info(f"成功导入路线图: {result.get('roadmap_id')}")
            return result
        else:
            logger.error(f"导入失败: {result.get('error')}")
            return result

    except Exception as e:
        logger.exception(f"处理YAML数据时出错: {str(e)}")
        return {"success": False, "error": f"处理YAML数据时出错: {str(e)}"}
