# 模板系统使用指南

本目录包含VibeCopilot的模板系统，提供模板的存储、加载和使用功能。

## 目录结构

```
src/templates/
├── models/            # 模板数据模型（重定向）
├── repositories/      # 模板存储仓库
└── services/          # 模板处理服务
```

## 模型使用

模板系统中的模型已迁移到主模型目录 `src/models`。为了向后兼容，原有导入路径仍然可用，但建议使用新路径。

**推荐用法**:
```python
from src.models.template import Template, TemplateVariable
from src.models.rule import Rule
```

**原兼容用法**:
```python
from src.templates.models.template import Template, TemplateVariable
from src.templates.models.rule import Rule
```

## 模板仓库

模板仓库提供统一的接口来存储和检索模板，支持文件系统和数据库两种实现方式。

### 基本用法

```python
from src.templates.repositories import (
    FileSystemTemplateRepository,
    SQLTemplateRepositoryAdapter
)
from src.db.repositories.template_repository import TemplateRepository as SQLTemplateRepository
from src.db.session import get_session

# 使用文件系统存储
fs_repo = FileSystemTemplateRepository(storage_dir="./templates")

# 使用数据库存储
session = get_session()
sql_repo = SQLTemplateRepository(session)
db_repo = SQLTemplateRepositoryAdapter(sql_repo)

# 获取模板
template = db_repo.get_template("template-id")

# 搜索模板
results = db_repo.search_templates(query="关键词", tags=["标签1", "标签2"])
```

## 最佳实践

1. 直接使用 `src.models` 目录下的模型类
2. 对于模板存储，优先使用数据库实现 (`SQLTemplateRepositoryAdapter`)
3. 文件系统实现主要用于离线使用或导入/导出场景

## 未来计划

未来版本中，`src/templates/models` 目录将被移除，所有模型类将只存在于 `src/models` 目录。请尽快迁移到新的导入路径。
