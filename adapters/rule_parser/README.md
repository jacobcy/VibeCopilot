# 规则解析器

规则解析器（Rule Parser）是VibeCopilot的核心组件之一，用于将Markdown格式的规则文件解析为结构化数据，以便规则引擎能够使用。

## 功能

- 解析Markdown格式的规则文件
- 支持使用OpenAI或Ollama作为解析引擎
- 检测规则之间的冲突

## 环境配置

规则解析器支持以下环境变量配置：

```
# 规则解析配置
VIBE_RULE_PARSER=openai  # openai, ollama - 规则解析使用的引擎
VIBE_OPENAI_MODEL=gpt-4o-mini  # 使用OpenAI解析规则时的模型
VIBE_OLLAMA_MODEL=llama3  # 使用Ollama解析规则时的模型
VIBE_OLLAMA_BASE_URL=http://localhost:11434  # Ollama服务地址
```

此外，如果使用OpenAI解析引擎，还需要设置：

```
OPENAI_API_KEY=your_openai_api_key
```

## 使用方法

### 命令行工具

规则解析器提供了命令行工具，可以直接解析规则文件并进行冲突检测。

```bash
# 解析规则文件
python -m adapters.rule_parser.main parse path/to/rule.md [--parser openai|ollama] [--model model_name] [--output output.json] [--pretty]

# 检测规则冲突
python -m adapters.rule_parser.main check-conflict path/to/rule1.md path/to/rule2.md [--parser openai|ollama] [--pretty]

# 检查环境配置
python -m adapters.rule_parser.main check-env
```

### 在代码中使用

```python
# 解析规则文件
from adapters.rule_parser.utils import parse_rule_file

# 使用默认解析器（根据环境变量 VIBE_RULE_PARSER 决定）
result = parse_rule_file("/path/to/rule.md")

# 指定解析器和模型
result = parse_rule_file("/path/to/rule.md", "openai", "gpt-4o-mini")

# 检测规则冲突
from adapters.rule_parser.utils import detect_rule_conflicts

rule1 = parse_rule_file("/path/to/rule1.md")
rule2 = parse_rule_file("/path/to/rule2.md")
conflict_result = detect_rule_conflicts(rule1, rule2)
```

### 在规则引擎中使用

规则引擎通过`src.core.rule_adapter`模块使用规则解析器：

```python
from src.core.rule_adapter import parse_markdown_rule

# 解析规则并转换为规则引擎期望的格式
rule = parse_markdown_rule("/path/to/rule.md")
```

## 规则文件格式

规则文件使用Markdown格式，可以包含以下内容：

### Front Matter（YAML头部）

```markdown
---
id: rule-id
name: 规则名称
type: manual
description: 规则描述
globs: ["*.ts", "*.tsx"]
always_apply: true
---
```

### 规则条目

使用HTML注释标记规则条目：

```markdown
<!-- BLOCK START id=rule-item-1 type=rule -->
**R1: TypeScript命名约定**

* 接口名称必须以I开头
* 类型名称必须使用PascalCase
* 变量和函数必须使用camelCase
<!-- BLOCK END -->
```

### 示例

使用HTML注释标记示例：

```markdown
<!-- BLOCK START id=example-1 type=example -->
```typescript
// 好的示例
interface IUserProps {
  firstName: string;
  lastName: string;
}
```
<!-- BLOCK END -->
```

## 开发者指南

如需添加新的解析器类型，请在`adapters/rule_parser`目录中创建新的解析器类，并在`parser_factory.py`中注册该解析器。
