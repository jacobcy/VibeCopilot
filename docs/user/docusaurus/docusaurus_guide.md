---
title: Docusaurus使用指南
description: 如何使用Docusaurus构建和管理VibeCopilot项目文档
category: 教程
created: 2024-04-01
updated: 2024-04-01
---

# Docusaurus使用指南

## 概述

Docusaurus是一个现代化的静态网站生成器，专注于使文档简单易用且美观。VibeCopilot项目使用Docusaurus作为文档发布平台，将标准Markdown文档转换为网站。本指南将帮助您快速上手Docusaurus并了解如何查看和使用项目文档。

## Docusaurus基础

### 什么是Docusaurus？

Docusaurus是由Facebook开源的静态网站生成器，具有以下特点：

- 易于使用和维护
- 内置版本控制
- 支持搜索功能
- 响应式网站设计
- 支持多语言翻译
- Markdown和MDX支持

### 文件结构

VibeCopilot项目的Docusaurus遵循以下结构：

```
website/                # Docusaurus网站目录
├── docs/               # 由docs/目录生成的文档
├── src/                # 网站源代码
├── static/             # 静态资源
├── docusaurus.config.js  # Docusaurus配置
├── sidebars.js         # 侧边栏配置
└── package.json        # 项目依赖

docs/                   # 标准Markdown文档目录
└── ...                 # 原始文档内容
```

> **重要**：文档内容应在`docs/`目录中编辑，而不是在`website/docs/`中，后者是由构建过程生成的。

## 查看文档网站

### 本地运行文档网站

要在本地预览文档网站，请按照以下步骤操作：

1. 确保安装了Node.js (v14或更高版本)
2. 进入网站目录：
   ```bash
   cd website
   ```
3. 安装依赖：
   ```bash
   npm install
   ```
4. 启动开发服务器：
   ```bash
   npm start
   ```
5. 在浏览器中访问：<http://localhost:3000>

### 文档格式与结构

Docusaurus使用从`docs/`目录构建的Markdown文件来生成网站。每个Markdown文件的开头都包含YAML格式的前置元数据：

```yaml
---
title: 文档标题
description: 文档描述
sidebar_position: 1  # 在侧边栏中的位置
---

# 正文内容开始
```

## 如何使用文档网站

### 导航文档

Docusaurus生成的网站包含以下导航元素：

- **顶部导航栏**：包含主要区域链接
- **侧边栏**：显示当前区域的文档结构
- **搜索栏**：用于查找特定内容
- **页面导航**：显示当前页面的目录

### 搜索内容

使用网站右上角的搜索框搜索内容：

1. 点击搜索图标或按`Ctrl+K`(Windows/Linux)或`Cmd+K`(Mac)
2. 输入搜索关键词
3. 从搜索结果中选择相关页面

### 查看代码示例

文档中的代码示例带有语法高亮和复制功能：

```jsx
// 示例代码
function example() {
  console.log('这是一个示例');
}
```

点击代码块右上角的复制按钮可以复制代码。

## 文档流程

### VibeCopilot的文档流程

VibeCopilot采用以下文档流程：

1. **创作**：在标准Markdown格式(`docs/`目录)或Obsidian中创建和编辑文档
2. **同步**：使用同步工具在Obsidian和标准Markdown之间同步
3. **构建**：Docusaurus将标准Markdown转换为网站
4. **发布**：自动部署到网站

> **注意**：编辑应在`docs/`目录或Obsidian中进行，而不是在`website/docs/`目录中，因为后者是自动生成的。

### 从Markdown到Docusaurus

标准Markdown文档(`docs/`)会按以下流程转换为Docusaurus网站：

1. Docusaurus读取`docs/`目录中的Markdown文件
2. 处理前置元数据和内容
3. 应用主题和布局
4. 生成HTML、CSS和JavaScript
5. 创建可导航的文档网站

## 与Obsidian集成

### Obsidian与Docusaurus的协同工作

VibeCopilot建立了从Obsidian到Docusaurus的单向工作流：

1. 在Obsidian中创建和编辑文档
2. 使用同步工具将Obsidian内容同步到标准Markdown格式：
   ```bash
   python scripts/docs/obsidian/sync.py to-docs
   ```
3. Docusaurus从标准Markdown构建网站

详细内容请参考[Obsidian同步工具使用指南](../obsidian/obsidian_integration_guide.md)。

## 部署文档

查看已部署的文档网站：

1. **GitHub Pages**：通过项目的GitHub Pages链接访问
2. **本地构建**：
   ```bash
   cd website
   npm run build
   ```
   生成的静态文件位于`website/build/`目录

## 常见问题解答

### 页面显示不正确

**问题**：文档页面显示不正确或格式丢失
**解决方案**：

1. 确认原始Markdown文件(`docs/`目录)格式正确
2. 检查前置元数据是否完整
3. 重新启动开发服务器

### 搜索不工作

**问题**：搜索功能无法找到内容
**解决方案**：

1. 确保已构建搜索索引
2. 在本地开发模式下，某些搜索功能可能受限
3. 在生产环境中搜索功能更完整

### 链接不正确

**问题**：页面之间的链接不工作
**解决方案**：

1. 确保在原始Markdown中使用正确的相对路径
2. 检查文件名是否正确
3. 使用`.md`扩展名，而不是`.html`

## 相关资源

- [Docusaurus官方文档](https://docusaurus.io/docs.md)
- [Markdown语法指南](https://www.markdownguide.org/.md)
- [Obsidian同步工具使用指南](../obsidian/obsidian_integration_guide.md)
- [VibeCopilot文档指南](../../guides/getting_started.md)
