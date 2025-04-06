# 使用 VibeCopilot 数据库模块开发指南

## 目录结构概览

VibeCopilot 采用清晰的分层架构，数据模型与数据访问层分离：

```
/src
├── models/              # 数据模型定义
│   ├── db/              # 数据库模型定义
│   └── ...
├── db/                  # 数据库访问层
│   ├── repositories/    # 数据访问对象(Repository)实现
│   └── repository.py    # Repository基类
└── ...
```

## 核心概念

VibeCopilot 使用仓库模式（Repository Pattern）提供数据访问抽象层，主要组件包括：

1. **数据模型（Model）**：位于 `src/models/db`，基于 SQLAlchemy ORM
2. **数据仓库（Repository）**：位于 `src/db/repositories`，提供数据访问接口
3. **数据库会话（Session）**：管理数据库连接和事务

## 新模块开发流程

### 步骤 1：定义数据模型

在 `src/models/db` 创建新的模型文件（例如 `mymodule.py`）：

```python
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from src.models.db.base import Base

class MyModel(Base):
    """我的模型"""

    __tablename__ = "my_models"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    # 更多字段...

    # 关系定义
    parent_id = Column(String, ForeignKey("parent_models.id"))
    parent = relationship("ParentModel", back_populates="children")
```

### 步骤 2：在 `models/db/__init__.py` 中导出模型

```python
# 添加导入
from .mymodule import MyModel

# 更新 __all__ 列表
__all__ = [
    # 现有模型...
    "MyModel",
]
```

### 步骤 3：创建仓库类

在 `src/db/repositories` 创建仓库文件（例如 `mymodule_repository.py`）：

```python
from typing import List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import MyModel

class MyModelRepository(Repository[MyModel]):
    """MyModel仓库"""

    def __init__(self, session: Session):
        """初始化仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, MyModel)

    # 添加自定义查询方法
    def get_by_name(self, name: str) -> Optional[MyModel]:
        """根据名称查询

        Args:
            name: 模型名称

        Returns:
            MyModel对象或None
        """
        return self.session.query(MyModel).filter(MyModel.name == name).first()

    def get_with_relations(self, model_id: str) -> Optional[MyModel]:
        """获取模型及关联数据

        Args:
            model_id: 模型ID

        Returns:
            MyModel对象或None
        """
        return self.session.query(MyModel).filter(MyModel.id == model_id).first()
```

### 步骤 4：在 `repositories/__init__.py` 中导出仓库

```python
# 添加导入
from .mymodule_repository import MyModelRepository

# 更新 __all__ 列表
__all__ = [
    # 现有仓库...
    "MyModelRepository",
]
```

### 步骤 5：在 `db/__init__.py` 中导出仓库

```python
# 添加导入
from .repositories import MyModelRepository

# 更新 __all__ 列表
__all__ = [
    # 现有导出...
    "MyModelRepository",
]
```

## 使用示例

### 基础用法

```python
from sqlalchemy.orm import Session
from src.db import init_db, get_session_factory, MyModelRepository
from src.models import MyModel

# 初始化数据库
engine = init_db()
SessionFactory = get_session_factory(engine)

# 创建会话
with SessionFactory() as session:
    # 创建仓库实例
    repo = MyModelRepository(session)

    # 创建记录
    new_model = repo.create({
        "id": "model-001",
        "name": "测试模型",
        "description": "这是一个测试模型"
    })

    # 查询记录
    model = repo.get_by_id("model-001")
    models = repo.get_all()

    # 更新记录
    repo.update("model-001", {"name": "更新后的名称"})

    # 删除记录
    repo.delete("model-001")
```

### 使用自定义查询方法

```python
# 使用自定义查询方法
with SessionFactory() as session:
    repo = MyModelRepository(session)

    # 按名称查询
    model = repo.get_by_name("测试模型")

    # 获取关联数据
    model_with_relations = repo.get_with_relations("model-001")
```

### 批量操作及事务管理

```python
# 在事务中执行多个操作
with SessionFactory() as session:
    try:
        repo = MyModelRepository(session)

        # 批量创建
        for i in range(5):
            repo.create({
                "id": f"model-{i:03d}",
                "name": f"批量模型 {i}",
                "description": "批量创建的模型"
            })

        # 提交事务
        session.commit()
    except Exception as e:
        # 回滚事务
        session.rollback()
        print(f"操作失败: {str(e)}")
```

## 最佳实践

1. **职责分离**：
   - 模型负责定义数据结构
   - 仓库负责数据访问逻辑
   - 服务层负责业务逻辑

2. **使用仓库基类**：
   - 继承 `Repository[T]` 获取通用的 CRUD 方法
   - 为特定业务需求添加自定义方法

3. **命名规范**：
   - 模型类名使用 `PascalCase`（如 `MyModel`）
   - 仓库类名使用 `PascalCase` + `Repository`（如 `MyModelRepository`）
   - 方法名使用 `snake_case`（如 `get_by_name`）

4. **会话管理**：
   - 使用 `with` 语句确保会话正确关闭
   - 在服务层注入仓库，避免在业务逻辑中直接管理会话

5. **测试友好**：
   - 使用依赖注入模式便于单元测试
   - 仓库接受会话作为构造参数，便于模拟

## 常见问题

### 如何处理关系查询？

```python
# 一对多关系
stories = repo.session.query(Story).filter(Story.epic_id == epic_id).all()

# 多对多关系
tasks_with_label = repo.session.query(Task).join(Task.labels).filter(Label.id == label_id).all()
```

### 如何处理复杂查询？

对于复杂查询，可以在仓库中添加专门的方法：

```python
def find_by_criteria(self, status=None, created_after=None, tags=None):
    """根据多种条件查询

    Args:
        status: 状态筛选
        created_after: 创建时间筛选
        tags: 标签筛选

    Returns:
        符合条件的对象列表
    """
    query = self.session.query(self.model_class)

    if status:
        query = query.filter(self.model_class.status == status)

    if created_after:
        query = query.filter(self.model_class.created_at >= created_after)

    if tags:
        query = query.join(self.model_class.tags).filter(Tag.name.in_(tags))

    return query.all()
```
