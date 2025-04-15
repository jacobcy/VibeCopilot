# VibeCopilot数据库-实体管理方案设计

## 一、现状分析

1. **实体映射定义**：
   - 系统在`entity_mapping.py`中定义了8种实体类型(task, epic, story, template, label, rule, workflow, comment)
   - 每种实体类型都有对应的数据库表

2. **实现不完整问题**：
   - 在`DatabaseService`中，只实现了部分实体类型的仓库(epic, story, task)
   - 其他实体类型(rule, workflow, template等)虽有表定义，但缺少仓库实现

3. **管理方式不统一**：
   - 核心业务实体(epic, story, task)通过通用和专用API双管理
   - 特殊实体(rule, workflow)可能使用专门服务管理

## 二、设计目标

1. **统一性**：所有实体类型都应有完整的仓库实现和API
2. **扩展性**：能够轻松添加新实体类型
3. **专业化**：保留特定实体的专用管理逻辑
4. **渐进式**：支持分阶段实现，优先核心业务实体

## 三、核心设计

### 1. 实体仓库注册系统

创建一个实体仓库注册系统，使所有实体类型都能有对应的仓库实现：

```python
class RepositoryRegistry:
    """实体仓库注册中心，管理所有实体类型对应的仓库类"""

    # 仓库类映射
    _registry = {
        "epic": EpicRepository,
        "story": StoryRepository,
        "task": TaskRepository,
        # 新增仓库类映射
        "rule": RuleRepository,
        "workflow": WorkflowRepository,
        "template": TemplateRepository,
        "label": LabelRepository,
        "comment": CommentRepository
    }

    @classmethod
    def get_repository_class(cls, entity_type):
        """获取实体类型对应的仓库类"""
        return cls._registry.get(entity_type)

    @classmethod
    def register(cls, entity_type, repository_class):
        """注册新的实体类型与仓库类映射"""
        cls._registry[entity_type] = repository_class

    @classmethod
    def get_all_entity_types(cls):
        """获取所有已注册的实体类型"""
        return list(cls._registry.keys())
```

### 2. 改进DatabaseService初始化

修改DatabaseService的初始化方法，动态创建各类型仓库实例：

```python
def __init__(self):
    """初始化数据库服务"""
    # 单例检查代码保持不变

    try:
        # 初始化数据库连接等代码保持不变

        # 动态初始化仓库
        self.repo_map = {}
        self._initialize_repositories()

        # 创建实体管理器
        self.entity_manager = EntityManager(self.repo_map)

        # 初始化特定实体管理器
        self._initialize_entity_managers()

        # 验证初始化
        self._validate_initialization()

        # 标记初始化完成
        self.__class__._initialized = True

        logger.info("数据库服务初始化成功")
    except Exception as e:
        logger.error(f"数据库服务初始化失败: {e}", exc_info=True)
        raise

def _initialize_repositories(self):
    """初始化所有实体仓库"""
    # 获取所有已注册实体类型
    entity_types = RepositoryRegistry.get_all_entity_types()

    for entity_type in entity_types:
        repo_class = RepositoryRegistry.get_repository_class(entity_type)
        if repo_class:
            try:
                # 创建仓库实例
                repo_instance = repo_class(self.session)
                # 保存到仓库映射
                self.repo_map[entity_type] = repo_instance
                # 创建属性访问器
                attr_name = f"{entity_type}_repo"
                setattr(self, attr_name, repo_instance)
                logger.debug(f"初始化仓库: {entity_type}")
            except Exception as e:
                logger.warning(f"初始化 {entity_type} 仓库失败: {e}")
```

### 3. 仓库基类改进

为所有实体类型创建统一的仓库基类，确保基本功能一致：

```python
class EntityRepository(Repository):
    """实体仓库基类，提供统一接口"""

    def __init__(self, session, model_class=None):
        # 如果未指定模型类，尝试自动推断
        if model_class is None:
            # 从类名推断模型类
            entity_type = self._get_entity_type_from_class_name()
            model_class = self._resolve_model_class(entity_type)

        super().__init__(session, model_class)

    def _get_entity_type_from_class_name(self):
        """从仓库类名推断实体类型"""
        class_name = self.__class__.__name__
        # 假设命名规范是XxxRepository
        if class_name.endswith('Repository'):
            entity_name = class_name[:-10].lower()
            return entity_name
        return None

    def _resolve_model_class(self, entity_type):
        """解析实体类型对应的模型类"""
        from src.db.utils.entity_mapping import get_model_class
        from src.db.utils.entity_mapping import map_entity_to_table

        table_name = map_entity_to_table(entity_type)
        model_class = get_model_class(table_name)

        if not model_class:
            raise ValueError(f"无法解析 {entity_type} 对应的模型类")

        return model_class
```

