"""
工作流初始数据模块

提供工作流表的初始数据
"""

import json
import logging
import uuid
from datetime import datetime

from src.core.config import refresh_config
from src.db import get_session
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository

logger = logging.getLogger(__name__)


def init_workflows():
    """初始化工作流数据"""
    # 刷新配置
    refresh_config()

    session = get_session()
    repo = WorkflowDefinitionRepository(session)

    # 添加一些示例工作流
    workflows = [
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

    success_count = 0
    for workflow in workflows:
        try:
            repo.create(data=workflow)
            success_count += 1
        except Exception as e:
            logger.error(f"创建工作流失败: {workflow['name']}", exc_info=True)

    logger.info(f"工作流初始化完成: 成功 {success_count}/{len(workflows)}")
    session.close()
