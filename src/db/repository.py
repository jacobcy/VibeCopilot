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
    """数据访问对象基类"""

    def __init__(self, session: Session, model_class: Type[T]):
        """初始化

        Args:
            session: SQLAlchemy会话对象
            model_class: 模型类
        """
        self.session = session
        self.model_class = model_class

    def create(self, data: Dict[str, Any]) -> T:
        """创建记录

        Args:
            data: 数据字典

        Returns:
            新创建的实体对象
        """
        try:
            logger.debug(f"尝试创建实体对象: {self.model_class.__name__}")
            logger.debug(f"输入数据: {data}")

            # 打印重要信息到控制台
            print(f"Repository.create - 模型类: {self.model_class.__name__}")
            print(f"Repository.create - 数据: {data}")

            if "title" in data:
                print(f"Repository.create - title字段值: '{data['title']}'")
            else:
                print(f"Repository.create - 数据中不存在title字段")

            if hasattr(self.model_class, "from_dict"):
                # 使用from_dict方法创建实例
                logger.debug(f"使用from_dict方法创建实例")
                print(f"Repository.create - 使用from_dict方法创建实例")
                instance = self.model_class.from_dict(data)
            else:
                # 使用关键字参数拆包创建实例
                # 防止字典内部有多余的键或特殊字符的键导致初始化失败
                # 改为直接使用全部数据，而不是尝试提取参数
                # SQLAlchemy模型通常会忽略未定义列的额外参数
                model_attrs = data.copy()

                # 如果非常需要过滤参数，使用这个代码块
                """
                model_attrs = {}
                # 获取模型类的__init__所需的参数
                if hasattr(self.model_class, "__init__"):
                    import inspect

                    init_params = inspect.signature(self.model_class.__init__).parameters
                    allowed_params = set(init_params.keys()) - {"self"}

                    # 仅保留模型初始化所需的参数
                    for key, value in data.items():
                        if key in allowed_params:
                            model_attrs[key] = value
                            logger.debug(f"找到参数 {key}: {value}")
                            print(f"Repository.create - 参数设置 {key}: {value}")
                        else:
                            logger.debug(f"忽略不需要的参数 {key}: {value}")
                            print(f"Repository.create - 忽略参数 {key}: {value}")
                else:
                    # 如果无法获取参数信息，直接使用全部数据
                    model_attrs = data
                """

                logger.debug(f"模型创建参数: {model_attrs}")
                print(f"Repository.create - 最终模型参数: {model_attrs}")
                if "title" in model_attrs:
                    print(f"Repository.create - 最终title字段值: '{model_attrs['title']}'")
                else:
                    print(f"Repository.create - 最终参数中不存在title字段")

                instance = self.model_class(**model_attrs)

            logger.debug(f"创建的实例: {instance.__dict__}")
            print(f"Repository.create - 创建实例: {instance.__dict__}")
            if hasattr(instance, "title"):
                print(f"Repository.create - 实例title属性: '{instance.title}'")
            else:
                print(f"Repository.create - 实例没有title属性")

            self.session.add(instance)
            self.session.commit()
            logger.debug(f"实体对象提交成功，ID: {getattr(instance, 'id', None)}")
            return instance
        except Exception as e:
            logger.error(f"创建实体对象失败: {str(e)}")
            print(f"Repository.create - 异常: {str(e)}")
            self.session.rollback()
            raise e

    def get_by_id(self, id: str) -> Optional[T]:
        """根据ID获取记录

        Args:
            id: 实体ID

        Returns:
            实体对象或None
        """
        return self.session.query(self.model_class).filter(self.model_class.id == id).first()

    def get_all(self, as_dict: bool = False) -> List[Any]:
        """获取所有记录

        Args:
            as_dict: 是否将对象转换为字典返回，默认为False

        Returns:
            如果as_dict为True，返回实体对象字典列表；否则返回实体对象列表
        """
        try:
            logger.debug(f"获取所有 {self.model_class.__name__} 实体")
            entities = self.session.query(self.model_class).all()
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

    def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """更新记录

        Args:
            id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体对象或None
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None

            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            self.session.commit()
            return instance
        except Exception as e:
            self.session.rollback()
            raise e

    def delete(self, id: str) -> bool:
        """删除记录

        Args:
            id: 实体ID

        Returns:
            是否删除成功
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False

            self.session.delete(instance)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e

    def filter(self, **filters) -> List[T]:
        """根据过滤条件查询

        Args:
            **filters: 过滤条件

        Returns:
            符合条件的实体对象列表
        """
        query = self.session.query(self.model_class)

        for attr, value in filters.items():
            if hasattr(self.model_class, attr):
                query = query.filter(getattr(self.model_class, attr) == value)

        return query.all()
