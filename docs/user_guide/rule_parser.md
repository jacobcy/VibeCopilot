# 规则解析器用户指南

## 概述

规则解析器是VibeCopilot的核心组件，允许用户通过解析Markdown格式的规则文件，实现规则的结构化管理和冲突检测。本工具支持使用OpenAI和Ollama两种解析引擎，并提供简单易用的命令行接口。

## 主要功能

- **规则解析**：将Markdown规则文件解析为结构化JSON数据
- **冲突检测**：检测两个规则之间的冲突并提供详细说明
- **环境检查**：验证环境配置及解析器可用性
- **多种引擎**：支持OpenAI（主要）和Ollama（备选）引擎

## 基本操作

### 环境配置检查

检查环境变量配置和解析器可用性：

```bash
python -m adapters.rule_parser.main check-env
```

示例输出：
```
环境变量状态:
  OPENAI_API_KEY: ✅ 已设置
  VIBE_OPENAI_MODEL: ✅ 已设置 gpt-4o-mini
  VIBE_RULE_PARSER: ✅ 已设置 openai
  VIBE_OLLAMA_MODEL: ✅ 已设置 llama3
  VIBE_OLLAMA_BASE_URL: ✅ 已设置 http://localhost:11434

可用解析器:
  OpenAI解析器: ✅ 可用
  Ollama解析器: ✅ 可用
```

### 解析规则文件

解析单个规则文件并输出结构化数据：

```bash
python -m adapters.rule_parser.main parse <规则文件路径> [--pretty]
```

参数说明：

- `<规则文件路径>`: 要解析的规则文件路径
- `--pretty`: 美化输出的JSON格式（可选）

示例：
```bash
python -m adapters.rule_parser.main parse rules/coding-flow.md --pretty
```

### 检测规则冲突

检测两个规则文件之间的潜在冲突：

```bash
python -m adapters.rule_parser.main check-conflict <规则文件1> <规则文件2> [--pretty]
```

参数说明：

- `<规则文件1>`, `<规则文件2>`: 要检测冲突的两个规则文件
- `--pretty`: 美化输出的JSON格式（可选）

示例：
```bash
python -m adapters.rule_parser.main check-conflict rules/rule1.md rules/rule2.md --pretty
```

## 常见问题

1. **OpenAI API密钥未设置**
   - 检查`.env`文件中是否正确设置了`OPENAI_API_KEY`
   - 运行`python -m adapters.rule_parser.main check-env`验证配置

2. **规则解析失败**
   - 确保规则文件格式正确，包含Front Matter部分
   - 检查文件路径是否正确
   - 尝试切换解析器（在`.env`中修改`VIBE_RULE_PARSER`）

3. **Ollama解析器不可用**
   - 确保本地Ollama服务正在运行
   - 验证`.env`中的`VIBE_OLLAMA_BASE_URL`设置
   - 检查网络连接

## 环境变量设置

系统使用以下环境变量进行配置：

| 环境变量 | 描述 | 默认值 |
|---------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | 无（必须设置） |
| `VIBE_RULE_PARSER` | 默认解析器类型（openai/ollama） | openai |
| `VIBE_OPENAI_MODEL` | 使用的OpenAI模型 | gpt-4o-mini |
| `VIBE_OLLAMA_MODEL` | 使用的Ollama模型 | llama3 |
| `VIBE_OLLAMA_BASE_URL` | Ollama服务地址 | <http://localhost:11434> |

可以通过修改项目根目录的`.env`文件来设置这些环境变量。
