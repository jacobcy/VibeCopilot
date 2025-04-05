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

## GitHub集成

VibeCopilot提供与GitHub的深度集成，支持项目管理、路线图同步和开发协作。

### 主要功能

- **项目管理**：同步GitHub Projects与本地任务
- **路线图同步**：将本地路线图发布到GitHub项目
- **开发协作**：自动化工作流、议题模板和CI集成

### 使用方法

```python
from scripts.github_project.api.github_client import GitHubClient
from scripts.github_project.projects.main import ProjectManager

# 初始化GitHub客户端
client = GitHubClient(token="your_github_token")

# 项目管理
project_manager = ProjectManager(client)
project = project_manager.get_project("username/repo", "Project Name")

# 导入路线图
from scripts.github_project.projects.roadmap_processor import RoadmapProcessor
processor = RoadmapProcessor()
processor.import_from_yaml(".ai/roadmap/current.yaml")
processor.sync_to_github(client, "username/repo")
```

### 命令行操作

```bash
# 查看GitHub项目
python -m src.github.projects.main list --repo=username/repo

# 同步路线图
python -m src.github.roadmap.cli sync --source=.ai/roadmap/current.yaml --repo=username/repo
```

配置需要在环境变量中设置GitHub token：
```bash
export GITHUB_TOKEN=your_personal_access_token
```
