# Notion 导出工具使用详情

## 配置选项详解

Notion 导出工具提供了丰富的配置选项，可通过环境变量或命令行参数设置。

### 环境变量配置

在 `config/default/.env.notion` 文件中可配置以下选项：

| 环境变量 | 必填 | 默认值 | 说明 |
|---------|------|-------|------|
| `NOTION_API_KEY` | 是 | - | Notion API 密钥 |
| `NOTION_PAGE_ID` | 是 | - | 要导出的页面 ID |
| `OUTPUT_FILENAME` | 否 | exported_notion_page.md | 输出文件名 |
| `OUTPUT_DIR` | 否 | exports | 输出目录路径 |
| `RECURSIVE` | 否 | false | 是否递归导出子页面 |
| `MAX_DEPTH` | 否 | 0 (无限制) | 递归导出的最大深度 |
| `USE_PAGE_TITLE_AS_FILENAME` | 否 | false | 是否使用页面标题作为文件名 |

### 命令行参数

以下命令行参数可覆盖环境变量配置：

| 参数 | 对应环境变量 | 示例 |
|-----|------------|------|
| `--recursive` | RECURSIVE=true | ./scripts/run_export_notion.sh --recursive |
| `--max-depth=N` | MAX_DEPTH=N | ./scripts/run_export_notion.sh --max-depth=3 |
| `--use-title` | USE_PAGE_TITLE_AS_FILENAME=true | ./scripts/run_export_notion.sh --use-title |

## 高级用法

### 组合参数使用

您可以组合多个参数实现更复杂的导出需求：

```bash
# 递归导出所有子页面，并使用页面标题作为文件名
./scripts/run_export_notion.sh --recursive --use-title

# 递归导出两层子页面，使用页面标题作为文件名
./scripts/run_export_notion.sh --recursive --max-depth=2 --use-title
```

### 文件命名规则

当启用 `USE_PAGE_TITLE_AS_FILENAME` 选项时，文件命名规则如下：

- 格式：`页面标题-页面ID前8位.md`
- 特殊字符会被替换为下划线或连字符
- 标题长度会被限制在 100 字符以内

例如，标题为 "研究笔记：Notion API 集成" 的页面可能会被命名为 `研究笔记-Notion-API-集成-1ca73a85.md`。

### 导出多个根页面

如需导出多个不同的根页面，可以创建多个环境变量文件并分别运行：

```bash
# 导出第一个页面
NOTION_PAGE_ID=page_id_1 ./scripts/run_export_notion.sh --recursive

# 导出第二个页面
NOTION_PAGE_ID=page_id_2 ./scripts/run_export_notion.sh --recursive
```

## Markdown 格式支持

导出工具支持以下 Notion 元素的 Markdown 转换：

| Notion 元素 | Markdown 表示 |
|------------|--------------|
| 段落 | 普通文本 |
| 标题 1-3 | #, ##, ### |
| 无序列表 | - 项目 |
| 有序列表 | 1. 项目 |
| 待办事项 | - [ ] 或 - [x] |
| 代码块 | ```语言\n代码\n``` |
| 引用 | > 引用内容 |
| 分割线 | --- |
| 子页面链接 | [📑 页面标题](页面ID) |
| 折叠块 | HTML details/summary 标签 |

## 故障排除

### 常见错误

1. **API 密钥错误**
   - 错误信息：`Invalid API key`
   - 解决方案：检查 NOTION_API_KEY 是否正确

2. **页面访问权限错误**
   - 错误信息：`Could not find page with ID: xxx`
   - 解决方案：确保您的集成已被授权访问该页面

3. **页面 ID 格式错误**
   - 错误信息：`Invalid configuration: pageId must be a 32-character hex string`
   - 解决方案：确保页面 ID 是 32 位的十六进制字符串

### 调试技巧

如需更详细的日志输出，可以在运行脚本前设置 DEBUG 环境变量：

```bash
DEBUG=true ./scripts/run_export_notion.sh
```

## 性能优化

- 对于大型页面，建议设置 MAX_DEPTH 限制递归深度
- 如果只需要特定子页面，建议单独导出这些页面而不是递归导出整个结构
- 导出大量页面时，建议分批次进行，避免 Notion API 限流

## 技术架构

该工具采用模块化设计，主要包含以下组件：

- **index.ts**: 程序入口点
- **types.ts**: 类型定义
- **utils.ts**: 工具函数
- **exporter.ts**: 导出逻辑
- **notion-client.ts**: Notion API 客户端
- **markdown-converter.ts**: Markdown 转换

每个模块职责单一，代码量控制在 200 行以内，符合项目代码组织规范。
