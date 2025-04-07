#!/usr/bin/env python
"""
调试Repository创建过程

模拟Repository类的create方法，排查问题
"""

import inspect
import logging
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Generic, Type, TypeVar

from sqlalchemy.orm import Session

from src.db import get_engine, get_session_factory
from src.models.db.roadmap import Task

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

T = TypeVar("T")


class MockRepository(Generic[T]):
    """模拟Repository类"""

    def __init__(self, session: Session, model_class: Type[T]):
        """初始化

        Args:
            session: SQLAlchemy会话对象
            model_class: 模型类
        """
        self.session = session
        self.model_class = model_class

    def create_v1(self, data: Dict[str, Any]) -> T:
        """创建记录（版本1 - 原始版本）

        Args:
            data: 数据字典

        Returns:
            新创建的实体对象
        """
        logger.info("使用版本1创建实例")
        try:
            logger.info(f"数据: {data}")
            # 直接使用参数创建实例
            instance = self.model_class(**data)

            logger.info(f"实例创建成功: {instance}")

            return instance
        except Exception as e:
            logger.error(f"创建实例失败: {e}")
            raise e

    def create_v2(self, data: Dict[str, Any]) -> T:
        """创建记录（版本2 - 改进版本）

        Args:
            data: 数据字典

        Returns:
            新创建的实体对象
        """
        logger.info("使用版本2创建实例")
        try:
            # 使用关键字参数拆包创建实例
            logger.info(f"原始数据: {data}")

            # 防止字典内部有多余的键或特殊字符的键导致初始化失败
            model_attrs = {}
            # 获取模型类的__init__所需的参数
            if hasattr(self.model_class, "__init__"):
                init_params = inspect.signature(self.model_class.__init__).parameters
                allowed_params = set(init_params.keys()) - {"self"}

                logger.info(f"模型允许的参数: {allowed_params}")

                # 仅保留模型初始化所需的参数
                for key, value in data.items():
                    if key in allowed_params:
                        model_attrs[key] = value
            else:
                # 如果无法获取参数信息，直接使用全部数据
                model_attrs = data

            logger.info(f"过滤后的数据: {model_attrs}")

            # 尝试直接创建
            instance = self.model_class(**model_attrs)

            logger.info(f"实例创建成功: {instance}")

            return instance
        except Exception as e:
            logger.error(f"创建实例失败: {e}")
            raise e


def main():
    """主函数"""
    try:
        # 获取数据库引擎和会话
        engine = get_engine()
        session_factory = get_session_factory(engine)
        session = session_factory()

        # 创建模拟Repository
        mock_repo = MockRepository(session, Task)

        # 创建测试数据
        task_id = f"T{uuid.uuid4().hex[:6]}"
        test_data = {
            "id": task_id,
            "title": "测试任务",
            "description": "测试Repository.create方法",
            "status": "todo",
            "priority": "P1",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            # 增加一些额外字段
            "extra_field1": "额外字段1",
            "extra_field2": 123,
        }

        logger.info("=" * 50)
        logger.info("尝试使用原始方法创建实例")
        try:
            task1 = mock_repo.create_v1(test_data)
            logger.info(f"✅ 版本1创建成功: {task1.id}")
        except Exception as e:
            logger.error(f"❌ 版本1创建失败: {e}")

        logger.info("=" * 50)
        logger.info("尝试使用改进方法创建实例")
        try:
            task2 = mock_repo.create_v2(test_data)
            logger.info(f"✅ 版本2创建成功: {task2.id}")
        except Exception as e:
            logger.error(f"❌ 版本2创建失败: {e}")

        # 检查Task.__init__的参数要求
        logger.info("=" * 50)
        logger.info("检查Task.__init__方法的参数:")
        sig = inspect.signature(Task.__init__)
        for param_name, param in sig.parameters.items():
            if param_name != "self":
                logger.info(f"参数 {param_name}: {param.default}")

        # 额外测试：直接使用**方式创建
        logger.info("=" * 50)
        logger.info("尝试直接使用Task类创建实例")
        try:
            task3 = Task(**{"id": f"T{uuid.uuid4().hex[:6]}", "title": "直接创建的任务"})
            logger.info(f"✅ 直接创建成功: {task3.id}")
        except Exception as e:
            logger.error(f"❌ 直接创建失败: {e}")

        return 0
    except Exception as e:
        logger.error(f"测试过程出现错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
