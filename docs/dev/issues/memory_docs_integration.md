# Memory 与 Docs Engine 集成方案

## 背景

VibeCopilot 目前有两个相关但独立的系统：

1. **Docs Engine**：负责文档的解析、块级管理和链接处理
2. **Memory**：提供统一的知识存储和检索功能

当前，Docs Engine 使用自己的存储系统（基于 SQLAlchemy），而不是利用 Memory 模块的存储能力。这导致了存储分散、功能重复和检索不统一的问题。

## 目标

建立 Docs Engine 和 Memory 之间的集成，使 Memory 成为文档内容的统一存储层，而 Docs Engine 专注于文档的解析和管理工具功能。

## 架构设计

### 职责划分

- **Docs Engine**：
  - 文档解析和块级内容提取
  - 文档格式转换
  - 链接处理
  - 模板管理
  - 命令行工具

- **Memory**：
  - 文档内容的存储
  - 文档检索（包括语义搜索）
  - 知识图谱构建
  - 与 VibeCopilot 的集成

### 架构图

```
┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │
│   Docs Engine   │─────▶│     Memory      │
│  (解析和管理工具)  │      │  (统一存储层)   │
│                 │      │                 │
└─────────────────┘      └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │                 │
                         │  VibeCopilot    │
                         │  (应用层)        │
                         │                 │
                         └─────────────────┘
```

## 实现方案

### 1. 创建 Memory 适配器

在 Docs Engine 中创建一个适配器，用于与 Memory 模块交互。这个适配器将负责将文档数据转换为 Memory 可以理解的格式，并调用 Memory 的 API 进行存储和检索。

```python
# src/docs_engine/memory_adapter.py

"""
Memory 适配器

提供 Docs Engine 与 Memory 系统的集成接口
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MemoryAdapter:
    """Memory 适配器"""

    def __init__(self):
        """初始化适配器"""
        # 导入 Memory 模块
        from src.memory.entity_manager import EntityManager
        from src.memory.relation_manager import RelationManager

        self.entity_manager = EntityManager()
        self.relation_manager = RelationManager()

    async def store_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """存储文档到 Memory 系统

        Args:
            doc_data: 文档数据

        Returns:
            存储结果
        """
        # 将文档数据转换为 Memory 可以理解的格式
        # 调用 Memory API 进行存储
        # 返回存储结果
        pass

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """从 Memory 系统获取文档

        Args:
            doc_id: 文档 ID

        Returns:
            文档数据
        """
        # 调用 Memory API 获取文档
        # 将结果转换为 Docs Engine 可以理解的格式
        pass

    async def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """搜索文档

        Args:
            query: 搜索查询

        Returns:
            匹配的文档列表
        """
        # 调用 Memory API 进行搜索
        # 将结果转换为 Docs Engine 可以理解的格式
        pass
```

### 2. 修改 Docs Engine 接口

更新 Docs Engine 的接口，使其使用 Memory 适配器进行存储操作。

```python
# src/docs_engine/docs_engine.py

"""
文档引擎接口模块
提供统一的文档引擎接口，使用 src.parsing 解析文档文件，并提供格式转换功能
"""

import logging
import os
from typing import Any, Dict, List, Optional

from src.docs_engine.engine import create_document_engine
from src.docs_engine.memory_adapter import MemoryAdapter
from src.parsing import create_parser

logger = logging.getLogger(__name__)
memory_adapter = MemoryAdapter()

async def parse_document_file(file_path: str, parser_type: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """解析文档文件并存储到 Memory 系统

    使用统一的 parsing 接口解析文档文件，并将结果存储到 Memory 系统

    Args:
        file_path: 文档文件路径
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的文档结构
    """
    # 解析文档
    # 存储到 Memory 系统
    # 返回结果
    pass

# 其他函数也类似修改...
```

### 3. 更新 CLI 工具

更新 Docs Engine 的命令行工具，使其支持与 Memory 的集成。

```python
# src/docs_engine/cli.py

"""
文档引擎命令行工具

提供命令行接口，用于文档解析、转换和管理。
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from src.docs_engine.docs_engine import (
    convert_document_links,
    create_document_from_template,
    extract_document_blocks,
    import_document_to_db,
    parse_document_file,
    search_documents,  # 新增
)

# 添加搜索命令
# 更新其他命令以支持 Memory 集成
```

## 迁移计划

### 阶段一：准备工作（2周）

1. 创建 Memory 适配器
2. 编写单元测试
3. 文档设计和规划

### 阶段二：并行运行（4周）

1. 修改 Docs Engine 接口，同时使用原有存储和 Memory 存储
2. 添加数据同步功能，确保两个系统的数据一致性
3. 添加新的 CLI 命令，如 `doc sync` 用于同步数据
4. 进行集成测试

### 阶段三：完全迁移（2周）

1. 将所有存储操作迁移到 Memory 模块
2. 弃用 Docs Engine 中的存储实现
3. 更新文档和测试
4. 性能测试和优化

## API 设计

### Memory 适配器 API

```python
# 存储文档
async def store_document(doc_data: Dict[str, Any]) -> Dict[str, Any]

# 获取文档
async def get_document(doc_id: str) -> Optional[Dict[str, Any]]

# 搜索文档
async def search_documents(query: str) -> List[Dict[str, Any]]

# 删除文档
async def delete_document(doc_id: str) -> bool

# 更新文档
async def update_document(doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]
```

### Docs Engine 公共 API

```python
# 解析文档文件
async def parse_document_file(file_path: str, parser_type: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]

# 解析文档内容
async def parse_document_content(content: str, context: str = "", parser_type: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]

# 提取文档块
async def extract_document_blocks(file_path: str) -> List[Dict[str, Any]]

# 导入文档到数据库
async def import_document_to_db(file_path: str) -> Dict[str, Any]

# 转换文档链接
def convert_document_links(content: str, from_format: str, to_format: str) -> str

# 创建文档从模板
def create_document_from_template(template: str, output_path: str, variables: Optional[Dict[str, Any]] = None) -> bool

# 搜索文档（新增）
async def search_documents(query: str) -> List[Dict[str, Any]]
```

## 注意事项

1. **异步支持**：Memory 模块可能使用异步 API，需要确保 Docs Engine 也支持异步操作
2. **兼容性**：确保现有功能在迁移过程中不受影响
3. **数据迁移**：需要设计数据迁移策略，确保现有数据能够平滑迁移到新系统
4. **错误处理**：完善错误处理机制，确保系统在各种情况下都能正常工作
5. **文档更新**：及时更新开发文档和用户文档

## 预期收益

1. **统一存储**：所有知识都存储在 Memory 系统中，便于统一管理和检索
2. **职责清晰**：Docs Engine 专注于文档处理工具功能，Memory 专注于知识存储
3. **功能增强**：通过 Memory 的高级功能，支持更强大的文档检索能力
4. **架构优化**：符合单一职责原则，减少代码重复
5. **维护简化**：只需维护一套存储系统，降低维护成本

## 结论

通过将 Docs Engine 与 Memory 集成，我们可以实现文档内容的统一存储和检索，同时保持各模块的职责清晰。这将提高系统的可维护性和可扩展性，并为 VibeCopilot 提供更强大的知识管理能力。
