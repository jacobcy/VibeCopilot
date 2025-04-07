# VibeCopilot 内容解析与数据存储统一方案

## 1. 背景与目标

VibeCopilot 项目处于demo阶段，目前有多个独立的内容解析和数据存储模块，包括：

- `content_parser` 模块：负责解析规则、文档和通用内容
- `rule_parser` 模块：专门用于解析规则文件
- `basic_memory` 模块：提供实体解析和向量存储功能
- 元数据存储：使用 SQLite 数据库通过 SQLAlchemy ORM 存储结构化数据
- 向量存储：目前使用外部 Basic Memory 提供的向量存储功能

由于项目处于demo阶段，没有大量生产数据需要迁移，我们可以直接重构代码，统一这些模块，减少代码重复，提高系统一致性和可维护性，快速实现高效的数据流转和集成。

## 2. 现状分析

### 2.1 内容解析系统

#### 2.1.1 Content Parser 模块

- 位置：`adapters/content_parser/`
- 设计模式：使用工厂模式创建不同类型的解析器
- 支持类型：规则解析、文档解析、通用内容解析
- 技术实现：主要基于 OpenAI 和 Ollama
- 关键功能：
  - 自动推断内容类型
  - 统一的文件、文本和目录解析接口
  - 错误处理和日志记录

#### 2.1.2 Rule Parser 模块

- 位置：`adapters/rule_parser/`
- 设计模式：同样使用工厂模式
- 关键功能：
  - 规则文件解析为结构化数据
  - 规则冲突检测
  - 命令行接口支持

#### 2.1.3 Basic Memory 解析器

- 位置：`adapters/basic_memory/parsers/`
- 技术实现：OpenAI、Ollama、Regex、LangChain
- 关键功能：
  - 实体和关系提取
  - 文档向量化
  - 语义搜索

### 2.2 数据存储系统

#### 2.2.1 SQLite 元数据数据库

- 位置：`src/db/`
- 技术实现：SQLAlchemy ORM
- 存储内容：文档、模板、工作流、史诗、故事、任务等结构化数据
- 架构特点：
  - 使用仓库模式
  - 完整的事务支持
  - 会话管理

#### 2.2.2 向量数据库

- 不再自己实现，直接使用Basic Memory提供的向量存储功能
- 通过MCP工具进行向量数据的存储和检索
- Basic Memory内部使用SQLite作为存储引擎

## 3. 统一架构设计

### 3.1 统一内容解析框架

```
src/
├── core/
│   └── parsing/
│       ├── __init__.py
│       ├── base_parser.py        # 抽象基础解析器
│       ├── parser_factory.py     # 统一工厂模式
│       ├── parsers/              # 具体解析器实现
│       │   ├── __init__.py
│       │   ├── openai_parser.py  # OpenAI实现
│       │   ├── ollama_parser.py  # Ollama实现
│       │   └── regex_parser.py   # 正则表达式解析器
│       └── processors/           # 内容处理器
│           ├── __init__.py
│           ├── rule_processor.py      # 规则处理
│           ├── document_processor.py  # 文档处理
│           └── entity_processor.py    # 实体处理
```

### 3.2 统一数据库架构

```
src/
├── db/
│   ├── __init__.py               # 数据库初始化和配置
│   ├── repository.py             # 基础仓库类
│   ├── session.py                # 会话管理
│   ├── service.py                # 服务层
│   ├── metadata/                 # SQLite 仓库
│   │   ├── __init__.py
│   │   ├── document_repo.py      # 文档仓库
│   │   ├── rule_repo.py          # 规则仓库
│   │   ├── entity_repo.py        # 实体仓库
│   │   └── template_repo.py      # 模板仓库
│   └── vector/                   # 向量数据库集成
│       ├── __init__.py
│       ├── memory_adapter.py     # Basic Memory 适配器
│       └── vector_store.py       # 向量存储抽象接口
```

