---
title: Obsidian语法检查工具概览
description: 统一语法检查工具使用指南
category: 开发文档
created: 2024-04-05
updated: 2024-04-25
---

# Obsidian语法检查工具概览

## 工具定位

该工具专门解决pre-commit与sync.py之间的语法检查一致性问题，针对Obsidian特有语法结构进行验证，包括双向链接、嵌入图片和MDX组件等。

## 核心功能

- **语法检查**: 验证Obsidian链接、嵌入和MDX组件语法
- **错误分级**: 区分错误(Errors)、警告(Warnings)和提示(Info)
- **多种集成**: 支持命令行、pre-commit钩子和sync.py集成

## 快速使用指南

### 命令行操作

```bash
# 检查单个文件
python scripts/docs/utils/obsidian/syntax_checker.py path/to/file.md

# 检查整个目录
python scripts/docs/utils/obsidian/syntax_checker.py docs/

# 生成HTML报告
python scripts/docs/utils/generate_report.py --format html
```

### 集成方式

```bash
# 与sync.py结合
python scripts/docs/obsidian/sync.py --check-syntax

# 严格模式(有错误会中断)
python scripts/docs/obsidian/sync.py --sync-file path/to/file.md --strict
```

## 配置参数

| 常用参数 | 说明 |
|--------|------|
| path | 检查目标(文件/目录) |
| --base-dir | 文档基础目录 |
| --verbose | 输出详细日志 |
| --errors-only | 只显示错误 |
| --format | 报告格式(html/json/text) |

## 常见问题速查

| 问题 | 解决方法 |
|-----|----------|
| 链接目标不存在 | 检查文件名大小写、空格处理、链接格式 |
| MDX组件未闭合 | 确保开闭标签匹配、检查嵌套顺序 |
| 缺少元数据字段 | 添加必要的前置YAML元数据(title、description等) |

## 最佳实践

1. **集成CI/CD**: 将检查纳入GitHub Actions工作流
2. **定期全面检查**: 使用报告工具进行项目全面扫描
3. **优先级处理**: 先修复错误级别问题，再处理警告和提示
4. **团队规范**: 所有成员提交前执行语法检查

## 相关资源

- [Obsidian与Docusaurus集成工作流](./obsidian_docusaurus_workflow.md)
- [文档引擎使用指南](../user/docs_engine_guide.md)
- [Markdown语法规范](../dev/markdown_style_guide.md)

---

本概览提供了Obsidian语法检查工具的核心概念和使用方式。详细配置和高级用法请参考相关工具源码及注释。
