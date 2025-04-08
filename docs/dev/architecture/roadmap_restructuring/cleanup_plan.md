# GitHub Roadmap模块清理计划

本文档列出了需要删除或替换的文件，以及替换后的新文件。在执行之前，请确保项目已备份。

## 文件替换计划

| 原始文件 | 新文件 | 说明 |
|---------|-------|------|
| `/adapters/roadmap_sync/connector.py` | `/adapters/roadmap_sync/connector.py.new` | 移除了GitHub相关功能，专注于文件转换 |
| `/src/roadmap/sync.py` | `/src/roadmap/sync.py.new` | 更新以使用新的模块结构 |

## 文件删除计划

以下文件应当删除，因为它们的功能已经被整合到其他模块中：

1. `/adapters/projects/main.py` - 功能已迁移到github_project模块
2. `/adapters/projects/roadmap.py` - 已创建兼容性层，实际功能已迁移
3. `/adapters/roadmap_sync/github_sync.py` - GitHub功能已迁移到github_project模块

## 需要检查引用的文件

以下文件可能包含对旧路径的引用，需要检查并更新：

1. `src/roadmap/cli.py` - 可能引用了sync.py中的旧功能
2. 任何导入了`adapters.projects.roadmap`的文件
3. 任何导入了`adapters.roadmap_sync.github_sync`的文件

## 实施步骤

1. **替换文件**

   ```bash
   # 替换connector.py
   mv /adapters/roadmap_sync/connector.py.new /adapters/roadmap_sync/connector.py
   # 替换sync.py
   mv /src/roadmap/sync.py.new /src/roadmap/sync.py
   ```

2. **删除重复文件**

   ```bash
   # 删除重复文件
   rm -f /adapters/projects/main.py
   rm -f /adapters/projects/roadmap.py
   rm -f /adapters/roadmap_sync/github_sync.py
   ```

3. **更新导入检查**

   使用grep命令查找可能需要更新的导入：

   ```bash
   # 检查对旧路径的引用
   grep -r "from adapters.projects.roadmap" .
   grep -r "from adapters.roadmap_sync.github_sync" .
   grep -r "import adapters.projects.roadmap" .
   grep -r "import adapters.roadmap_sync.github_sync" .
   ```

## 测试计划

1. **基本功能测试**

   测试YAML和Markdown转换功能：

   ```python
   from adapters.roadmap_sync.connector import RoadmapConnector

   connector = RoadmapConnector()
   # 测试Markdown到YAML转换
   result = connector.convert_markdown_to_yaml()
   print(result)
   # 测试YAML到Markdown转换
   result = connector.convert_yaml_to_markdown()
   print(result)
   ```

2. **GitHub集成测试**

   测试GitHub集成功能：

   ```python
   from adapters.github_project.roadmap.generator import RoadmapGenerator

   # 确保设置了环境变量：GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, GITHUB_PROJECT_NUMBER
   generator = RoadmapGenerator(
       owner="your-owner",
       repo="your-repo",
       project_number=1
   )
   result = generator.generate(["markdown"])
   print(result)
   ```

3. **数据库同步测试**

   测试数据库同步功能：

   ```python
   from src.db.service import DatabaseService
   from src.roadmap.sync import DataSynchronizer

   db = DatabaseService()
   sync = DataSynchronizer(db)

   # 测试从文件系统同步到数据库
   result = sync.sync_all_from_filesystem()
   print(result)

   # 测试同步到YAML
   yaml_path = sync.sync_to_roadmap_yaml()
   print(yaml_path)
   ```

## 兼容性注意事项

1. 我们已经创建了兼容性导入层，但可能仍有一些边缘情况未覆盖
2. 对于较旧的代码，可能需要更新导入路径
3. 如果发现兼容性问题，可以添加更多的导入重定向
