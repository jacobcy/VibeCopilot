"""
数据访问对象基类模块

提供通用的数据库操作接口，所有具体仓库类都应继承自此基类。
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from src.models.db import Base

# 定义泛型类型T，限制为Base的子类
T = TypeVar("T", bound=Base)


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
            if hasattr(self.model_class, "from_dict"):
                # 使用from_dict方法创建实例
                instance = self.model_class.from_dict(data)
            else:
                # 使用关键字参数拆包创建实例
                # 防止字典内部有多余的键或特殊字符的键导致初始化失败
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
                else:
                    # 如果无法获取参数信息，直接使用全部数据
                    model_attrs = data

                instance = self.model_class(**model_attrs)

            self.session.add(instance)
            self.session.commit()
            return instance
        except Exception as e:
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

    def get_all(self) -> List[T]:
        """获取所有记录

        Returns:
            实体对象列表
        """
        return self.session.query(self.model_class).all()

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