### 4. 实体管理器工厂

创建实体管理器工厂，统一管理各类实体管理器：

```python
class EntityManagerFactory:
    """实体管理器工厂，创建和管理各类实体管理器"""

    # 实体管理器类映射
    _managers = {
        "epic": EpicManager,
        "story": StoryManager,
        "task": TaskManager,
        # 可以添加其他实体管理器
        "rule": RuleManager,
        "workflow": WorkflowManager,
        "template": TemplateManager
    }

    @classmethod
    def create_manager(cls, entity_type, entity_manager, **kwargs):
        """创建实体管理器"""
        if entity_type not in cls._managers:
            raise ValueError(f"未知实体类型: {entity_type}")

        manager_class = cls._managers[entity_type]
        return manager_class(entity_manager, **kwargs)

    @classmethod
    def register_manager(cls, entity_type, manager_class):
        """注册新的实体管理器类"""
        cls._managers[entity_type] = manager_class
```

## 四、实体类型优化

### 1. 实体类型分级管理

将实体类型分为核心实体和扩展实体，便于分阶段实现：

```python
# 定义实体类型级别
ENTITY_LEVELS = {
    # 核心业务实体，优先实现
    "CORE": ["epic", "story", "task"],

    # 支撑实体，次优先级
    "SUPPORT": ["label", "comment", "template"],

    # 系统实体，按需实现
    "SYSTEM": ["rule", "workflow"]
}

# 实体类型状态
ENTITY_STATUS = {
    # 已完全实现
    "epic": "IMPLEMENTED",
    "story": "IMPLEMENTED",
    "task": "IMPLEMENTED",

    # 部分实现
    "label": "PARTIAL",
    "template": "PARTIAL",

    # 待实现
    "rule": "PLANNED",
    "workflow": "PLANNED",
    "comment": "PLANNED"
}
```

### 2. 实体模型接口标准化

确保所有实体模型类都实现统一接口：

```python
class EntityModel:
    """实体模型接口，所有实体模型类都应实现这些方法"""

    @classmethod
    def from_dict(cls, data):
        """从字典创建实体"""
        raise NotImplementedError

    def to_dict(self):
        """转换为字典"""
        raise NotImplementedError

    @classmethod
    def get_schema(cls):
        """获取模型结构定义"""
        raise NotImplementedError
```

## 五、具体实现计划

### 第一阶段：完善现有实体

1. **实现仓库类**：
   为所有在`entity_mapping.py`中定义的实体类型实现仓库类

```python
class RuleRepository(EntityRepository):
    """规则仓库类"""

    def __init__(self, session):
        # 将在基类中自动解析模型类
        super().__init__(session)

    # 可以添加特定规则的方法
    def get_rules_by_category(self, category):
        """获取指定分类的规则"""
        return self.filter(category=category)

    def get_active_rules(self):
        """获取所有激活状态的规则"""
        return self.filter(is_active=True)
```

2. **添加模型类**：
   确保所有实体类型都有对应的模型类定义，例如Rule模型：

```python
class Rule(Base):
    """规则数据库模型"""

    __tablename__ = "rules"

    id = Column(String(50), primary_key=True, default=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)

    def __init__(self, **kwargs):
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"rule_{uuid.uuid4().hex[:8]}"

        super().__init__(**kwargs)

        # 补充默认值
        if getattr(self, "created_at", None) is None:
            self.created_at = datetime.now().isoformat()
        if getattr(self, "updated_at", None) is None:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
```

### 第二阶段：添加专用管理器

为需要特殊处理的实体类型添加专用管理器：

```python
class RuleManager:
    """规则管理器，处理规则特有的逻辑"""

    def __init__(self, entity_manager):
        self.entity_manager = entity_manager

    def get_rule(self, rule_id):
        """获取规则"""
        return self.entity_manager.get_entity("rule", rule_id)

    def list_rules(self):
        """获取所有规则"""
        return self.entity_manager.get_entities("rule")

    def create_rule(self, data):
        """创建规则"""
        return self.entity_manager.create_entity("rule", data)

    def update_rule(self, rule_id, data):
        """更新规则"""
        return self.entity_manager.update_entity("rule", rule_id, data)

    def delete_rule(self, rule_id):
        """删除规则"""
        return self.entity_manager.delete_entity("rule", rule_id)

    # 添加特有方法
    def apply_rule(self, rule_id, context):
        """应用规则到指定上下文"""
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        # 规则应用逻辑
        # ...

        return True
```

### 第三阶段：API扩展与统一

为DatabaseService添加新实体类型的便捷方法：

