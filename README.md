# VibeCopilot

智能协作开发助手，让开发流程更高效自然。

## 数据库系统

VibeCopilot使用统一的SQLite数据库，简化了数据访问和管理。

### 使用方法

```python
from src.db.service import DatabaseService

# 创建数据库服务实例
db_service = DatabaseService()

# 使用高级API
epics = db_service.list_epics()
templates = db_service.search_templates(query="用户界面")
```

### 命令行操作

可以使用命令行工具管理数据库：

```bash
# 初始化数据库
python -m src.cli.main db --action=init

# 查询数据
python -m src.cli.main db --action=query --type=epic
python -m src.cli.main db --action=query --type=task --id=task-001

# 搜索模板
python -m src.cli.main db --action=query --type=template --query="用户界面" --tags="前端,组件"
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
