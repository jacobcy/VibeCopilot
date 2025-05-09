"""
数据库仓库模块

提供各种数据实体的数据库访问方法
"""

# 导入仓库类
from src.db.repositories.docs_engine import BlockRepository, DocumentRepository, LinkRepository, LinkType
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.roadmap_repository import EpicRepository, MilestoneRepository, RoadmapRepository, StoryRepository
from src.db.repositories.rule_repository import RuleExampleRepository, RuleItemRepository, RuleRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.stage_repository import StageRepository
from src.db.repositories.system_config_repository import SystemConfigRepository
from src.db.repositories.template_repository import TemplateRepository, TemplateVariableRepository
from src.db.repositories.transition_repository import TransitionRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository

from .task_repository import TaskCommentRepository, TaskRepository

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
    # 任务仓库
    "TaskRepository",
    "TaskCommentRepository",
    # 模板仓库
    "TemplateRepository",
    "TemplateVariableRepository",
    # 规则仓库
    "RuleRepository",
    "RuleItemRepository",
    "RuleExampleRepository",
    # 系统配置仓库
    "SystemConfigRepository",
    # 工作流会话仓库
    "WorkflowDefinitionRepository",
    "FlowSessionRepository",
    "StageInstanceRepository",
    "StageRepository",
    "TransitionRepository",
]
