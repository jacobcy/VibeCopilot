import json
import logging
import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_config
from src.db.session_manager import session_scope

logger = logging.getLogger(__name__)

# 导入所有数据模型以确保它们被定义
from src.models.db import *  # noqa


# 初始化数据库并创建表结构
def init_database(force_recreate: bool = False) -> bool:
    """
    初始化数据库，创建表结构

    Args:
        force_recreate: 是否强制重建数据库，默认为False

    Returns:
        bool: 是否成功初始化
    """
    try:
        config = get_config()
        db_path = config.get("database.path", "db/vibecopilot.db")

        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 创建引擎
        engine = create_engine(f"sqlite:///{db_path}")

        # 如果force_recreate为True，则删除所有表并重新创建
        if force_recreate:
            logger.info("强制重建数据库...")
            from src.models.db.base import Base

            Base.metadata.drop_all(engine)

        # 创建所有表
        from src.models.db.base import Base

        Base.metadata.create_all(engine)

        # 初始化基础数据
        init_basic_data(engine)

        # 导入工作流定义
        try:
            import_workflows()
        except Exception as we:
            logger.error(f"导入工作流失败: {we}")

        logger.info("数据库初始化完成")
        return True
    except Exception as e:
        logger.error(f"初始化数据库失败: {e}")
        return False


def init_basic_data(engine):
    """初始化基础数据"""
    # 在这里添加基础数据初始化逻辑
    pass


def import_workflows():
    """导入所有工作流定义"""
    try:
        # 导入通用任务工作流
        workflow_path = Path("/Users/jacobcy/Public/VibeCopilot/.ai/workflow/simple-task.json")
        if workflow_path.exists():
            with session_scope() as session:
                with open(workflow_path, "r") as f:
                    workflow_data = json.load(f)

                    # 从数据库中查询此工作流
                    from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
                    from src.models.db.workflow_definition import WorkflowDefinition

                    workflow_repo = WorkflowDefinitionRepository()
                    workflow_id = workflow_data["id"]

                    # 检查工作流是否存在
                    existing = workflow_repo.get_by_id(session, workflow_id)

                    if existing:
                        logger.info(f"工作流 {workflow_id} 已存在，更新中...")
                        # 更新现有工作流
                        # 提取需要的字段
                        update_data = {
                            "name": workflow_data.get("name"),
                            "type": "universal_task",
                            "description": workflow_data.get("description"),
                            "stages_data": workflow_data.get("stages", []),
                        }
                        workflow_repo.update(session, workflow_id, update_data)
                    else:
                        logger.info(f"创建新工作流: {workflow_id}")
                        # 创建新工作流记录
                        workflow_repo.create_workflow(
                            session=session,
                            name=workflow_data.get("name"),
                            workflow_type="universal_task",
                            description=workflow_data.get("description"),
                            stages_data=workflow_data.get("stages", []),
                        )

                    logger.info(f"工作流 {workflow_id} 已成功导入")
    except Exception as e:
        logger.error(f"导入工作流失败: {e}")
        raise
