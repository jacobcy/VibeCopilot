---
title: Docusaurus 使用指南
description: 如何使用Docusaurus管理和发布VibeCopilot项目文档
category: 教程
created: 2023-03-31
updated: 2023-03-31
---

# Docusaurus 使用指南

## 简介

[Docusaurus](https://docusaurus.io/) 是Facebook开发的静态网站生成器，专为技术文档优化，是VibeCopilot文档发布系统的核心组件。本指南将帮助您了解Docusaurus的基本使用方法，以及如何与VibeCopilot的文档系统集成。

## 什么是Docusaurus？

Docusaurus具有以下核心优势：

- **专为文档设计**：提供完整的文档网站框架
- **React驱动**：使用React构建，支持自定义组件
- **搜索功能**：内置文档搜索能力
- **版本控制**：支持文档版本管理
- **MDX支持**：可在Markdown中嵌入React组件
- **国际化**：支持多语言文档

## 安装与配置

### 前置要求

- [Node.js](https://nodejs.org/) 16.14 或更高版本
- [npm](https://www.npmjs.com/) 或 [Yarn](https://yarnpkg.com/)

### 基本配置

VibeCopilot项目已经为您配置好了Docusaurus环境，文档位于 `website` 目录中。如果您需要从头开始，可以按照以下步骤操作：

1. 安装Docusaurus：
   ```bash
   npx create-docusaurus@latest website classic
   ```

2. 进入网站目录：
   ```bash
   cd website
   ```

3. 启动开发服务器：
   ```bash
   npm run start
   # 或使用Yarn
   yarn start
   ```

4. 在浏览器中访问 `http://localhost:3000` 查看网站

## 文档结构

Docusaurus的文档结构如下：

```
website/
├── blog/                # 博客文章（可选）
├── docs/                # 文档目录
│   ├── intro.md         # 入门文档
│   └── tutorial/        # 教程目录
├── src/                 # 自定义React组件
│   ├── components/      # 自定义组件
│   └── pages/           # 自定义页面
├── static/              # 静态资源（图片等）
├── docusaurus.config.js # 主配置文件
├── sidebars.js          # 侧边栏配置
└── package.json         # 依赖管理
```

### 重要配置文件

1. **docusaurus.config.js**：网站主配置文件，包含主题、插件、导航等设置
2. **sidebars.js**：定义文档侧边栏结构
3. **package.json**：管理依赖和脚本

## 编写文档

### 文档格式

Docusaurus使用Markdown和MDX格式编写文档。每个文档文件通常包含以下结构：

```markdown
---
id: document-id
title: 文档标题
sidebar_label: 侧边栏标签
description: 文档描述
---

# 文档标题

内容...
```

### 组织文档

文档存放在 `docs` 目录下，可以按照逻辑分类创建子目录。目录结构将直接影响URL结构。

### 文档链接

在Docusaurus中，可以使用相对路径链接到其他文档：

```markdown
[链接文本](./other-doc.md)
```

## 发布文档

### 构建静态网站

```bash
npm run build
# 或使用Yarn
yarn build
```

构建后的静态文件位于 `build` 目录。

### 预览构建结果

```bash
npm run serve
# 或使用Yarn
yarn serve
```

### 部署选项

1. **GitHub Pages**：最简单的部署方式
   ```bash
   npm run deploy
   ```

2. **Netlify/Vercel**：连接Git仓库自动部署

3. **自托管**：将构建目录部署到任何静态网站服务器

## 自定义与扩展

### 主题自定义

可以在 `src/css/custom.css` 中修改CSS变量来自定义主题。

### 添加自定义页面

在 `src/pages` 目录下创建React组件：

```jsx
// src/pages/my-custom-page.js
import React from 'react';
import Layout from '@theme/Layout';

export default function MyCustomPage() {
  return (
    <Layout title="My Custom Page">
      <div className="container margin-vert--lg">
        <h1>My Custom Page</h1>
        <p>This is a custom React page</p>
      </div>
    </Layout>
  );
}
```

### 添加自定义组件

在MDX文档中使用自定义React组件：

```jsx
// src/components/MyComponent.js
import React from 'react';

export default function MyComponent({name}) {
  return <div>Hello, {name}!</div>;
}
```

```markdown
// docs/example.mdx
---
title: 示例
---

import MyComponent from '@site/src/components/MyComponent';

# 示例页面

下面是自定义组件:

<MyComponent name="Docusaurus" />
```

## 与VibeCopilot集成

### 自动生成侧边栏

VibeCopilot的文档引擎可以自动生成Docusaurus侧边栏配置：

```bash
python -m src.docs_engine.cli sidebar --output website/sidebars.json
```

或使用快捷脚本：

```bash
python scripts/docs/obsidian_sync.py --sidebar
```

### 同步Obsidian内容

1. 使用文档同步工具同步Obsidian内容到Docusaurus：

```bash
python scripts/docs/obsidian_sync.py --sync-all
```

2. 构建并预览网站：

```bash
cd website
npm run start
```

## 最佳实践

1. **保持文档组织一致**：遵循VibeCopilot的文档结构规范
2. **使用前置元数据**：为每个文档添加完整的元数据头部
3. **版本管理**：对重要文档启用版本控制
4. **添加目录**：长文档添加目录提高可导航性：
   ```markdown
   import TOCInline from '@theme/TOCInline';

   <TOCInline toc={toc} />
   ```
5. **使用Docusaurus特性**：适当使用提示框、标签页等功能

```markdown
:::tip 提示
这是一个提示框
:::

:::warning 警告
这是一个警告框
:::
```

## 常见问题

### Q: 如何添加新的侧边栏类别？

A: 在 `sidebars.js` 中添加新的类别，或使用VibeCopilot的自动侧边栏生成工具。

### Q: 如何处理大型文档库的性能问题？

A: 考虑使用文档版本控制，将旧版本文档分离存储；优化图片大小；使用懒加载组件。

### Q: Obsidian中的双向链接在Docusaurus中如何显示？

A: VibeCopilot的文档引擎会自动将Obsidian的双向链接 `[[文档名]]` 转换为Docusaurus兼容的链接 `[文档名](路径/文档名.md)`。

## 获取帮助

- 官方文档：[Docusaurus文档](https://docusaurus.io/docs)
- VibeCopilot支持：查阅 `docs/dev/workflow` 中的文档工作流指南
- GitHub Issues：在项目仓库提交问题
