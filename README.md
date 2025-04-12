# VibeCopilot 模板生成系统

VibeCopilot 是一个强大的AI辅助开发工具，集成了模板生成、命令处理、规则管理等多个子系统。它提供了统一的命令接口，可以通过MCP协议在任何支持的项目中使用。

## 功能特点

- **多种生成器**: 支持基于正则表达式的本地生成和基于LLM的云端智能生成
- **变量验证**: 自动验证必需变量和变量类型
- **命令行界面**: 提供丰富的命令行工具管理和使用模板
- **模板管理**: 支持模板的导入、创建、更新和删除
- **多种输出格式**: 支持Markdown、JSON等多种输出格式
- **MCP服务器**: 提供标准的MCP接口，支持跨项目使用

Looking at the README.md, here's how to use VibeCopilot:

## Installation

First, install all dependencies:
```bash
pip install -r requirements.txt
```

For MCP server functionality, install as an editable uvx package:
```bash
uvx install-editable .
```

## Starting the MCP Server

Launch the MCP server with the following command:
```bash
uvx mcp-server-cursor --workspace /path/to/project
```

## Template Generation

Test template generation with the regex generator (default):
```bash
python test_template_generator.py templates/rule/command.md -v '{"name":"test_command","description":"A test command for demonstration"}'
```

Use the LLM generator by adding the `-g llm` flag:
```bash
python test_template_generator.py templates/rule/command.md -v '{"name":"test_command","description":"A test command for demonstration"}' -g llm
```

## Using with Cursor IDE

To use VibeCopilot in Cursor IDE, add this configuration to `.cursor/mcp.json`:
```json
{
    "mcpServers": {
      "cursor-command": {
        "command": "uvx",
        "args": [
          "mcp-server-cursor",
          "--workspace",
          "${workspaceRoot}"
        ]
      }
    }
}
```

## Command Line Tools

The template system offers several command line tools:
```bash
# List all templates
python -m src.commands.template.main list

# View a specific template
python -m src.commands.template.main show <template_id>

# Generate template content
python -m src.commands.template.main generate <template_id> --variables '{"name":"value"}'

# Import a template
python -m src.commands.template.main import <file_path>

# Load all templates from a directory
python -m src.commands.template.main load
```

## 命令行工具

模板系统提供了一套完整的命令行工具:

```bash
# 列出所有模板
python -m src.commands.template.main list

# 查看特定模板
python -m src.commands.template.main show <template_id>

# 生成模板内容
python -m src.commands.template.main generate <template_id> --variables '{"name":"value"}'

# 导入模板
python -m src.commands.template.main import <file_path>

# 加载目录中的所有模板
python -m src.commands.template.main load
```

## 项目结构

```
src/
├── commands/
│   └── template/       # 模板命令行工具
├── cursor/            # Cursor命令处理系统
│   ├── command/       # 命令处理核心
│   ├── server.py      # MCP服务器
│   └── command_handler.py  # 命令处理器
├── models/            # 数据模型
├── templates/
│   ├── core/         # 模板核心功能
│   └── generators/   # 模板生成器
│       ├── base_generator.py     # 生成器基类
│       ├── regex_generator.py    # 正则生成器
│       └── llm_generator.py      # LLM生成器
templates/
├── rule/            # 规则模板
└── doc/             # 文档模板
```

## 支持的功能

系统支持多种功能，包括:

- **规则模板**: 用于生成各类规则文档
- **文档模板**: 用于生成API文档、架构文档等
- **任务模板**: 用于生成任务描述和计划
- **命令处理**: 通过MCP服务器提供统一的命令接口
- **规则管理**: 管理和执行项目规则
- **工作流管理**: 管理项目工作流程

## 开发者指南

要扩展系统功能:

1. 添加新的模板生成器: 实现`TemplateGenerator`接口
2. 添加新的命令: 在`src/commands/template/commands.py`中注册新命令
3. 创建新模板: 在templates目录下创建符合规范的Markdown文件
4. 扩展MCP服务器: 在`src/cursor/server.py`中添加新的方法

## 许可证

本项目采用MIT许可证。

![CI](https://github.com/jacobcy/VibeCopilot/actions/workflows/ci.yml/badge.svg)
![Tests](https://github.com/jacobcy/VibeCopilot/actions/workflows/test-all.yml/badge.svg)
