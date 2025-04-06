# 路线图模块清理计划

本文档提供了路线图模块代码清理的详细计划，目标是简化架构，只保留以SQLite作为主要数据源的相关功能。

## 当前问题

当前的路线图模块存在以下问题：

1. 多种数据源和转换路径（SQLite、YAML、Markdown、GitHub）导致复杂度过高
2. 旧的代码依赖Markdown和YAML作为中间数据源，逻辑过时
3. 同步逻辑散布在多个地方，职责不清晰
4. 部分代码位置不合理（如`DataSynchronizer`在临时目录）

## 目标架构

我们的目标是简化架构：

1. **SQLite作为唯一主要数据源**
2. **只保留三种同步路径**：
   - SQLite导出到YAML
   - YAML导入到SQLite
   - SQLite与GitHub服务器同步

## 需要清理的组件

1. `adapters/roadmap_sync/converter/` - YAML和Markdown转换工具
2. `adapters/roadmap_sync/markdown_parser.py` - Markdown解析逻辑
3. `adapters/roadmap_sync/connector.py` - 旧的连接器实现
4. `adapters/github_project/roadmap/generator.py` - 简化，只保留必要部分
5. `src/services/roadmap_service.py` - 移除Markdown相关逻辑

## 实施计划

### 1. 创建新的数据同步模块

1. 在`src/db/`目录下创建`sync.py`文件
2. 从`temp/roadmap.bak/sync.py`提取以下核心功能：
   - `sync_to_roadmap_yaml` - 数据库导出到YAML
   - `sync_from_roadmap_yaml` - YAML导入到数据库
   - GitHub同步相关方法
3. 实现一个精简版的`DataSynchronizer`类

```python
"""
数据库同步模块

提供数据库与YAML和GitHub之间的同步功能。
"""

import os
import logging
from typing import Any, Dict, Optional, Tuple

import yaml

from .service import DatabaseService

logger = logging.getLogger(__name__)

class DataSynchronizer:
    """数据同步器，负责数据库、YAML文件和GitHub之间的同步"""

    def __init__(self, db_service: DatabaseService, project_root: Optional[str] = None):
        """初始化同步器"""
        self.db = db_service
        self.project_root = project_root or os.environ.get("PROJECT_ROOT", os.getcwd())
        self.ai_dir = os.path.join(self.project_root, ".ai")

    def sync_to_roadmap_yaml(self, output_path: Optional[str] = None) -> str:
        """将数据库数据同步到roadmap.yaml"""
        # 导出数据
        roadmap_data = self.db.export_to_yaml()

        # 默认输出路径
        if not output_path:
            output_path = os.path.join(self.ai_dir, "roadmap", "current.yaml")

        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 写入YAML文件
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(roadmap_data, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"数据已同步到YAML: {output_path}")
        return output_path

    def sync_from_roadmap_yaml(self, yaml_path: Optional[str] = None) -> Tuple[int, int, int]:
        """从roadmap.yaml同步数据到数据库"""
        # 默认YAML路径
        if not yaml_path:
            yaml_path = os.path.join(self.ai_dir, "roadmap", "current.yaml")

        # 检查文件是否存在
        if not os.path.exists(yaml_path):
            logger.error(f"YAML文件不存在: {yaml_path}")
            return 0, 0, 0

        # 读取YAML文件
        with open(yaml_path, "r", encoding="utf-8") as f:
            roadmap_data = yaml.safe_load(f)

        # 导入数据
        result = self.db.import_from_yaml(roadmap_data)

        logger.info(f"从YAML导入数据完成: {result[0]}个Epic, {result[1]}个Story, {result[2]}个Task")
        return result

    def sync_to_github(self) -> Dict[str, Any]:
        """同步数据到GitHub"""
        # 集成现有GitHub同步逻辑
        # 从adapters/roadmap_sync/db_connector.py移植必要代码

    def sync_from_github(self) -> Dict[str, Any]:
        """从GitHub同步数据"""
        # 集成现有GitHub同步逻辑
        # 从adapters/roadmap_sync/db_connector.py移植必要代码
```

### 2. 更新服务层代码

修改`src/services/roadmap_service.py`：

1. 移除所有Markdown相关逻辑
2. 使用新的`DataSynchronizer`类
3. 简化`sync_roadmap`方法

