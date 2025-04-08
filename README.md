# VibeCopilot 模板生成系统

VibeCopilot 模板生成系统是一个强大的工具，用于根据预定义模板和变量生成各种类型的文档，包括规则、文档和其他内容。该系统支持本地正则替换和云端LLM生成两种方式，满足不同场景的需求。

## 功能特点

- **多种生成器**: 支持基于正则表达式的本地生成和基于LLM的云端智能生成
- **变量验证**: 自动验证必需变量和变量类型
- **命令行界面**: 提供丰富的命令行工具管理和使用模板
- **模板管理**: 支持模板的导入、创建、更新和删除
- **多种输出格式**: 支持Markdown、JSON等多种输出格式

## 安装使用

```bash
# 安装依赖
pip install -r requirements.txt

# 测试模板生成
python test_template_generator.py templates/rule/command.md -v '{"name":"test_command","description":"A test command for demonstration"}'

# 使用LLM生成器
python test_template_generator.py templates/rule/command.md -v '{"name":"test_command","description":"A test command for demonstration"}' -g llm
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
├── models/             # 数据模型
├── templates/
│   ├── core/           # 模板核心功能
│   └── generators/     # 模板生成器
│       ├── base_generator.py       # 生成器基类
│       ├── regex_generator.py      # 正则生成器
│       └── llm_generator.py        # LLM生成器
templates/
├── rule/               # 规则模板
└── doc/                # 文档模板
```

## 支持的模板类型

系统支持多种模板类型，包括:

- **规则模板**: 用于生成各类规则文档
- **文档模板**: 用于生成API文档、架构文档等
- **任务模板**: 用于生成任务描述和计划

## 开发者指南

要扩展模板系统功能:

1. 添加新的模板生成器: 实现`TemplateGenerator`接口
2. 添加新的命令: 在`src/commands/template/commands.py`中注册新命令
3. 创建新模板: 在templates目录下创建符合规范的Markdown文件

## 许可证

本项目采用MIT许可证。

![CI](https://github.com/jacobcy/VibeCopilot/actions/workflows/ci.yml/badge.svg)
![Tests](https://github.com/jacobcy/VibeCopilot/actions/workflows/test-all.yml/badge.svg)
