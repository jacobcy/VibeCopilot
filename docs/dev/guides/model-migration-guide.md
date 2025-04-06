# 模型统一迁移指南

本文档提供了将原有多个模型实现迁移到统一模型的步骤和注意事项。

## 目标

- 统一规则和模板的数据模型定义
- 减少代码重复，提高维护性
- 确保各模块使用一致的数据结构
- 简化数据转换逻辑

## 新的模型结构

```
src/models/
  ├── __init__.py         # 导出所有模型
  ├── base.py             # 基础类型和共享枚举
  ├── rule.py             # 统一的规则模型
  ├── template.py         # 统一的模板模型
  └── db/                 # 数据库模型
      ├── __init__.py     # 导出数据库模型
      ├── base.py         # SQLAlchemy Base定义
      ├── rule.py         # 规则数据库模型
      └── template.py     # 模板数据库模型
```

## 迁移步骤

### 1. 更新导入路径

| 旧路径 | 新路径 |
|-------|--------|
| `from src.rule_engine.models.rule import *` | `from src.models.rule import *` |
| `from src.rule_engine.models.template import *` | `from src.models.template import *` |
| `from src.templates.models.rule import *` | `from src.models.rule import *` |
| `from src.templates.models.template import *` | `from src.models.template import *` |
| `from src.db.models import Base` | `from src.models.db import Base` |
| `from src.db.models.template import *` | `from src.models.db.template import *` |

### 2. 更新数据库模型引用

将所有使用旧数据库模型的代码更新为使用新的数据库模型：

```python
# 旧代码
from src.db.models.template import Template

# 新代码
from src.models.db import Template
```

### 3. 更新模型转换逻辑

新的数据库模型已经提供了与Pydantic模型的互相转换方法：

```python
# 数据库模型转Pydantic模型
pydantic_rule = db_rule.to_pydantic()

# Pydantic模型转数据库模型
db_rule = Rule.from_pydantic(pydantic_rule)
```

### 4. 处理RuleType和TemplateVariableType

使用统一的枚举类型：

```python
# 旧代码
from src.rule_engine.models.rule import RuleType

# 新代码
from src.models.base import RuleType
```

## 需要更新的模块

以下模块可能需要更新导入和模型使用:

1. `src/rule_engine/` - 规则引擎相关代码
2. `src/templates/` - 模板处理相关代码
3. `src/adapters/rule_parser/` - 规则解析器
4. `src/db/` - 数据库操作相关代码

## 测试检查点

在迁移后，请确保通过以下测试：

1. 规则的创建、读取、更新和删除功能正常
2. 模板的解析、渲染和应用功能正常
3. 规则解析器能够正确地将Markdown规则解析为JSON
4. 所有现有的单元测试能够通过

## 注意事项

- 新模型可能增加了一些原有模型中不存在的字段，确保处理这些差异
- 尽量使用类型提示和IDE自动完成功能来快速发现导入错误
- 迁移时遵循增量更新的原则，逐模块进行测试
