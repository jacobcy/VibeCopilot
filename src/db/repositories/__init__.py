"""
数据库仓库模块

提供各种数据实体的数据库访问方法
"""

# 导入仓库类
from src.db.repositories.docs_engine import (
    BlockRepository,
    DocumentRepository,
    LinkRepository,
    LinkType,
)
from src.db.repositories.flow_session_repository import (
    FlowSessionRepository,
    StageInstanceRepository,
    WorkflowDefinitionRepository,
)
from src.db.repositories.roadmap_repository import (
    EpicRepository,
    MilestoneRepository,
    RoadmapRepository,
    StoryRepository,
    TaskRepository,
)
from src.db.repositories.template_repository import TemplateRepository, TemplateVariableRepository
from src.db.repositories.workflow_repository import (
    WorkflowExecutionRepository,
    WorkflowRepository,
    WorkflowStepRepository,
)

# 导出所有仓库类
__all__ = [
    # 文档引擎仓库
    "DocumentRepository",
    "BlockRepository",
    "LinkRepository",
    "LinkType",
    # 路线图仓库
    "RoadmapRepository",
    "EpicRepository",
    "StoryRepository",
    "MilestoneRepository",
    "TaskRepository",
    # 模板仓库
    "TemplateRepository",
    "TemplateVariableRepository",
    # 工作流仓库
    "WorkflowRepository",
    "WorkflowExecutionRepository",
    "WorkflowStepRepository",
    # 工作流会话仓库
    "WorkflowDefinitionRepository",
    "FlowSessionRepository",
    "StageInstanceRepository",
]
