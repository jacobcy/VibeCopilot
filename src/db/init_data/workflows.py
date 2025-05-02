"""
工作流初始数据模块

提供工作流表的初始数据，支持从.ai/workflow目录读取JSON文件
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.config import get_app_dir, refresh_config
from src.db import get_session
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository

logger = logging.getLogger(__name__)


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """加载JSON文件

    Args:
        file_path: JSON文件路径

    Returns:
        Optional[Dict[str, Any]]: JSON文件内容
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件 {file_path} 失败: {e}")
        return None


def get_workflow_files() -> List[str]:
    """获取工作流文件列表

    Returns:
        List[str]: 工作流文件路径列表
    """
    workflow_dir = Path(get_app_dir()) / ".ai" / "workflow"

    if not workflow_dir.exists():
        logger.warning(f"工作流目录不存在: {workflow_dir}")
        return []

    # 获取所有.json文件
    json_files = list(workflow_dir.glob("*.json"))

    return [str(file) for file in json_files]


def init_workflows() -> Dict[str, int]:
    """初始化工作流数据，并返回统计"""
    # 刷新配置
    refresh_config()

    session = get_session()
    # Initialize repo without session
    repo = WorkflowDefinitionRepository()

    # 添加自定义工作流
    workflow_files = get_workflow_files()
    custom_workflows = []
    files_failed_parsing = 0

    # 读取并解析工作流文件
    for file_path in workflow_files:
        try:
            workflow_data = load_json_file(file_path)
            if workflow_data:
                # 确保有ID字段
                if "id" not in workflow_data:
                    workflow_data["id"] = f"wfd_{uuid.uuid4().hex[:8]}"

                # 如果stages_data是列表，需要转换为JSON字符串
                if "stages_data" in workflow_data and not isinstance(workflow_data["stages_data"], str):
                    workflow_data["stages_data"] = json.dumps(workflow_data["stages_data"])

                custom_workflows.append(workflow_data)
                logger.info(f"从文件 {file_path} 加载工作流: {workflow_data.get('name')}")
            else:
                files_failed_parsing += 1
        except Exception as e:
            logger.error(f"解析工作流文件 {file_path} 失败: {e}", exc_info=True)
            files_failed_parsing += 1

    # 如果没有从文件加载工作流，使用默认示例
    if not custom_workflows and not workflow_files:
        logger.info("没有找到工作流文件，使用默认示例")
        custom_workflows = [
            {
                "id": f"wfd_{uuid.uuid4().hex[:8]}",
                "name": "代码审查流程",
                "description": "标准代码审查工作流程",
                "type": "code_review",
                "stages_data": json.dumps(
                    [
                        {"name": "静态代码分析", "description": "使用工具进行代码静态分析", "order_index": 1, "checklist": {"tool": "pylint", "threshold": 8.0}},
                        {"name": "单元测试检查", "description": "运行单元测试并检查覆盖率", "order_index": 2, "checklist": {"min_coverage": 70}},
                        {
                            "name": "人工代码审查",
                            "description": "至少一名高级开发人员进行代码审查",
                            "order_index": 3,
                            "checklist": {"min_reviewers": 1, "role": "senior_developer"},
                        },
                    ]
                ),
                "source_rule": "code_review_workflow",
            },
            {
                "id": f"wfd_{uuid.uuid4().hex[:8]}",
                "name": "发布流程",
                "description": "标准发布工作流程",
                "type": "release",
                "stages_data": json.dumps(
                    [
                        {"name": "版本号更新", "description": "更新项目版本号", "order_index": 1, "checklist": {"version_file": "pyproject.toml"}},
                        {"name": "生成变更日志", "description": "生成本次发布的变更日志", "order_index": 2, "checklist": {"template": "changelog.md.j2"}},
                        {"name": "打包发布", "description": "构建并上传发布包", "order_index": 3, "checklist": {"registry": "pypi"}},
                    ]
                ),
                "source_rule": "release_workflow",
            },
        ]

    # 创建工作流
    success_count = 0
    fail_count = files_failed_parsing  # 初始化失败计数为解析失败的文件数
    for workflow in custom_workflows:
        try:
            # 检查工作流是否已存在
            existing = repo.get_by_name(session, workflow.get("name"))
            if existing:
                logger.warning(f"工作流 '{workflow.get('name')}' 已存在，跳过创建")
                continue  # 或者可以考虑更新？目前跳过

            # Pass session to create method
            repo.create(session, data=workflow)
            success_count += 1
        except Exception as e:
            logger.error(f"创建工作流失败: {workflow.get('name')}", exc_info=True)
            fail_count += 1

    logger.info(f"工作流初始化完成: 成功 {success_count}, 失败 {fail_count}")
    session.close()
    return {"success": success_count, "failed": fail_count}
