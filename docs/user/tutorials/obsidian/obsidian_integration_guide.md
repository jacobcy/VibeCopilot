---
id: obsidian_integration_guide
title: Obsidian 同步工具使用指南
sidebar_position: 1
---

# Obsidian 同步工具使用指南

本指南将帮助您快速入门VibeCopilot的Obsidian同步工具，即使您是完全的小白用户，也能轻松实现Obsidian与标准Markdown文档之间的双向同步。

## 什么是Obsidian同步工具？

VibeCopilot的Obsidian同步工具是一个简单易用的实用程序，它可以：

- 将`docs/`目录中的标准Markdown文档自动同步到Obsidian知识库
- 将Obsidian知识库中的更改同步回标准Markdown文档
- 自动处理两种格式之间的转换
- 智能过滤特定文件类型，避免不必要的同步

重要说明：同步仅在`docs/`目录（标准Markdown）和`.obsidian/vault/`（Obsidian知识库）之间进行，不涉及`website/docs/`（Docusaurus生成目录）。

## 开始使用前的准备

### 安装必要软件

1. **安装Obsidian**：
   - 从[Obsidian官网](https://obsidian.md/.md)下载并安装Obsidian
   - 创建一个新的保险库或打开现有保险库

2. **确认Python环境**：
   - 确保已安装Python 3.8或更高版本
   - VibeCopilot工具已包含所需的Python库

### 设置Obsidian保险库

最简单的方法是将Obsidian保险库指向项目的`.obsidian/vault`目录：

1. 打开Obsidian
2. 点击"打开另一个保险库" > "打开文件夹作为保险库"
3. 选择项目中的`.obsidian/vault`目录
4. 点击"打开"

这样，Obsidian就会直接使用同步工具管理的文件。

## 基本使用方法

### 一键同步操作

VibeCopilot的同步工具提供了简单的命令行操作：

#### 将标准文档同步到Obsidian

```bash
python scripts/docs/obsidian/sync.py to-obsidian
```

这个命令会将`docs/`目录中的标准Markdown文件转换并同步到Obsidian保险库中。

#### 将Obsidian文档同步回标准格式

```bash
python scripts/docs/obsidian/sync.py to-docs
```

这个命令会将Obsidian保险库中的修改转换回标准Markdown格式，并更新`docs/`目录。

#### 自动监控并同步变更

```bash
python scripts/docs/obsidian/sync.py watch
```

这个命令会持续运行并监控文件变化，当检测到更改时自动进行双向同步。

### 配置同步选项

同步工具使用项目根目录下的`.env`文件进行配置：

```
# .env文件示例
DOCS_SOURCE_DIR=docs
OBSIDIAN_VAULT_DIR=.obsidian/vault
AUTO_SYNC_DOCS=false
AUTO_SYNC_INTERVAL=300
```

如果需要更改配置，只需编辑这个文件即可。一般情况下，默认配置已经足够使用。

## 链接和格式转换

同步工具会自动处理以下格式转换：

### 标准Markdown → Obsidian

| 标准Markdown格式 | Obsidian格式 |
|-------------------|-------------|
| `[显示文本](文件名.md)` | `[显示文本](文件名\.md)` |
| `![图片名](路径/图片.png)` | 保持不变 |

### Obsidian → 标准Markdown

| Obsidian格式 | 标准Markdown格式 |
|-------------|-------------------|
| `[显示文本](文件名\.md)` | `[显示文本](文件名.md)` |
| `[文件名](文件名.md)` | `[文件名](文件名.md)` |
| `![图片名](图片名.md)` | `![图片名](图片名)` |

## 文档流程

### VibeCopilot的文档流程

VibeCopilot采用以下文档流程：

1. **创作内容**：在Obsidian或直接编辑`docs/`目录中的标准Markdown文件
2. **同步文档**：使用同步工具在两个环境间保持内容一致
3. **构建网站**：Docusaurus自动从`docs/`目录构建网站内容

```
[Obsidian知识库] ⟷ [标准Markdown文档] → [Docusaurus网站]
(.obsidian/vault/)   (docs/)            (website/docs/)
```

> **重要**：只需编辑Obsidian或`docs/`目录中的文件，不要直接修改`website/docs/`中的内容，因为它们是自动生成的。

## 实用技巧

### 1. 设置定时同步

如果希望文档自动同步，可以：

1. 在`.env`文件中设置`AUTO_SYNC_DOCS=true`
2. 调整`AUTO_SYNC_INTERVAL`设定同步间隔（秒）
3. 使用`watch`命令启动同步工具

### 2. 在提交前同步

养成在Git提交前运行同步的习惯：

```bash
# 提交前先同步
python scripts/docs/obsidian/sync.py to-docs
git add .
git commit -m "更新文档"
```

### 3. 处理同步冲突

如果同时在Obsidian和标准文档中编辑了同一文件，可能会发生冲突：

1. 使用`to-obsidian`或`to-docs`命令，以其中一方为准
2. 手动合并变更
3. 重新运行同步命令

### 4. 创建新文档

创建新文档的最佳方式：

1. 在Obsidian中创建新文件
2. 添加基本的前置元数据：
   ```yaml
   ---
   title: 文档标题
   description: 文档描述
   ---
   ```
3. 编写内容
4. 运行`to-docs`命令将其同步到标准目录

## 文件过滤

同步工具会自动过滤特定文件类型，避免不必要的同步：

1. **Docusaurus配置文件**：`_category_.json`等文件不会同步到Obsidian
2. **Obsidian配置文件**：`app.json`、`appearance.json`等文件不会同步到标准文档
3. **临时文件和系统文件**：`.DS_Store`等系统文件会被排除

这确保了只有实际内容会被同步，而特定平台的配置文件保持独立。

## 常见问题解答

### Obsidian中看不到同步的文件？

**解决方案**：

1. 确认Obsidian打开的保险库路径是否正确
2. 检查`.env`文件中的`OBSIDIAN_VAULT_DIR`设置
3. 手动运行`to-obsidian`命令

### 链接显示不正确？

**解决方案**：

1. 在Obsidian中，使用Wiki链接格式`[文件名](文件名.md)`或`[显示文本](文件名.md)`
2. 在标准Markdown中，使用`[显示文本](文件名.md)`格式
3. 同步工具会自动处理转换

### 某些文件不需要同步？

**解决方案**：
同步工具会自动排除以下文件：

- Docusaurus配置文件（如`_category_.json`）
- Obsidian配置文件（如`app.json`和`workspace.json`）
- 临时文件和系统文件（`.DS_Store`等）

### 同步命令报错？

**解决方案**：

1. 确认Python环境正确
2. 检查是否在项目根目录运行命令
3. 确保文件路径不包含特殊字符

## 下一步

现在您已经了解了Obsidian同步工具的基本使用方法，可以：

1. 查看[Docusaurus使用指南](../docusaurus/docusaurus_guide.md)了解如何查看网站文档
2. 探索[项目文档目录](../../../dev/document_index.md)了解更多文档内容
3. 加入我们的用户群组分享您的使用经验

---

通过本指南，您应该能够轻松上手VibeCopilot的Obsidian同步工具。如有任何问题，欢迎在GitHub上提issue或加入我们的社区讨论！
