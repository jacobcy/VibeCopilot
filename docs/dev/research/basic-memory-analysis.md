## 使用Basic Memory命令行工具

首先，需要安装Basic Memory：

```bash
# 使用uv（推荐）
uv tool install basic-memory

# 或使用pip
pip install basic-memory
```

### 主要命令

1. **基本操作命令**：

```bash
# 同步知识库
basic-memory sync

# 实时监控文件变化
basic-memory sync --watch

# 查看状态
basic-memory status

# 启动MCP服务器（与Claude集成）
basic-memory mcp
```

2. **直接使用工具功能**：

```bash
# 写入笔记
basic-memory tool write-note --title "笔记标题" --folder "文件夹" --content "笔记内容"

# 也可以通过管道输入内容
echo "# 我的笔记\n\n这是一个测试笔记" | basic-memory tool write-note --title "测试笔记" --folder "笔记"

# 读取笔记
basic-memory tool read-note "笔记标题"

# 搜索笔记
basic-memory tool search-notes "搜索关键词"

# 获取最近活动
basic-memory tool recent-activity

# 构建上下文
basic-memory tool build-context "memory://笔记路径"
```

3. **导入功能**：

```bash
# 导入Claude对话
basic-memory import claude conversations

# 导入ChatGPT历史
basic-memory import chatgpt
```

4. **多项目管理**：

```bash
# 添加新项目
basic-memory project add work ~/work-basic-memory

# 设置默认项目
basic-memory project default work

# 列出所有项目
basic-memory project list
```

### 在脚本中使用

你可以在Shell脚本中组合这些命令，实现更复杂的功能：

```bash
#!/bin/bash

# 同步知识库
basic-memory sync

# 创建新笔记
cat << EOF | basic-memory tool write-note --title "项目计划" --folder "规划"
# 项目计划

## 目标
- 实现基础功能
- 完善用户体验

## 时间线
- 第一周：需求分析
- 第二周：核心实现
EOF

# 搜索相关内容
basic-memory tool search-notes "项目计划"
```

这些命令使你可以完全通过命令行或脚本使用Basic Memory的所有功能，不需要通过Claude。这对于自动化工作流或将Basic Memory集成到其他系统中非常有用。

注意，当使用`tool`子命令时，你可以访问Basic Memory的核心功能，这些功能与Claude中使用的MCP工具完全相同。

## Basic Memory的代码结构

Basic Memory是一个基于Python实现的本地知识库系统，主要结构包括：

1. **核心模块结构**：
   - `mcp/` - Model Context Protocol集成，允许与Claude等LLM交互
   - `models/` - 数据模型定义
   - `repository/` - 数据存储层
   - `markdown/` - Markdown解析和处理
   - `services/` - 核心业务逻辑服务
   - `schemas/` - 数据结构和验证
   - `cli/` - 命令行工具

2. **MCP工具实现**：
   - `write_note.py` - 创建或更新笔记
   - `read_note.py` - 读取笔记内容
   - `search.py` - 搜索知识库
   - `build_context.py` - 构建上下文关系
   - `recent_activity.py` - 获取最近活动
   - `canvas.py` - 创建可视化画布

## 关键组件工作原理

1. **MCP服务器**：
   - 使用`FastMCP`创建一个服务器实例
   - 注册各种工具，如write_note、read_note等
   - 监听Claude的请求并执行对应工具

2. **write_note工具**：
   - 接收标题、内容、文件夹和标签参数
   - 解析Markdown内容中的语义标记(观察和关系)
   - 创建实体并保存到知识库
   - 返回创建结果摘要，包括观察和关系的统计信息

3. **文件系统集成**：
   - 所有知识以Markdown文件形式存储在本地
   - 使用文件监控系统实时同步文件变化
   - 初始化时会设置文件监视任务，结束时会取消该任务

## 技术栈

- 使用`mcp`框架与Claude集成
- 使用`loguru`进行日志记录
- 使用`asyncio`实现异步操作
- 使用`FastAPI`设计的API架构
- 使用`SQLite`存储元数据

这个系统的核心价值在于：

1. 它把AI助手的"记忆"以Markdown文件形式存储在本地
2. 它自动识别并构建内容的语义关系图
3. 它为AI助手提供读写这些知识的能力

通过这种方式，你可以将与Claude的对话内容保存成永久的知识资源，并在未来的对话中继续引用和扩展这些知识。
