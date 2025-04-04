# Notion 导出工具用户指南

## 简介

Notion 导出工具是一个高效的命令行工具，用于将 Notion 页面导出为 Markdown 文档。它支持递归导出子页面、自定义文件名和深度控制等功能，帮助您轻松构建本地知识库。

## 主要功能

- **单页面导出**：将单个 Notion 页面导出为 Markdown 文件
- **递归导出**：自动识别并导出所有子页面，保持知识结构完整
- **智能文件命名**：支持使用页面标题作为文件名，提高可读性
- **深度控制**：可限制递归导出的深度，避免导出过多内容
- **格式保留**：保留 Notion 中的富文本格式、列表、代码块等元素

## 快速开始

### 前提条件

1. 已安装 Node.js 和 npm/pnpm
2. 已安装 TypeScript 和 ts-node
3. 拥有 Notion API 密钥

### 基本设置

1. **创建 Notion 集成**
   - 访问 [Notion Integrations](https://www.notion.so/my-integrations) 页面
   - 创建新集成并获取 API 密钥

2. **授权访问页面**
   - 打开您要导出的 Notion 页面
   - 点击右上角的 "Share" 按钮
   - 添加您刚刚创建的集成

3. **配置环境变量**
   - 复制 `.env.notion.example` 为 `.env.notion`
   - 填入您的 Notion API 密钥和页面 ID

### 基本使用

运行以下命令导出单个页面：

```bash
./scripts/run_export_notion.sh
```

导出结果将保存在 `exports` 目录下。

## 常见问题

**Q: 如何找到 Notion 页面 ID？**

A: 页面 ID 是 URL 中的 32 位字符串。例如，在 `https://www.notion.so/myworkspace/Page-Title-1ca73a857f76800eb2f9e4502426d717` 中，ID 是 `1ca73a857f76800eb2f9e4502426d717`。

**Q: 导出失败怎么办？**

A: 最常见的原因是集成未被授权访问页面。确保您已在 Notion 页面的共享设置中添加了您的集成。

**Q: 如何导出特定深度的子页面？**

A: 使用 `--max-depth` 参数设置递归深度，例如：`./scripts/run_export_notion.sh --recursive --max-depth=2`

## 下一步

查看 [使用详情](./usage_detail.md) 了解更多高级用法和配置选项。
