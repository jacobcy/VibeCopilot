---
title: Obsidian与Docusaurus集成工作流
description: 如何使用Obsidian编写文档并发布到Docusaurus的工作流指南
category: 开发指南
created: 2024-04-05
updated: 2024-04-05
---

# Obsidian与Docusaurus集成工作流

## 概述

VibeCopilot项目使用Obsidian作为文档编辑工具，Docusaurus作为文档发布平台。本文档介绍如何在这两个工具之间高效协作，确保文档质量和链接完整性。

## 工作流程

整个文档开发工作流程分为以下几个步骤：

1. 在Obsidian中编写和组织文档
2. 转换为Docusaurus格式
3. 预览和测试
4. 发布文档

### 1. 在Obsidian中编写文档

#### 设置Obsidian

1. 打开Obsidian并创建一个新的Vault（保管库），指向项目的docs目录
2. 确保文档符合以下规范：
   - 每个文档都有合适的YAML前置元数据（title、description、category等）
   - 使用`[文件名](文件名.md)`格式创建内部链接
   - 图片和资源文件放在`docs/assets`目录中

#### 文档组织结构

```
docs/
├── assets/           # 图片和其他资源
├── dev/              # 开发者文档
├── user/             # 用户文档
└── workflow/         # 工作流文档
```

### 2. 转换为Docusaurus格式

我们使用自定义工具将Obsidian格式转换为Docusaurus格式。转换处理包括：

- Obsidian链接 `[文件名](文件名.md)` → Docusaurus链接 `[文件名](./文件名.md)`
- 图片引用路径转换
- YAML前置元数据保留

#### 使用转换工具

```bash
# 转换单个文件
python scripts/docs/tools/obsidian_to_docusaurus.py --obsidian-dir docs --docusaurus-dir website/docs --file path/to/file.md

# 转换所有文件
python scripts/docs/tools/obsidian_to_docusaurus.py --obsidian-dir docs --docusaurus-dir website/docs
```

### 3. 预览和测试

转换后，可以使用Docusaurus开发服务器预览文档：

```bash
cd website
npm start
```

这将启动一个本地开发服务器，通常在<http://localhost:3000访问。>

#### 链接检查

Docusaurus会自动检查链接完整性。检查模式有：

- **开发模式**：警告但不阻止
- **构建模式**：严格检查，错误会导致构建失败
- **CI环境**：最严格模式，确保发布前所有链接正确

手动运行链接检查：

```bash
node scripts/docs/tools/check_links.js docs
```

### 4. 发布文档

发布通过GitHub Actions自动化：

1. 将更改推送到main分支
2. GitHub Actions工作流会自动构建文档
3. 构建成功后，自动部署到GitHub Pages

## 最佳实践

### 文档编写指南

1. **使用明确的标题结构**：
   - 每个文档只有一个h1标题
   - 使用h2、h3等创建层次结构
   - 避免跳过标题级别

2. **链接最佳实践**：
   - 使用相对路径（`[文件名](文件名.md)`）而非绝对路径
   - 为链接添加描述性文本（`[描述](文件名.md)`）
   - 确保链接目标文件存在

3. **图片处理**：
   - 图片放在`docs/assets`目录
   - 使用相对路径引用（`![图片名.png](图片名.png.md)`）
   - 添加alt文本（`![替代文本](图片名.png.md)`）

### 常见问题与解决方案

#### 链接错误

**问题**：链接在转换后不正确或无法访问
**解决方案**：

1. 确保使用正确的Obsidian链接语法 `[文件名](文件名.md)`
2. 检查目标文件是否存在
3. 运行链接检查工具查找问题

#### 图片显示问题

**问题**：图片不显示或路径错误
**解决方案**：

1. 确认图片位于`docs/assets`目录
2. 使用相对路径：`![图片名.png](图片名.png.md)`
3. 检查图片文件名大小写是否正确

## 工具参考

### 文档转换工具

工具位置：`scripts/docs/tools/obsidian_to_docusaurus.py`

```bash
python scripts/docs/tools/obsidian_to_docusaurus.py --help
```

### 链接检查工具

工具位置：`scripts/docs/tools/check_links.js`

```bash
node scripts/docs/tools/check_links.js [docs目录] [--strict] [--verbose]
```

### Pre-commit钩子

提交前自动运行检查，确保文档质量：

- Markdown语法检查
- Obsidian特有语法检查
- 文档链接检查

## 相关资源

- [Docusaurus官方文档](https://docusaurus.io/docs.md)
- [Obsidian官方帮助](https://help.obsidian.md/Home.md)
- [Obsidiosaurus项目](https://github.com/CIMSTA/obsidiosaurus.md)（我们借鉴了其思路）
