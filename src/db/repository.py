"""
数据访问对象基类模块

提供通用的数据库操作接口，所有具体仓库类都应继承自此基类。
"""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from src.models.db import Base

# 定义泛型类型T，限制为Base的子类
T = TypeVar("T", bound=Base)

logger = logging.getLogger(__name__)


class Repository(Generic[T]):
    """数据访问对象基类 (无状态)"""

    def __init__(self, model_class: Type[T]):
        """初始化

        Args:
            model_class: 模型类
        """
        self.model_class = model_class

    def create(self, session: Session, data: Dict[str, Any]) -> T:
        """创建记录

        Args:
            session: SQLAlchemy 会话对象
            data: 数据字典

        Returns:
            新创建的实体对象
        """
        try:
            logger.debug(f"尝试创建实体对象: {self.model_class.__name__}")
            logger.debug(f"输入数据: {data}")

            # 仅保留模型类名和数据概要的日志
            logger.debug(f"Repository.create - 模型类: {self.model_class.__name__}")

            # 简化输出数据，避免过长日志
            data_summary = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool, type(None)))}
            logger.debug(f"Repository.create - 数据摘要: {data_summary}")

            # 创建实例逻辑
            if hasattr(self.model_class, "from_dict"):
                # 使用from_dict方法创建实例
                logger.debug("使用from_dict方法创建实例")
                instance = self.model_class.from_dict(data)
            else:
                # 使用关键字参数拆包创建实例
                model_attrs = data.copy()
                logger.debug(f"模型创建参数: {model_attrs}")
                instance = self.model_class(**model_attrs)

            # 简化实例信息输出
            instance_attrs = {
                k: v for k, v in vars(instance).items() if not k.startswith("_") and not isinstance(v, (dict, list)) and k != "_sa_instance_state"
            }
            logger.debug(f"Repository.create - 实例属性: {instance_attrs}")

            session.add(instance)
            session.flush()
            logger.debug(f"实体对象已添加到会话，ID: {getattr(instance, 'id', None)}")
            return instance
        except Exception as e:
            logger.error(f"创建实体对象失败: {str(e)}")
            raise e

    def get_by_id(self, session: Session, id: Any) -> Optional[T]:
        """通用按ID获取实体的方法

        Args:
            session: SQLAlchemy 会话对象
            id: 实体ID

        Returns:
            实体对象或None
        """
        logger.debug(f"Repository.get_by_id entered for model {self.model_class.__name__}, id: {id}")
        logger.debug(f"Received session object: type={type(session)}, value={session}")
        session_bind = getattr(session, "bind", "Attribute Missing")
        logger.debug(f"Repository.get_by_id: Received session bind. Bind Type: {type(session_bind)}, Value: {session_bind}")

        if not id:
            logger.debug("ID is None or empty, returning None.")
            return None
        try:
            if not isinstance(session, Session):
                logger.error(f"Repository get_by_id received invalid session type: {type(session)}")
                raise TypeError(f"Expected SQLAlchemy Session, got {type(session)}")

            logger.debug(f"Executing query: session.query({self.model_class.__name__}).filter(id == {id}).first()")
            result = session.query(self.model_class).filter(self.model_class.id == id).first()
            logger.debug(f"Query result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting {self.model_class.__name__} by id {id}: {e}", exc_info=True)
            raise

    def get_all(self, session: Session, as_dict: bool = False) -> List[Any]:
        """获取所有记录

        Args:
            session: SQLAlchemy 会话对象
            as_dict: 是否将对象转换为字典返回，默认为False

        Returns:
            如果as_dict为True，返回实体对象字典列表；否则返回实体对象列表
        """
        try:
            logger.debug(f"获取所有 {self.model_class.__name__} 实体")
            entities = session.query(self.model_class).all()
            logger.debug(f"找到 {len(entities)} 个 {self.model_class.__name__} 实体")

            if not as_dict:
                # 直接返回实体对象列表
                return entities

            # 转换为字典列表
            result = []
            for entity in entities:
                if hasattr(entity, "to_dict"):
                    try:
                        # 安全调用to_dict，避免可能的递归
                        entity_dict = self._safe_to_dict(entity)
                        result.append(entity_dict)
                    except Exception as e:
                        logger.error(f"实体转换为字典失败: {e}", exc_info=True)
                        # 尝试使用替代方法
                        entity_dict = {k: v for k, v in vars(entity).items() if not k.startswith("_")}
                        result.append(entity_dict)
                else:
                    # 移除SQLAlchemy内部属性
                    entity_dict = {k: v for k, v in vars(entity).items() if not k.startswith("_")}
                    result.append(entity_dict)

            logger.debug(f"成功转换 {len(result)} 个实体为字典格式")
            return result
        except Exception as e:
            logger.error(f"获取所有 {self.model_class.__name__} 实体失败: {e}", exc_info=True)
            return []

    def _safe_to_dict(self, entity: Any) -> Dict[str, Any]:
        """安全地将实体转换为字典，避免递归调用

        Args:
            entity: 实体对象

        Returns:
            字典表示
        """
        # 获取基本属性，不包含关系
        result = {}
        for key, value in vars(entity).items():
            # 排除私有属性和关系属性
            if not key.startswith("_") and not hasattr(value, "__table__"):
                # 处理基本类型数据
                if isinstance(value, (str, int, float, bool, type(None))):
                    result[key] = value
                elif isinstance(value, (list, tuple)):
                    # 略过列表类型属性，避免递归
                    continue
                else:
                    # 其他类型转为字符串
                    result[key] = str(value)

        return result

    def update(self, session: Session, id: str, data: Dict[str, Any]) -> Optional[T]:
        """更新记录

        Args:
            session: SQLAlchemy 会话对象
            id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体对象或None
        """
        try:
            instance = self.get_by_id(session, id)
            if not instance:
                return None

            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            session.flush()
            return instance
        except Exception as e:
            raise e

    def delete(self, session: Session, id: str) -> bool:
        """删除记录

        Args:
            session: SQLAlchemy 会话对象
            id: 实体ID

        Returns:
            是否删除成功
        """
        try:
            instance = self.get_by_id(session, id)
            if not instance:
                return False

            session.delete(instance)
            session.flush()
            return True
        except Exception as e:
            raise e

    def filter(self, session: Session, **filters) -> List[T]:
        """根据过滤条件查询

        Args:
            session: SQLAlchemy 会话对象
            **filters: 过滤条件

        Returns:
            符合条件的实体对象列表
        """
        query = session.query(self.model_class)

        for attr, value in filters.items():
            if hasattr(self.model_class, attr):
                query = query.filter(getattr(self.model_class, attr) == value)

        return query.all()
