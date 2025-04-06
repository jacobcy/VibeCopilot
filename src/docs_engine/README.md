# VibeCopilot 动态文档系统

动态文档系统是 VibeCopilot 的核心组件之一，提供了文档管理、块级内容操作和文档间链接关系处理的功能。

## 系统架构

文档系统采用分层架构设计：

1. **数据层**：基于SQLAlchemy的ORM模型定义和数据访问对象
2. **功能层**：核心API，提供文档、块和链接的操作接口
3. **工具层**：提供Markdown导入导出、内容解析等辅助功能
4. **应用层**：与VibeCopilot其他组件的集成接口

## 主要组件

### 数据模型

- `Document`: 文档实体，包含元数据和引用信息
- `Block`: 文档块，文档内容的最小组成单位
- `Link`: 文档/块间的链接关系

### 核心API

- `DocumentEngine`: 文档管理引擎，提供文档的CRUD操作
- `BlockManager`: 块管理器，处理文档内容的块级操作
- `LinkManager`: 链接管理器，处理文档间的引用关系

### 工具类

- `MarkdownImporter`: Markdown文件导入工具
- ID生成器: 提供文档、块和链接的ID生成功能
- Markdown解析器: 将Markdown内容解析为块结构

## 使用示例

请参考 `examples/docs_engine_demo.py` 文件，了解动态文档系统的基本用法。

## 实现特点

1. **块级管理**：文档内容以块为单位管理，支持精确定位和操作
2. **双向链接**：支持文档与文档、块与块之间的双向链接
3. **Markdown原生支持**：与Markdown格式无缝集成
4. **元数据管理**：支持文档元数据的提取和管理
5. **文档图谱**：支持文档关系的图谱分析

## 开发指南

### 添加新的块类型

1. 在 `src/models/docs_engine.py` 的 `BlockType` 枚举中添加新类型
2. 在 `src/docs_engine/utils/markdown_parser.py` 中更新解析逻辑
3. 在 `BlockManager` 中添加对应的处理方法

### 扩展链接功能

1. 在 `src/models/docs_engine.py` 的 `LinkType` 枚举中添加新类型
2. 在 `LinkManager` 中添加相应的处理方法
3. 更新链接解析和渲染逻辑

## 未来计划

- [ ] 添加全文搜索支持
- [ ] 实现版本历史管理
- [ ] 添加协作编辑功能
- [ ] 支持更多内容格式（如HTML、PDF）
- [ ] 实现文档关系可视化