### 3.3 统一内存管理系统

```
src/
├── memory/
│   ├── __init__.py
│   ├── sync_service.py           # 同步服务
│   ├── entity_manager.py         # 实体管理
│   ├── observation_manager.py    # 观察管理
│   └── relation_manager.py       # 关系管理
```

## 4. 实现计划

由于处于demo阶段，我们采用快速实现的方式，直接重构代码并测试，不考虑数据兼容问题。

### 4.1 第一阶段：统一解析逻辑

1. **目标**: 直接实现统一的解析框架
2. **具体任务**:
   - 在 `src/core/parsing` 中创建新的解析框架
   - 实现 `BaseParser` 抽象类和具体解析器
   - 实现特定类型的处理器 (规则、文档、实体)
   - 直接替换现有的解析器实现
   - 编写单元测试并验证功能

3. **计划时间**: 1周
4. **预期成果**:
   - 统一的解析器接口
   - 减少50%以上的代码重复

### 4.2 第二阶段：Basic Memory 集成

1. **目标**: 实现与Basic Memory的无缝集成
2. **具体任务**:
   - 实现Basic Memory适配器
   - 创建向量存储抽象接口，确保未来可替换性
   - 实现同步服务，负责将本地数据同步到Basic Memory
   - 设计GitActions工作流，自动触发同步
   - 创建测试用例并验证功能

3. **计划时间**: 1周
4. **预期成果**:
   - 与Basic Memory的完整集成
   - 自动化的数据同步
   - 保持命令行和Cursor Agent数据一致性

### 4.3 第三阶段：实现核心功能

1. **目标**: 直接实现最小化规则和引擎功能
2. **具体任务**:
   - 快速实现 `EntityManager`、`ObservationManager` 等核心组件
   - 利用Basic Memory API实现向量搜索功能
   - 自动化测试核心功能

3. **计划时间**: 1周
4. **预期成果**:
   - 最小可行产品的核心功能
   - 更高效的实现
   - 全面的测试用例

## 5. 关键代码示例

### 5.1 Basic Memory 适配器

```python
# src/db/vector/memory_adapter.py
from typing import List, Dict, Any, Optional

from basic_memory.mcp.async_client import client
from basic_memory.mcp.tools.write_note import write_note
from basic_memory.mcp.tools.search_notes import search_notes

from src.db.vector.vector_store import VectorStore
from src.core.config import get_config

class BasicMemoryAdapter(VectorStore):
    """Basic Memory 向量存储适配器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化Basic Memory适配器

        Args:
            config: 可选配置参数
        """
        self.config = config or get_config().get("basic_memory", {})
        self.default_folder = self.config.get("default_folder", "vibecopilot")
        self.default_tags = self.config.get("default_tags", "vibecopilot")

    async def store(self, texts: List[str], metadata: List[Dict[str, Any]], folder: Optional[str] = None) -> List[str]:
        """将文本存储到Basic Memory

        Args:
            texts: 要存储的文本内容列表
            metadata: 每个文本对应的元数据
            folder: 存储文件夹，如果为None则使用默认文件夹

        Returns:
            存储成功后返回的permalink列表
        """
        if len(texts) != len(metadata):
            raise ValueError("texts和metadata的长度必须相同")

        target_folder = folder or self.default_folder
        permalinks = []

        for i, text in enumerate(texts):
            meta = metadata[i]
            title = meta.get("title", f"VibeCopilot Content {i}")

            # 构建标签
            tags = meta.get("tags", self.default_tags)
            if isinstance(tags, list):
                tags = ",".join(tags)

            # 构建Markdown内容
            content = f"# {title}\n\n{text}\n\n"

            # 添加元数据部分
            content += "## 元数据\n"
            for key, value in meta.items():
                if key != "title" and key != "tags":
                    content += f"- **{key}**: {value}\n"

            # 存储到Basic Memory
            result = await write_note(
                title=title,
                content=content,
                folder=target_folder,
                tags=tags
            )

            # 解析结果获取permalink
            permalink = None
            for line in result.split("\n"):
                if line.startswith("permalink:"):
                    permalink = line.split(":", 1)[1].strip()
                    break

            if permalink:
                permalinks.append(permalink)

        return permalinks

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """使用Basic Memory搜索相关内容

        Args:
            query: 搜索查询
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        # 调用Basic Memory搜索
        results = await search_notes(
            query={"text": query},
            page_size=limit
        )

        # 转换结果格式
        formatted_results = []
        for result in results.results:
            formatted_result = {
                "content": result.content if hasattr(result, "content") else "",
                "title": result.title if hasattr(result, "title") else "",
                "permalink": result.permalink if hasattr(result, "permalink") else "",
                "score": result.score if hasattr(result, "score") else None,
                "metadata": {}
            }

            # 提取元数据
            if hasattr(result, "metadata") and result.metadata:
                formatted_result["metadata"] = result.metadata

            formatted_results.append(formatted_result)

        return formatted_results
```

