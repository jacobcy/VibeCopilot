---
id: docusaurus_guide
title: Docusaurus 指南
sidebar_position: 2
---

<!-- # Docusaurus 指南 -->

本指南介绍如何使用和自定义 Docusaurus 文档网站，以最佳方式展示您的 VibeCopilot 知识库。

## Docusaurus 简介

[Docusaurus](https://docusaurus.io/) 是一个现代静态网站生成器，专注于创建文档网站。VibeCopilot 使用 Docusaurus 将您的 Obsidian 知识库转换为专业的文档网站。

## 基本操作

### 启动开发服务器

```bash
# 进入网站目录
cd website

# 启动开发服务器
npm start
```

访问 [http://localhost:3000](http://localhost:3000) 查看实时预览。

### 构建静态网站

```bash
npm run build
```

构建结果将保存在 `website/build` 目录中。

### 部署网站

VibeCopilot 支持多种部署方式：

```bash
# 部署到 GitHub Pages
npm run deploy
```

## 自定义 Docusaurus

### 修改配置文件

主要配置文件位于 `website/docusaurus.config.ts`，您可以自定义：

- 网站标题和描述
- 导航栏和页脚
- 主题颜色
- 插件配置

### 自定义主题

#### 修改 CSS

编辑 `website/src/css/custom.css` 文件以自定义网站样式：

```css
:root {
  --ifm-color-primary: #2e8555;
  --ifm-color-primary-dark: #29784c;
  /* 其他颜色变量 */
}
```

#### 自定义组件

您可以通过创建主题组件来覆盖默认组件：

1. 创建 `website/src/theme` 目录
2. 添加自定义组件，如 `Footer.js`

### 侧边栏配置

编辑 `website/sidebars.ts` 文件自定义文档侧边栏：

```typescript
const sidebars = {
  tutorialSidebar: [
    {
      type: 'category',
      label: '用户指南',
      items: ['user/guides/getting_started'],
    },
    {
      type: 'category',
      label: '教程',
      items: [
        'user/tutorials/obsidian/obsidian_integration_guide',
        'user/tutorials/docusaurus/docusaurus_guide',
      ],
    },
  ],
};
```

## 页面和文档

### Markdown 功能

Docusaurus 支持扩展的 Markdown 语法：

#### 警告框

```markdown
:::note 标题
这是一个提示框。
:::

:::tip 提示
这是一个技巧提示框。
:::

:::warning 警告
这是一个警告提示框。
:::
```

#### 代码块

```markdown
```jsx title="src/components/HelloWorld.js"
function HelloWorld() {
  return <div>Hello, World!</div>;
}
```

### MDX 支持

Docusaurus 支持 MDX，允许您在 Markdown 中使用 React 组件：

```markdown
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
  <TabItem value="js" label="JavaScript">
    ```js
    console.log('Hello, World!');
    ```
  </TabItem>
  <TabItem value="py" label="Python">
    ```py
    print('Hello, World!')
    ```
  </TabItem>
</Tabs>
```

## 添加多语言支持

在 `docusaurus.config.ts` 中配置多语言支持：

```typescript
module.exports = {
  i18n: {
    defaultLocale: 'zh-Hans',
    locales: ['zh-Hans', 'en'],
    localeConfigs: {
      'zh-Hans': {
        label: '简体中文',
        direction: 'ltr',
      },
      en: {
        label: 'English',
        direction: 'ltr',
      },
    },
  },
  // 其他配置...
};
```

## 搜索功能

VibeCopilot 内置了 Docusaurus 的本地搜索功能。您也可以集成 Algolia DocSearch 以获得更好的搜索体验：

1. 在 [Algolia DocSearch](https://docsearch.algolia.com/apply/) 申请账号
2. 在 `docusaurus.config.ts` 中配置：

```typescript
themeConfig: {
  algolia: {
    appId: 'YOUR_APP_ID',
    apiKey: 'YOUR_API_KEY',
    indexName: 'YOUR_INDEX_NAME',
  },
}
```

## 进阶功能

### 添加博客

VibeCopilot 支持博客功能，您可以在 `website/blog` 目录中添加博客文章：

```markdown
---
slug: welcome
title: 欢迎使用 VibeCopilot
authors: [jacobcy]
tags: [hello, vibe]
---

欢迎使用 VibeCopilot！这是我们的第一篇博客文章。
```

### 集成 Google Analytics

```typescript
themeConfig: {
  googleAnalytics: {
    trackingID: 'UA-XXXXXXXXX-X',
  },
}
```

## 故障排除

### 常见问题

1. **构建失败**: 检查 Markdown 语法和引用的资源
2. **样式问题**: 检查自定义 CSS 是否正确加载
3. **链接错误**: 确保文档 ID 和路径正确

## 下一步

- 探索 [Docusaurus 官方文档](https://docusaurus.io/docs) 了解更多功能
- 查看 [示例网站](https://docusaurus.io/docs/examples) 获取灵感
