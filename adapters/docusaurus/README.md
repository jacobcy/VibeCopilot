# Docusaurus 适配器

此模块提供与 Docusaurus 文档网站交互的功能，包括文档同步和索引生成。

## 主要功能

- 将标准文档同步到 Docusaurus 网站
- 生成 Docusaurus 侧边栏配置
- 创建索引页面

## 组件

### Docusaurus 同步器 (DocusaurusSync)

`DocusaurusSync` 类负责将文档同步到 Docusaurus 网站。

```python
from adapters.docusaurus import DocusaurusSync

# 创建同步器
sync = DocusaurusSync("/path/to/source", "/path/to/docusaurus/content")

# 同步单个文件
sync.sync_file("path/to/file.md")

# 同步所有文件
stats = sync.sync_all()
print(f"同步完成: 添加 {stats['added']}，更新 {stats['updated']}，删除 {stats['deleted']}")
```

### 索引生成器 (IndexGenerator)

`IndexGenerator` 类负责为 Docusaurus 文档生成索引页面。

```python
from adapters.docusaurus import IndexGenerator

# 创建索引生成器
generator = IndexGenerator("/path/to/docusaurus/content")

# 为目录生成索引
generator.generate_index_for_directory("/path/to/directory")
```

## 配置选项

Docusaurus 适配器使用以下环境变量进行配置：

- `DOCUSAURUS_CONTENT_DIR` - Docusaurus 内容目录
- `SIDEBAR_CONFIG_PATH` - 侧边栏配置路径

## 与其他模块的集成

Docusaurus 适配器与以下模块集成：

- `src/parsing` - 用于解析文档内容
- `docs_engine` - 使用文档引擎进行格式转换
- `obsidian` - 从 Obsidian 接收文档内容