### 5.2 向量存储抽象接口

```python
# src/db/vector/vector_store.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStore(ABC):
    """向量存储抽象接口，提供与不同向量数据库的兼容层"""

    @abstractmethod
    async def store(self, texts: List[str], metadata: List[Dict[str, Any]], folder: Optional[str] = None) -> List[str]:
        """存储文本到向量数据库

        Args:
            texts: 要存储的文本列表
            metadata: 与文本对应的元数据列表
            folder: 可选的存储文件夹

        Returns:
            存储成功后的标识符列表
        """
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文本

        Args:
            query: 搜索查询
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        pass
```

### 5.3 同步服务

```python
# src/memory/sync_service.py
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from src.parsing.parser_factory import create_parser
from src.db.metadata.rule_repo import RuleRepository
from src.db.metadata.document_repo import DocumentRepository
from src.db.vector.memory_adapter import BasicMemoryAdapter

class SyncService:
    """同步服务 - 负责将本地内容同步到Basic Memory"""

    def __init__(self):
        """初始化同步服务"""
        self.rule_repo = RuleRepository()
        self.document_repo = DocumentRepository()
        self.vector_store = BasicMemoryAdapter()
        self.rule_parser = create_parser("rule")
        self.document_parser = create_parser("document")

    async def sync_rules(self, rule_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """同步规则文件到Basic Memory

        Args:
            rule_files: 要同步的规则文件路径，如果为None则同步所有规则

        Returns:
            同步结果摘要
        """
        # 获取所有规则文件路径
        rules_dir = Path(".cursor/rules")
        files_to_sync = []

        if rule_files:
            # 同步指定文件
            for file_path in rule_files:
                path = Path(file_path)
                if path.exists() and path.suffix in [".mdc", ".md"]:
                    files_to_sync.append(path)
        else:
            # 同步所有规则文件
            for rule_file in rules_dir.rglob("*.mdc"):
                files_to_sync.append(rule_file)

        # 解析并同步规则文件
        texts = []
        metadata = []

        for file_path in files_to_sync:
            # 解析规则文件
            try:
                parse_result = self.rule_parser.parse_file(file_path)

                # 提取内容和元数据
                rule_id = file_path.stem
                rule_name = parse_result.get("name", rule_id)
                rule_content = str(file_path.read_text(encoding="utf-8"))

                # 准备向量存储
                texts.append(rule_content)
                metadata.append({
                    "title": f"Rule: {rule_name}",
                    "tags": "rule,vibecopilot",
                    "rule_id": rule_id,
                    "rule_type": parse_result.get("type", "unknown"),
                    "file_path": str(file_path),
                    "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
            except Exception as e:
                print(f"解析规则文件失败: {file_path} - {str(e)}")

        # 存储到Basic Memory
        if texts:
            permalinks = await self.vector_store.store(texts, metadata, folder="rules")
            return {
                "synced_count": len(permalinks),
                "total_count": len(files_to_sync),
                "permalinks": permalinks
            }
        else:
            return {
                "synced_count": 0,
                "total_count": len(files_to_sync),
                "permalinks": []
            }

    async def sync_documents(self, doc_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """同步文档文件到Basic Memory

        Args:
            doc_files: 要同步的文档文件路径，如果为None则同步所有文档

        Returns:
            同步结果摘要
        """
        # 获取所有文档文件路径
        docs_dir = Path("docs")
        files_to_sync = []

        if doc_files:
            # 同步指定文件
            for file_path in doc_files:
                path = Path(file_path)
                if path.exists() and path.suffix in [".md", ".mdx"]:
                    files_to_sync.append(path)
        else:
            # 同步所有文档文件
            for doc_file in docs_dir.rglob("*.md"):
                files_to_sync.append(doc_file)

            for doc_file in docs_dir.rglob("*.mdx"):
                files_to_sync.append(doc_file)

        # 解析并同步文档文件
        texts = []
        metadata = []

        for file_path in files_to_sync:
            # 解析文档文件
            try:
                doc_content = file_path.read_text(encoding="utf-8")

                # 提取标题
                title = file_path.stem.replace("-", " ").title()
                for line in doc_content.split("\n")[:10]:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                # 准备向量存储
                texts.append(doc_content)
                metadata.append({
                    "title": f"Document: {title}",
                    "tags": "documentation,vibecopilot",
                    "doc_path": str(file_path),
                    "doc_type": "markdown",
                    "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
            except Exception as e:
                print(f"解析文档文件失败: {file_path} - {str(e)}")

        # 存储到Basic Memory
        if texts:
            permalinks = await self.vector_store.store(texts, metadata, folder="documentation")
            return {
                "synced_count": len(permalinks),
                "total_count": len(files_to_sync),
                "permalinks": permalinks
            }
        else:
            return {
                "synced_count": 0,
                "total_count": len(files_to_sync),
                "permalinks": []
            }

    async def sync_all(self, changed_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """同步所有内容到Basic Memory

        Args:
            changed_files: 更改的文件列表，如果提供则只同步这些文件

        Returns:
            同步结果摘要
        """
        if changed_files:
            # 分类文件
            rule_files = []
            doc_files = []

            for file_path in changed_files:
                path = Path(file_path)
                if not path.exists():
                    continue

                if ".cursor/rules" in str(path) and path.suffix in [".mdc", ".md"]:
                    rule_files.append(file_path)
                elif "docs" in str(path) and path.suffix in [".md", ".mdx"]:
                    doc_files.append(file_path)

            # 同步更改的文件
            rule_result = await self.sync_rules(rule_files)
            doc_result = await self.sync_documents(doc_files)
        else:
            # 同步所有文件
            rule_result = await self.sync_rules()
            doc_result = await self.sync_documents()

        # 返回汇总结果
        return {
            "rules": rule_result,
            "documents": doc_result,
            "total_synced": rule_result.get("synced_count", 0) + doc_result.get("synced_count", 0)
        }
```

