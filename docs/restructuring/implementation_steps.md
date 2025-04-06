# GitHub Roadmap模块重构实施指南

本文档提供了重构GitHub Roadmap模块的详细步骤。

## 重构步骤说明

### 步骤1: 建立新的目录结构

```
adapters/
├── github_project/
│   ├── api/              # 保持不变
│   ├── analysis/         # 保持不变
│   ├── roadmap/          # 新增目录，存放路线图相关功能
│   │   ├── __init__.py
│   │   ├── generator.py  # 从projects移过来
│   │   ├── processor.py  # 从projects移过来
│   │   └── importer.py   # 从projects移过来
│   ├── __init__.py
│   ├── cli.py
│   └── README.md         # 更新
│
├── roadmap_sync/
│   ├── converter/        # 保持不变，专注于YAML<->Markdown转换
│   ├── __init__.py
│   ├── markdown_parser.py
│   ├── models.py
│   ├── connector.py      # 简化版的connector，不包含GitHub功能
│   └── README.md         # 更新
│
└── projects/             # 仅保留兼容性导入
    └── __init__.py       # 仅包含兼容性导入代码
```

### 步骤2: `adapters/roadmap_sync` 重构

1. 移除GitHub相关功能，专注于文件转换
2. 更新connector.py，移除GitHub相关代码
3. 更新README.md

```python
# adapters/roadmap_sync/connector.py (简化版)
class RoadmapConnector:
    """简化的路线图连接器，专注于文件系统操作"""

    def __init__(self, stories_dir=None, roadmap_file=None):
        self.stories_dir = stories_dir or os.path.join(os.getcwd(), ".ai/stories")
        self.roadmap_file = roadmap_file or os.path.join(os.getcwd(), ".ai/roadmap/current.yaml")

    def convert_yaml_to_markdown(self):
        """将YAML转换为Markdown"""
        from .converter.yaml_to_markdown import YamlToMarkdownConverter
        converter = YamlToMarkdownConverter(self.roadmap_file, self.stories_dir)
        return converter.convert()

    def convert_markdown_to_yaml(self):
        """将Markdown转换为YAML"""
        from .converter.markdown_to_yaml import MarkdownToYamlConverter
        converter = MarkdownToYamlConverter(self.stories_dir, self.roadmap_file)
        return converter.convert()
```

### 步骤3: `adapters/github_project` 增强

1. 创建roadmap子目录
2. 移动projects模块中的相关文件
3. 更新API引用

```python
# adapters/github_project/roadmap/generator.py
"""
GitHub路线图生成器，从GitHub导入数据并生成路线图
"""
# 从adapters/projects/roadmap_generator.py移植过来的代码
# 更新导入路径

from ..api import GitHubClient

class RoadmapGenerator:
    """从GitHub生成路线图"""

    def __init__(self, github_client=None, config=None):
        self.github_client = github_client or GitHubClient()
        self.config = config or {}

    # 实现从projects/roadmap_generator.py移植的功能
```

### 步骤4: 创建兼容性层

为确保现有代码不会中断，创建兼容性导入:

```python
# adapters/projects/__init__.py
"""
兼容性导入，重定向到新的模块位置
"""
import warnings

warnings.warn(
    "adapters.projects 模块已被弃用，请使用 adapters.github_project 或 adapters.roadmap_sync",
    DeprecationWarning,
    stacklevel=2
)

# 导入重定向
from adapters.github_project.roadmap.generator import RoadmapGenerator
from adapters.github_project.roadmap.processor import RoadmapProcessor
from adapters.github_project.roadmap.importer import ImportRoadmap

# 旧版本类名称兼容
from adapters.roadmap_sync.connector import RoadmapConnector as ProjectConnector

__all__ = [
    "RoadmapGenerator",
    "RoadmapProcessor",
    "ImportRoadmap",
    "ProjectConnector"
]
```

### 步骤5: 更新 `src/roadmap` 模块

```python
# src/roadmap/sync.py (更新导入)
"""
数据库同步模块，提供与外部系统的集成
"""

# 更新导入
from adapters.roadmap_sync.connector import RoadmapConnector
from adapters.github_project.roadmap.processor import RoadmapProcessor

class DataSynchronizer:
    """数据同步器，负责数据库、文件系统和GitHub之间的同步"""

    def __init__(self, db_service, project_root=None):
        self.db = db_service
        self.project_root = project_root or os.getcwd()

        # 使用新的模块化组件
        self.roadmap_connector = RoadmapConnector(
            stories_dir=os.path.join(self.project_root, ".ai/stories"),
            roadmap_file=os.path.join(self.project_root, ".ai/roadmap/current.yaml")
        )
        self.github_processor = RoadmapProcessor()

    # 更新同步方法，利用新的模块化组件
```

### 步骤6: 测试每个组件

为每个主要功能创建测试用例:

```python
# tests/adapters/roadmap_sync/test_connector.py
def test_yaml_to_markdown_conversion():
    """测试YAML到Markdown的转换"""
    connector = RoadmapConnector(
        stories_dir="./tests/fixtures/stories",
        roadmap_file="./tests/fixtures/roadmap.yaml"
    )
    result = connector.convert_yaml_to_markdown()
    assert result["success"] == True
    # 检查生成的文件...

# tests/adapters/github_project/roadmap/test_generator.py
def test_roadmap_generation_from_github():
    """测试从GitHub生成路线图"""
    # 使用模拟的GitHub客户端
    mock_client = MockGitHubClient()
    generator = RoadmapGenerator(github_client=mock_client)
    result = generator.generate()
    assert "milestones" in result
    assert len(result["milestones"]) > 0
```

## 迁移指南

对于已经使用旧模块的代码，提供以下迁移路径:

### 1. 对于使用`adapters/projects`的代码

```python
# 旧代码
from adapters.projects import RoadmapGenerator

# 新代码
from adapters.github_project.roadmap.generator import RoadmapGenerator
```

### 2. 对于使用`adapters/roadmap_sync`中GitHub功能的代码

```python
# 旧代码
from adapters.roadmap_sync.github_sync import GitHubSynchronizer

# 新代码
from adapters.github_project.sync import GitHubSynchronizer
```

### 3. 对于直接使用`src/roadmap`的代码

这部分代码大部分可以不变，因为我们会保持向后兼容性。

## 风险和缓解措施

### 风险1: 现有代码可能依赖于被移动的模块

**缓解措施**: 创建兼容性导入，确保旧的导入路径仍然有效。

### 风险2: 功能可能在重构过程中丢失

**缓解措施**: 创建全面的测试用例，确保所有功能都被保留。

### 风险3: 文档可能过时

**缓解措施**: 更新所有README和用户指南，确保它们反映新的结构。

## 时间估计

- **步骤1-2**: 1工作日
- **步骤3-4**: 1工作日
- **步骤5**: 0.5工作日
- **步骤6**: 1工作日
- **文档更新**: 0.5工作日

总计: 约4个工作日完成整个重构过程。
