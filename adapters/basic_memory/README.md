# Basic Memory 适配器

Basic Memory 是一个知识管理和信息提取适配器，用于解析文档、提取实体关系并存储/导出这些信息。

## 主要功能

- 解析多种格式的文档（主要是Markdown）
- 提取文档中的实体和关系
- 将结构化信息存储到SQLite数据库
- 支持将数据导出到Obsidian等知识库格式

## 文件结构

- `cli/` - 命令行工具
- `db/` - 数据库操作
- `parsers/` - 文档解析器
- `exporters/` - 数据导出器
- `utils/` - 辅助工具函数

## 使用方法

详见 [使用文档](./readmd.md)。

## 命令行工具

提供了方便的命令行工具用于批量处理文档:

```bash
# 安装命令行工具
ln -sf $(pwd)/scripts/basicmem /usr/local/bin/basicmem

# 查看帮助
basicmem --help

# 解析文档
basicmem parse document.md

# 导出数据
basicmem export data.json
```
