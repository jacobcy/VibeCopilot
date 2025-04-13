#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型测试脚本

用于测试修改后的数据库模型是否正常工作。
"""

import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from src.db import ensure_tables_exist, get_session_factory
from src.models.db.stage import Stage
from src.models.db.transition import Transition
from src.models.db.workflow_definition import WorkflowDefinition

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def generate_uuid():
    """生成UUID"""
    return str(uuid.uuid4())


def test_create_workflow_with_stages_and_transitions():
    """测试创建工作流定义及其阶段和转换"""
    # 确保数据库表存在
    ensure_tables_exist()

    # 获取数据库会话
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 1. 创建工作流定义
        workflow_id = f"wf_{generate_uuid()[:8]}"
        workflow = WorkflowDefinition(
            id=workflow_id,
            name="测试工作流",
            type="test",
            description="这是一个测试工作流",
            stages_data=[{"id": "stage1", "name": "阶段1"}, {"id": "stage2", "name": "阶段2"}],
            source_rule=None,
        )
        session.add(workflow)
        session.flush()  # 确保ID已分配

        logger.info(f"创建了工作流定义: {workflow.id} - {workflow.name}")

        # 2. 创建阶段
        stage1 = Stage(
            id=f"stage_{generate_uuid()[:8]}",
            workflow_id=workflow.id,
            name="需求分析",
            description="分析和确认需求",
            order_index=1,
            checklist=["创建需求文档", "确认需求范围"],
            deliverables=["需求文档", "工作量评估"],
            is_end=False,
        )

        stage2 = Stage(
            id=f"stage_{generate_uuid()[:8]}",
            workflow_id=workflow.id,
            name="设计",
            description="系统设计和技术方案",
            order_index=2,
            checklist=["架构设计", "接口设计"],
            deliverables=["设计文档"],
            is_end=True,
        )

        session.add_all([stage1, stage2])
        session.flush()

        logger.info(f"创建了阶段: {stage1.id} - {stage1.name}")
        logger.info(f"创建了阶段: {stage2.id} - {stage2.name}")

        # 3. 创建转换
        transition = Transition(
            id=f"trans_{generate_uuid()[:8]}",
            workflow_id=workflow.id,
            from_stage=stage1.id,
            to_stage=stage2.id,
            condition="自动",
            description="需求分析完成后自动进入设计阶段",
        )

        session.add(transition)
        session.commit()

        logger.info(f"创建了转换: {transition.id}")

        # 4. 验证关系
        # 重新获取工作流定义以刷新关系
        workflow = session.query(WorkflowDefinition).filter_by(id=workflow.id).first()

        # 验证关系是否正确
        logger.info(f"工作流 {workflow.id} 有 {len(workflow.stages)} 个阶段")
        for stage in workflow.stages:
            logger.info(f"  - 阶段: {stage.id} - {stage.name}")

        logger.info(f"工作流 {workflow.id} 有 {len(workflow.transitions)} 个转换")
        for trans in workflow.transitions:
            from_stage = session.query(Stage).filter_by(id=trans.from_stage).first()
            to_stage = session.query(Stage).filter_by(id=trans.to_stage).first()
            logger.info(f"  - 转换: {from_stage.name} -> {to_stage.name}")

        logger.info("测试成功完成")
        return True

    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    try:
        result = test_create_workflow_with_stages_and_transitions()
        if result:
            logger.info("✅ 所有测试通过")
        else:
            logger.error("❌ 测试失败")
    except Exception as e:
        logger.error(f"❌ 测试异常: {str(e)}")
