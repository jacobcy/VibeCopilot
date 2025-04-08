# VibeCopilot 规则引擎

规则引擎是VibeCopilot的核心组件，负责规则的解析、验证、存储和生成等功能。

## 功能概述

- **规则解析**：将Markdown格式的规则文件解析为结构化数据
- **规则验证**：确保规则数据符合系统要求
- **规则存储**：将规则保存到数据库中
- **规则导出**：将规则导出为YAML或其他格式
- **规则生成**：基于模板生成新的规则

## 模块结构

```
src/rule_engine/
├── core/               # 核心功能
│   ├── rule_manager.py # 规则管理器
│   └── ...
├── parsers/            # 解析器
│   ├── rule_parser.py  # 规则解析
│   └── ...
├── validators/         # 验证器
│   ├── rule_validator.py # 规则验证
│   └── ...
├── exporters/          # 导出器
│   ├── yaml_exporter.py # YAML导出
│   └── ...
├── storage/            # 存储模块
│   ├── rule_repository.py # 规则仓库
│   └── ...
├── generators/         # 生成器模块
│   ├── rule_generator.py # 规则生成器
│   └── ...
└── main.py             # 模块入口
```

## 主要类和函数

### RuleManager

`RuleManager`是规则引擎的中心类，提供规则的完整生命周期管理：

```python
from src.rule_engine import RuleManager

# 初始化规则管理器
manager = RuleManager()

# 从文件导入规则
rule = manager.import_rule_from_file("path/to/rule.md")

# 从内容导入规则
rule_content = "---\nid: test_rule\ntype: rule\n---\n# Test Rule\n..."
rule = manager.import_rule_from_content(rule_content)

# 导出规则为YAML
yaml_str = manager.export_rule_to_yaml(rule.id)
```

### 解析和导出

也可以直接使用解析和导出函数：

```python
from src.rule_engine import parse_rule_file, export_rule_to_yaml

# 解析规则文件
rule_dict = parse_rule_file("path/to/rule.md")

# 导出为YAML
yaml_str = export_rule_to_yaml(rule_dict)
```

### 规则生成

使用模板生成规则：

```python
from src.rule_engine import generate_rule_from_template

# 生成规则
variables = {
    "command_name": "test",
    "description": "测试命令",
    "purpose": "用于测试功能"
}
rule_data = generate_rule_from_template("command", variables, "output_rule.md")
```

## 命令行使用

你可以通过命令行使用规则引擎的功能：

```bash
# 测试规则解析
python test_rule_engine_refactored.py path/to/rule.md

# 测试模板生成规则
python test_template_rule_generator.py command --vars '{"command_name":"test"}'

# 简化版模板生成
python test_template_rule_generator_simple.py templates/rule/command.md output.md --vars '{"command_name":"test"}'
```
