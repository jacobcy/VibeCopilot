# VibeCopilot - AI 辅助开发工作流

[![构建状态](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/jacobcy/VibeCopilot/actions/workflows/ci.yml/badge.svg)
[![测试状态](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/jacobcy/VibeCopilot/actions/workflows/test-all.yml/badge.svg)
[![许可证](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![版本](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/jacobcy/VibeCopilot/releases)

VibeCopilot 是一款旨在通过 AI 增强开发流程的命令行工具，帮助开发者更高效地管理项目、任务、知识和工作流。它通过 **MCP (Modular Command Protocol)** 标准与 Cursor IDE 等外部工具集成。

## ✨ 主要功能

VibeCopilot 提供了以下核心功能模块，通过统一的命令行界面进行管理：

* **数据库管理 (`db`)**: 初始化、查询、备份和恢复项目数据库 (基于 SQLite)。
* **工作流管理 (`flow`)**: 定义、创建、执行和管理开发工作流及会话。支持结构化的开发流程检查点。
* **知识库管理 (`memory`)**: 存储、检索、同步和管理项目相关的知识和文档 (当前使用 **basic-memory** 实现)。
* **路线图管理 (`roadmap`)**: 创建、查看、更新项目路线图，并支持与 **GitHub Projects** 进行双向同步，自动检测 Git 仓库信息。
* **规则管理 (`rule`)**: 定义、验证和管理项目中的结构化规则（如代码规范、流程规则等）。支持基于 YAML/Markdown 的规则模板。
* **状态管理 (`status`)**: 查看和更新项目的整体状态、各模块状态及活动路线图等持久化状态。
* **任务管理 (`task`)**: 创建、查询、更新和管理开发任务（类似 GitHub Issues）。
* **模板管理 (`template`)**: 管理用于生成代码、文档或其他内容的模板。支持多种生成器。
* **帮助系统 (`help`)**: 提供详细的命令行帮助信息和规则文档。

## 🚀 快速开始

### 技术栈

* **后端**: Python 3.9+ (FastAPI/Flask, SQLAlchemy)
* **数据库**: SQLite (元数据), **basic-memory** (知识库)
* **包管理**: `uv` / `pnpm`
* **AI**: Claude API

### 环境准备

1. 确保已安装 Python 3.9+ 和 Git。
2. 安装 `uv` 包管理器（如果尚未安装）：`pip install uv`
3. 设置必要的环境变量，例如：
    * `GITHUB_TOKEN`: 用于 GitHub 集成
    * `VIBECOPILOT_ENV`: 运行环境 (development, testing, production)
    * `DB_PATH`: SQLite 数据库文件路径
    * `LOG_LEVEL`: 日志级别

### 安装

在项目根目录下，使用 `uvx` 安装可编辑模式的 VibeCopilot：

```bash
uvx install-editable .
```

### 初始化

首次运行或在新的工作区中，需要在项目根目录下运行初始化命令：

```bash
vibecopilot db init
vibecopilot status init
# 如果需要初始化规则和模板等数据，可能还需要运行其他初始化命令
# 例如: vibecopilot rule load
# 例如: vibecopilot template load
```

### 💻 使用方法

VibeCopilot 主要通过命令行界面 (CLI) 进行交互。

#### 通用选项

* `--version`: 显示 VibeCopilot 的版本信息。
* `-v, --verbose`: 显示详细的日志信息，有助于调试。
* `-h, --help`: 显示帮助信息。

#### 主要命令

以下是 VibeCopilot 提供的主要命令组：

```
Usage: vibecopilot [OPTIONS] COMMAND [ARGS]...

  VibeCopilot CLI工具

Options:
  --version      显示版本信息
  -v, --verbose  显示详细日志信息
  -h, --help     Show this message and exit.

Commands:
  db        数据库管理命令
  flow      工作流管理命令
  help      显示帮助信息
  memory    知识库管理命令
  roadmap   路线图管理命令
  rule      规则管理命令
  status    项目状态管理命令
  task      任务管理命令
  template  模板管理命令
```

要查看具体命令组的详细用法，请使用：

```bash
vibecopilot <命令组名称> --help
```
例如，查看 `roadmap` 命令组的帮助信息：

```bash
vibecopilot roadmap --help
```
要查看某个具体子命令的帮助信息，请使用：

```bash
vibecopilot <命令组名称> <子命令名称> --help
```
例如，查看 `roadmap sync` 子命令的帮助信息：

```bash
vibecopilot roadmap sync --help
```

### 与 Cursor IDE 集成

将以下配置添加到您工作区的 `.cursor/mcp.json` 文件中：

```json
{
    "mcpServers": {
      "vibecopilot-server": {
        "command": "uvx",
        "args": [
          "mcp-server-cursor",
          "--workspace",
          "${workspaceRoot}"
        ],
        "host": "127.0.0.1", # 根据实际情况配置
        "port": 5000        # 根据实际情况配置
      }
    }
}
```
然后重启 Cursor IDE。

## 📂 项目结构速览

* `/src`: 核心源代码
* `/config`: 配置文件 (.yaml, .json)
* `/docs`: 项目文档
* `/tests`: 测试代码
* `/.ai`: AI相关资源 (例如知识库存储)
* `/templates`: 各种生成模板

更多详细结构和规范请参考 `/docs/README.md`。

## 🤝 贡献

欢迎为 VibeCopilot 做出贡献！请阅读 [CONTRIBUTING.md](https://github.com/jacobcy/VibeCopilot/blob/main/CONTRIBUTING.md) 了解详细信息。我们遵循 [约定式提交规范](https://www.conventionalcommits.org/en/v1.0.0/) (`core-rules/convention`) 和强制开发流程检查点 (`dev-rules/flow`)。

(在此处可以添加更多具体的贡献指南，例如如何报告 Bug、提交 Pull Request 等，或者指引到 CONTRIBUTING.md 文件)

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](https://github.com/jacobcy/VibeCopilot/blob/main/LICENSE) 文件。