```python
# 规则相关方法
def get_rule(self, rule_id: str) -> Dict[str, Any]:
    """获取规则

    Args:
        rule_id: 规则ID

    Returns:
        规则数据
    """
    return self.rule_manager.get_rule(rule_id)

def list_rules(self) -> List[Dict[str, Any]]:
    """获取所有规则

    Returns:
        规则列表
    """
    return self.rule_manager.list_rules()

def create_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """创建规则

    Args:
        data: 规则数据

    Returns:
        创建的规则
    """
    return self.rule_manager.create_rule(data)

def update_rule(self, rule_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """更新规则

    Args:
        rule_id: 规则ID
        data: 更新数据

    Returns:
        更新后的规则
    """
    return self.rule_manager.update_rule(rule_id, data)

def delete_rule(self, rule_id: str) -> bool:
    """删除规则

    Args:
        rule_id: 规则ID

    Returns:
        是否成功
    """
    return self.rule_manager.delete_rule(rule_id)
```

## 六、统一CLI接口

为确保所有实体类型都能通过CLI操作，统一CLI接口设计：

```python
# CLI 命令示例
@cli.command()
@click.option("--id", help="实体ID")
@click.option("--type", help="实体类型", required=True)
def get(id, type):
    """获取实体"""
    db = get_db_service()
    entity = db.get_entity(type, id)
    if entity:
        click.echo(json.dumps(entity, indent=2))
    else:
        click.echo(f"未找到 {type} 实体，ID: {id}")

@cli.command()
@click.option("--type", help="实体类型", required=True)
def list(type):
    """列出实体"""
    db = get_db_service()
    entities = db.get_entities(type)
    click.echo(json.dumps(entities, indent=2))

@cli.command()
@click.option("--type", help="实体类型", required=True)
@click.option("--data", help="实体数据(JSON)", required=True)
def create(type, data):
    """创建实体"""
    db = get_db_service()
    try:
        data_dict = json.loads(data)
        entity = db.create_entity(type, data_dict)
        click.echo(f"成功创建 {type} 实体，ID: {entity['id']}")
    except Exception as e:
        click.echo(f"创建 {type} 实体失败: {str(e)}")
```

## 七、实体管理权限与验证

添加实体操作的权限控制和数据验证：

```python
class EntityValidator:
    """实体数据验证器"""

    @staticmethod
    def validate(entity_type, data, action="create"):
        """验证实体数据

        Args:
            entity_type: 实体类型
            data: 实体数据
            action: 操作类型（create, update）

        Returns:
            (bool, str): (是否有效, 错误信息)
        """
        # 基本字段检查
        if action == "create":
            if entity_type == "task" and not data.get("title"):
                return False, "任务标题不能为空"

            if entity_type == "epic" and not data.get("title"):
                return False, "Epic标题不能为空"

            if entity_type == "rule" and not data.get("name"):
                return False, "规则名称不能为空"

        # 关系验证
        if entity_type == "task" and data.get("story_id"):
            # 验证story存在
            # ...
            pass

        return True, ""
```

## 八、事务与并发控制

添加事务和并发处理支持：

```python
class DatabaseService:
    # 其他方法...

    def transaction(self):
        """创建事务上下文管理器"""
        return TransactionContext(self.session)

    def batch_create(self, entity_type, data_list):
        """批量创建实体

        Args:
            entity_type: 实体类型
            data_list: 实体数据列表

        Returns:
            创建的实体列表
        """
        results = []

        with self.transaction():
            for data in data_list:
                entity = self.create_entity(entity_type, data)
                results.append(entity)

        return results

# 事务上下文管理器
class TransactionContext:
    """事务上下文管理器"""

    def __init__(self, session):
        self.session = session

    def __enter__(self):
        # 事务已经开始
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 发生异常，回滚事务
            self.session.rollback()
            return False
        else:
            # 没有异常，提交事务
            self.session.commit()
            return True
```

## 九、总结与建议

1. **实施路径**：
   - 先完善`entity_mapping.py`，确保所有实体类型定义准确
   - 实现所有实体类型的模型类
   - 为所有实体类型创建仓库类
   - 逐步添加专用管理器
   - 统一CLI接口

2. **优先级**：
   - 核心实体(epic, story, task)已实现完整管理
   - 支持实体(label, template)优先补充实现
   - 系统实体(rule, workflow)在基础架构稳定后实现

3. **质量保障**：
   - 添加单元测试，验证仓库基本功能
   - 添加集成测试，确保实体关系正确
   - 对新增API先实现最小可行版本，再逐步完善

4. **注意事项**：
   - 保持向后兼容，避免破坏现有功能
   - 提供清晰的迁移路径，便于用户适应新API
   - 完善文档，明确各实体类型的用途和关系

此方案遵循VibeCopilot的渐进式开发策略和核心功能优先原则，提供了一个完整而统一的实体管理解决方案，让所有实体类型都能通过通用和专用API进行操作。
