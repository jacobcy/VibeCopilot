# MemoryItemRepository 重构指南

## 1. 目标

本次重构旨在优化 `src/db/repositories/memory_item_repository.py`，实现以下核心目标：

- **极致职责分离**：将 `MemoryItemRepository` 的职责 **严格限定** 在 `MemoryItem` 模型与 **关系型数据库（SQLite）** 之间的 **数据持久化操作 (CRUD)** 上。它只关心如何在 **其管理的 SQLite 表** 中存储和检索 `MemoryItem` 记录。
- **消除领域知识耦合**：Repository **不应理解** `MemoryItem` 记录的业务含义（例如它代表"记忆"），也 **不应感知** 任何外部系统（如向量数据库、文件系统或其他服务）。字段如 `permalink` 或 `folder` 对 Repository 而言，仅仅是 **普通的文本或数据字段**。
- **提升模块独立性与可测试性**：确保 `MemoryItemRepository` 可以独立于项目的其他业务逻辑（特别是 `memory` 相关逻辑）进行开发、测试和维护。

## 2. 问题分析

当前 `MemoryItemRepository` 存在以下问题，违反了上述目标：

- **感知外部逻辑**：直接导入并使用了 `src.memory.vector.chroma_utils` 中的工具函数，以及执行了路径规范化 (`normalize_path`)。这表明 Repository 具有了它不应具备的知识：
  - 它知道 `permalink` 字段具有特殊格式和含义（可能指向外部向量存储）。
  - 它知道 `folder` 字段代表一个文件系统路径，需要规范化。
- **职责越界**：Repository 执行了本应由 **上层服务 (如 `MemoryService`)** 或 **共享工具类** 处理的数据校验和准备工作。例如，它校验 `permalink` 格式、生成 `permalink`、规范化 `folder` 路径。这些操作都基于对字段业务含义的理解，而非纯粹的数据存储。
- **违反单一职责原则**：Repository 同时承担了数据持久化和特定领域数据（路径、外部链接）的预处理职责。

## 3. 重构方案

核心思路是将所有 **隐含了对字段业务含义理解** 的校验、转换和准备逻辑从 `MemoryItemRepository` 中 **彻底移除**，上移至负责业务逻辑的调用方（预期为 `MemoryService`）。

**具体步骤：**

1. **移除 Repository 内部依赖**：
    - 从 `memory_item_repository.py` 文件顶部移除所有与 `src.memory` 或路径处理相关的导入语句，例如：
      ```python
      # 移除这些或类似的导入
      # from src.memory.vector.chroma_utils import generate_permalink, parse_permalink, is_permalink, path_to_permalink
      # from some_path_utils import normalize_path
      ```

2. **净化 Repository 方法**：
    - 审查 `MemoryItemRepository` 中的所有方法（如 `create_item`, `get_by_permalink`, `update_item` 等）。
    - **移除** 所有进行 `permalink` 格式校验/生成/转换的代码。
    - **移除** 所有进行 `folder` 路径规范化的代码。
    - Repository 方法现在 **完全信任** 传入的数据。它接收 `title`, `content`, `folder`, `permalink` 等参数，并 **直接将这些值** 用于数据库操作（INSERT, SELECT, UPDATE, DELETE）。它 **不关心** 这些值的具体含义或格式是否符合外部系统的要求。
    - **示例 (修改后)**：
      ```python
      # 在 create_item 中
      # 直接使用传入的参数构建数据字典
      data = {
          "title": title,
          "content": content,
          "content_type": content_type,
          "folder": folder,         # 直接存储传入的值
          "tags": tags,
          "permalink": permalink,   # 直接存储传入的值
          "source": source,
          "sync_status": sync_status,
      }
      # 调用基础的 create 方法进行数据库插入
      item = super().create(data)
      # ...
      ```
    - 对于 `get_by_permalink`，它仅执行 `SELECT ... WHERE permalink = ?`，传入的 `permalink` 值由调用方保证其有效性（如果需要的话）。Repository 不做校验。

3. **强化服务层 (`MemoryService`) 职责**：
    - `MemoryService`（或任何调用 `MemoryItemRepository` 的服务）现在 **全权负责** 在调用 Repository 前，准备好所有 **符合业务规则和外部系统要求** 的数据。
    - **调用 `create_item` 前**：服务层需要：
        - 如有必要，调用路径工具规范化 `folder`。
        - 如有必要，调用 `permalink` 工具生成或校验 `permalink`。
        - 然后将 **处理好** 的 `folder` 和 `permalink` 值传递给 `repository.create_item`。
    - **调用 `get_by_permalink` 前**：服务层需要确保传入的 `permalink` 参数是它想要查询的 **确切值**（可能需要先进行格式转换）。
    - **调用 `update_item` 前**：如果更新 `folder` 或 `permalink`，服务层负责进行必要的规范化或校验/转换，然后将最终值传给 Repository。
    - `MemoryService` 将是依赖 `src.memory.vector.chroma_utils` 或其他路径/链接处理工具的地方。

## 4. 预期收益

- **极致解耦**：`MemoryItemRepository` 成为一个纯粹的、可复用的数据库访问层，与 `memory` 业务或任何特定外部系统完全解耦。
- **职责清晰**：业务逻辑（数据校验、准备、与其他服务协调）清晰地集中在 `MemoryService` 中。
- **易于替换实现**：未来如果更换向量数据库或 `permalink` 策略，只需修改 `MemoryService` 和相关工具，`MemoryItemRepository` 无需改动。同样，如果更换关系数据库，只需调整 Repository 内部实现，不影响服务层。
- **高度可测试性**：可以非常容易地 mock `MemoryItemRepository` 来测试服务层，也可以独立测试 Repository 的数据库交互逻辑。

## 5. 后续步骤

1. 根据本指南，修改 `src/db/repositories/memory_item_repository.py` 代码，移除所有数据校验和准备逻辑。
2. 识别并修改所有调用 `MemoryItemRepository` 的服务层代码（主要是 `MemoryService`），将移除的逻辑添加到服务层相应的方法调用之前。
3. 确保服务层正确导入并使用了 `chroma_utils` 或其他必要的工具。
4. 运行单元测试和集成测试，验证重构的正确性。
5. 进行代码审查。
