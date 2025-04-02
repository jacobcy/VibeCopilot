---
title: Obsidian与Docusaurus集成工作流概览
description: 文档编写和发布流程简要指南
category: 开发指南
created: 2024-04-05
updated: 2024-04-25
---

# Obsidian与Docusaurus集成工作流概览

## 核心流程

VibeCopilot项目采用Obsidian进行文档编写，Docusaurus负责文档发布。整个工作流程分为四个核心步骤：

1. **编写文档** - 在Obsidian中创建和编辑文档
2. **格式转换** - 将Obsidian格式转换为Docusaurus兼容格式
3. **预览测试** - 本地测试文档链接和展示效果
4. **自动发布** - 通过GitHub Actions发布到生产环境

## 快速开始

### Obsidian设置

```bash
# 1. 创建指向项目docs目录的Vault
# 2. 确保文档包含必要的YAML前置元数据
---
title: 文档标题
description: 简短描述
category: 文档分类
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

### 格式转换

```bash
# 转换单个文件
python scripts/docs/tools/obsidian_to_docusaurus.py --file path/to/file.md

# 转换所有文件
python scripts/docs/tools/obsidian_to_docusaurus.py
```

### 本地预览

```bash
cd website
npm start  # 访问 http://localhost:3000
```

### 链接检查

```bash
node scripts/docs/tools/check_links.js docs
```

## 文档编写规范

1. **标题结构**：每个文档只有一个h1标题，按层次使用h2-h6
2. **链接格式**：使用`[描述](文件名.md)`的相对路径链接
3. **图片引用**：将图片放在`docs/assets`目录并使用相对路径引用

## 常见问题快速解决

| 问题 | 解决方案 |
|------|---------|
| 链接错误 | 检查语法格式、目标文件是否存在、运行链接检查工具 |
| 图片不显示 | 确认图片位于assets目录、检查引用路径和文件名大小写 |
| 转换失败 | 验证YAML前置元数据格式、检查特殊字符 |

## 相关工具参考

- 文档转换：`scripts/docs/tools/obsidian_to_docusaurus.py`
- 链接检查：`scripts/docs/tools/check_links.js`
- 语法检查：参见「Obsidian语法检查工具」文档

## 集成自动化

项目已配置pre-commit钩子和GitHub Actions工作流，可自动执行：

- 提交前的语法和链接检查
- 推送到main分支后的文档构建和发布

---

本指南提供Obsidian-Docusaurus工作流的核心概念。完整的工具使用细节请参考相关工具文档。
