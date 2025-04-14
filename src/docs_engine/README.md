# VibeCopilot 文档引擎

文档引擎是 VibeCopilot 的核心组件之一，提供文档管理、内容解析和格式转换功能。

## 快速开始

### 安装

确保已安装所有依赖：

```bash
pip install -e .
```

### 命令行工具

文档引擎提供了命令行工具 `doc`，可以执行以下操作：

```bash
# 显示帮助信息
doc --help

# 解析文档
doc parse <文件路径> [--output 输出文件] [--pretty]

# 提取文档块
doc extract <文件路径> [--output 输出文件] [--pretty]

# 导入文档到数据库
doc import <文件路径>

# 转换文档链接
doc convert <文件路径> --from <源格式> --to <目标格式> [--output 输出文件]

# 创建文档
doc create --template <模板名称> --output <输出路径> [--title <标题>] [--desc <描述>]
```

调试模式：

```bash
doc --debug <命令> <参数>
```

## 主要功能

- **文档解析**：将文档解析为结构化数据
- **块级管理**：支持文档内容的块级操作
- **链接转换**：支持不同格式间的链接转换
- **模板系统**：基于模板创建新文档

## 目录结构

- `api/`: 核心API接口
- `storage/`: 存储引擎
- `utils/`: 工具函数
- `config/`: 配置管理
- `templates/`: 文档模板
- `tools/`: 辅助工具
- `converters/`: 格式转换器

## 使用示例

### 解析文档

```bash
doc parse 文档.md --output 解析结果.json --pretty
```

### 转换链接格式

```bash
doc convert 文档.md --from obsidian --to docusaurus --output 转换后.md
```

### 创建新文档

```bash
doc create --template default --output 新文档.md --title "文档标题" --desc "文档描述"
```