## 6. Git Actions 实现

为了自动化同步过程，我们将实现GitHub Actions工作流，在提交被推送到仓库时触发同步操作。

```yaml
# .github/workflows/sync-to-basic-memory.yml
name: Sync to Basic Memory

on:
  push:
    branches: [ main, dev ]
    paths:
      - 'docs/**/*.md'
      - 'docs/**/*.mdx'
      - '.cursor/rules/**/*.mdc'
      - '.cursor/rules/**/*.md'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # 获取完整历史以检测更改

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Get changed files
        id: changed-files
        run: |
          CHANGED_FILES=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }})
          echo "changed_files=$CHANGED_FILES" >> $GITHUB_OUTPUT

      - name: Sync to Basic Memory
        run: python -m src.scripts.sync_to_basic_memory --files "${{ steps.changed-files.outputs.changed_files }}"
        env:
          BASIC_MEMORY_HOME: ${{ secrets.BASIC_MEMORY_HOME }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

同步脚本 `src/scripts/sync_to_basic_memory.py` 的实现：

```python
#!/usr/bin/env python
"""同步规则和文档到 Basic Memory."""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List

from src.memory.sync_service import SyncService

async def main(file_paths: List[str]) -> None:
    """同步文件到Basic Memory."""
    print(f"开始同步文件到Basic Memory...")

    # 初始化同步服务
    sync_service = SyncService()

    # 同步文件
    result = await sync_service.sync_all(file_paths)

    # 打印结果
    print(f"\n同步完成!")
    print(f"规则：同步 {result['rules']['synced_count']} / {result['rules']['total_count']}")
    print(f"文档：同步 {result['documents']['synced_count']} / {result['documents']['total_count']}")
    print(f"总计：同步 {result['total_synced']} 个文件")

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="同步文件到Basic Memory")
    parser.add_argument("--files", type=str, help="要同步的文件路径列表，用空格分隔")
    args = parser.parse_args()

    # 解析文件列表
    file_paths = args.files.split() if args.files else []

    # 运行同步
    asyncio.run(main(file_paths))