```python
def sync_roadmap(self, direction: str = "to-github") -> Dict[str, Any]:
    """同步路线图数据

    Args:
        direction: 同步方向 (to-github, from-github)

    Returns:
        Dict[str, Any]: 同步结果
    """
    # 检查GitHub配置
    if not self.github_owner or not self.github_repo:
        raise ValueError("缺少GitHub配置，请设置GITHUB_OWNER和GITHUB_REPO环境变量")

    # 初始化数据同步器
    from src.db.sync import DataSynchronizer
    from src.db.service import DatabaseService

    db_service = DatabaseService()
    synchronizer = DataSynchronizer(db_service)

    if direction == "to-github":
        # 从数据库同步到GitHub
        result = synchronizer.sync_to_github()

        return {
            "direction": direction,
            "synced": True,
            "created": result.get("created", 0),
            "updated": result.get("updated", 0),
            "message": f"已向GitHub同步数据"
        }

    elif direction == "from-github":
        # 从GitHub同步到数据库
        result = synchronizer.sync_from_github()

        return {
            "direction": direction,
            "synced": True,
            "message": f"已从GitHub同步数据"
        }
    else:
        raise ValueError(f"不支持的同步方向: {direction}")
```

### 3. 更新命令实现

修改`src/cli/commands/roadmap/sync_command.py`以反映新架构：

```python
def execute(self, parsed_args: Dict) -> None:
    """执行命令"""
    from src.db.sync import DataSynchronizer
    from src.db.service import DatabaseService

    # 初始化所需服务
    db_service = DatabaseService()
    synchronizer = DataSynchronizer(db_service)

    try:
        # 显示执行中消息
        direction = parsed_args.get("direction")
        if direction == "to-github":
            print("正在推送数据库数据到GitHub...")
            result = synchronizer.sync_to_github()

            # 输出结果
            if result.get("success", False):
                print(f"同步成功: {result.get('message')}")
                print(f"已创建: {result.get('created', 0)} 条目")
                print(f"已更新: {result.get('updated', 0)} 条目")
            else:
                print(f"同步失败: {result.get('error', '未知错误')}")

        else:  # from-github
            print("正在从GitHub拉取数据...")
            result = synchronizer.sync_from_github()

            # 输出结果
            if result.get("success", False):
                print(f"同步成功: {result.get('message')}")
                print(f"已导入: Epic {result.get('epics', 0)}, Story {result.get('stories', 0)}, Task {result.get('tasks', 0)}")
            else:
                print(f"同步失败: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"错误: {str(e)}")
```

### 4. 要删除的文件和目录

1. `adapters/roadmap_sync/converter/` - 整个目录
2. `adapters/roadmap_sync/markdown_parser.py`
3. `adapters/roadmap_sync/connector.py` - 或大幅简化

### 5. 测试计划

1. 测试数据库导出到YAML:
   ```python
   from src.db.sync import DataSynchronizer
   from src.db.service import DatabaseService

   db = DatabaseService()
   sync = DataSynchronizer(db)
   yaml_path = sync.sync_to_roadmap_yaml()
   print(f"已导出到: {yaml_path}")
   ```

2. 测试YAML导入到数据库:
   ```python
   from src.db.sync import DataSynchronizer
   from src.db.service import DatabaseService

   db = DatabaseService()
   sync = DataSynchronizer(db)
   result = sync.sync_from_roadmap_yaml("path/to/roadmap.yaml")
   print(f"已导入: Epic {result[0]}, Story {result[1]}, Task {result[2]}")
   ```

3. 测试GitHub同步功能:
   ```python
   from src.db.sync import DataSynchronizer
   from src.db.service import DatabaseService

   db = DatabaseService()
   sync = DataSynchronizer(db)

   # 测试向GitHub同步
   result = sync.sync_to_github()
   print(f"已同步到GitHub: {result}")

   # 测试从GitHub同步
   result = sync.sync_from_github()
   print(f"已从GitHub同步: {result}")
   ```

## 总结

通过这个计划，我们将大幅简化路线图模块架构，只保留以SQLite为中心的核心功能，消除过时的多余转换逻辑，提高代码可维护性。主要成果将是：

1. 更加清晰的数据流路径
2. 简化的同步机制
3. 更易于理解和维护的代码结构
4. 删除大量过时代码
