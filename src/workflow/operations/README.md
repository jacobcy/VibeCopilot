# 工作流操作模块

此目录包含工作流操作的实现，已按功能拆分为多个文件以提高可维护性。

## 文件结构

- `__init__.py` - 包初始化，导出所有公共函数
- `base.py` - 基础工具函数，如目录路径和文件路径获取
- `list.py` - 列出工作流的函数
- `get.py` - 获取工作流的各种函数
- `create.py` - 创建工作流的函数
- `update.py` - 更新工作流的函数
- `delete.py` - 删除工作流的函数
- `validate.py` - 验证工作流的函数
- `sync.py` - 与数据库同步工作流的函数

## 替代 workflow_operations.py

此目录的文件替代了原来的 `workflow_operations.py` 单文件实现，将其拆分为更小、更易于维护的模块。
所有功能与原来保持一致，只是结构更加清晰和模块化。

## 使用方法

推荐从包级别导入需要的函数：

```python
from src.workflow.operations import (
    list_workflows,
    get_workflow,
    create_workflow,
    # ...其他需要的函数
)
```

也可以从特定模块导入：

```python
from src.workflow.operations.get import get_workflow_by_name
from src.workflow.operations.create import create_workflow
```
