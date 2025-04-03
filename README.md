# VibeCopilot

智能协作开发助手，让开发流程更高效自然。

## 数据库统一

VibeCopilot现在使用统一的SQLite数据库，简化了数据访问和管理。

### 使用方法

```python
from src.db.service import DatabaseService

# 创建数据库服务实例
db_service = DatabaseService()

# 使用高级API
epics = db_service.list_epics()
templates = db_service.search_templates(query="用户界面")
```

### 数据迁移

如果您之前使用的是分离的数据库系统，可以使用迁移工具将数据迁移到新的统一数据库：

```bash
# 检查迁移状态
python -m src.cli.main db-migrate --action=check

# 执行数据迁移（先测试，不实际修改数据库）
python -m src.cli.main db-migrate --action=migrate --dry_run=true

# 执行实际迁移
python -m src.cli.main db-migrate --action=migrate
```

## 配置

数据库配置位于`src/core/config.py`中：

```python
"database": {
    "path": ".ai/vibecopilot.db",
    "type": "sqlite",
    "debug": False,
}
```

您可以通过环境变量`VIBECOPILOT_DB_PATH`覆盖默认路径。