```

## 7. 开发和测试策略

### 7.1 快速实现策略

**策略**:

- 采用过油票模式，只实现必要功能
- 不考虑兼容性，直接重构
- 不迁移现有数据，创建全新的结构
- 使用抽象接口确保未来可替换性

### 7.2 测试驱动开发

**策略**:

- 先编写测试用例，再实现功能
- 每实现一个功能点就进行测试
- 专注核心功能的单元测试
- 使用简单的集成测试验证组件间的交互

### 7.3 快速反馈循环

**策略**:

- 真实数据快速验证
- 实现一个功能点就运行测试
- 查找简单有效的实现方式
- 不过度设计和过早优化

## 8. 未来扩展

### 8.1 支持更多向量数据库

通过抽象接口支持其他向量数据库：

- Chroma
- Milvus
- Qdrant
- Pinecone

### 8.2 支持更多内容类型

- 代码解析器
- 图表解析器
- 音频转录解析器
- 视频内容解析器

### 8.3 高级特性

- 实时事件流处理
- 分布式向量查询
- 多向量索引支持
- 自定义相似度算法

## 9. 实施计划

下面是具体的实施计划，专注于demo阶段的快速实现：

### 第一周 (统一解析器)

- 周一：创建核心解析器抽象类和组件结构
- 周二：实现OpenAI和Ollama解析器
- 周三：实现类型处理器(规则、文档、实体)
- 周四：编写测试用例，并进行测试
- 周五：修复问题并完成可用版本

### 第二周 (Basic Memory 集成)

- 周一：实现向量存储抽象接口
- 周二：实现Basic Memory适配器
- 周三：实现同步服务
- 周四：设置GitHub Actions
- 周五：集成测试与完善

### 第三周 (核心功能)

- 周一：实现实体管理器
- 周二：实现观察管理器
- 周三：实现关系管理和查询
- 周四：综合测试所有功能
- 周五：编写示例代码和文档

## 10. 结论

本方案为VibeCopilot的内容解析和数据存储系统提供了一个直接的重构方案。当前项目处于demo阶段，我们采用直接实现的方式，不考虑兼容性和数据迁移问题。

这种快速实现的方式将让我们专注于系统的核心功能，在短时间内实现可用版本。整个实现预计只需要3周时间，显着缩短了开发周期。

通过这种直接的重构和与Basic Memory的集成，VibeCopilot将获得：

- 统一的解析和存储接口
- 命令行和Cursor Agent使用同一数据源
- 更简洁清晰的代码结构
- 更高效的开发和迭代
- 为后期扩展奠定实验基础
