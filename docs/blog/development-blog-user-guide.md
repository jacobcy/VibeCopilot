# VibeCopilot Blog 命令使用指南

## 概述

Blog 命令用于从 Basic Memory 知识库中检索和展示开发日志，便于跟踪项目进度、记录和分享开发经验。通过这个命令，您可以轻松查看过去的开发工作，生成进度报告，以及导出特定主题的开发记录。

## 基本用法

```
/blog [参数]
```

不带任何参数时，默认显示最近 7 天的开发日志。

## 参数说明

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--timeframe` | 时间范围 | "7d" | `--timeframe=30d`、`--timeframe=本周`、`--timeframe=上个月` |
| `--tag` | 按标签筛选 | 无 | `--tag=feature`、`--tag=bug,performance` |
| `--search` | 按关键词搜索 | 无 | `--search=认证`、`--search=性能优化` |
| `--format` | 输出格式 | "markdown" | `--format=text`、`--format=markdown` |
| `--output` | 输出位置 | "console" | `--output=console`、`--output=file` |
| `--folder` | 要搜索的文件夹 | "开发日志" | `--folder=技术文档`、`--folder=项目记录` |

## 使用示例

### 查看最近 7 天的开发日志

```
/blog
```

### 查看特定时间范围的日志

```
/blog --timeframe=30d
/blog --timeframe=上个月
/blog --timeframe=本周
```

### 按标签筛选日志

```
/blog --tag=feature
/blog --tag=bug,performance
```

### 搜索特定主题的日志

```
/blog --search=性能
/blog --search=数据库
```

### 导出日志到文件

```
/blog --output=file
/blog --timeframe=本季度 --output=file
```

### 以纯文本格式查看日志

```
/blog --format=text
```

### 组合使用多个参数

```
/blog --timeframe=上个月 --tag=feature --format=markdown --output=file
```

## 命令行工具

除了在 Cursor 中使用 `/blog` 命令外，您还可以通过命令行工具直接使用：

```bash
python scripts/blog_cli.py [参数]
```

例如：
```bash
python scripts/blog_cli.py --timeframe=30d --tag=feature
```

不带参数运行命令行工具会显示帮助信息：
```bash
python scripts/blog_cli.py
```

## 输出格式

### Markdown 格式（默认）

Markdown 格式输出包含标题、日期、内容和标签，适合用于文档和报告。

### 文本格式

纯文本格式提供更简洁的输出，适合在终端查看或处理。

## 集成建议

- 结合 `/update` 命令添加新的开发日志
- 使用 `/memory` 命令检查日志存储状态
- 通过 `/check` 命令查看项目进度并参考相关日志

## 自定义与扩展

您可以通过修改 `src/cli/commands/blog.py` 和 `scripts/basic_memory/blog_logs.py` 来扩展功能，例如添加更多输出格式、增强搜索能力或添加数据可视化功能 🚀
