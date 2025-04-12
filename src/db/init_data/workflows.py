"""
工作流初始数据模块

提供工作流相关表的初始数据
"""

import logging
from datetime import datetime

from src.db import get_session
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository

logger = logging.getLogger(__name__)


def init_workflows():
    """初始化工作流数据"""
    session = get_session()
    repo = WorkflowDefinitionRepository(session)

    # 添加一些示例工作流
    workflows = [
        {
            "name": "需求开发流程",
            "description": "从需求分析到功能上线的标准流程",
            "content": """
stages:
  - name: 需求分析
    description: 分析和确认需求
    actions:
      - 创建需求文档
      - 确认需求范围
      - 评估工作量

  - name: 设计
    description: 系统设计和技术方案
    actions:
      - 架构设计
      - 接口设计
      - 数据模型设计

  - name: 开发
    description: 功能实现
    actions:
      - 编写代码
      - 单元测试
      - 代码审查

  - name: 测试
    description: 功能测试和验证
    actions:
      - 集成测试
      - 功能测试
      - 性能测试

  - name: 发布
    description: 功能上线
    actions:
      - 准备发布计划
      - 执行发布
      - 监控系统
""",
            "category": "development",
            "status": "active",
        }
    ]

    success_count = 0
    for workflow in workflows:
        try:
            repo.create(**workflow)
            success_count += 1
        except Exception as e:
            logger.error(f"创建工作流失败: {workflow['name']}", exc_info=True)

    logger.info(f"工作流初始化完成: 成功 {success_count}/{len(workflows)}")
    session.close()
