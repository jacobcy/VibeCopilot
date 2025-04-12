# VibeCopilot 健康检查模块

## 模块说明

本模块提供了VibeCopilot系统的健康状态检查功能，可以检查系统各个组件的运行状态、完整性和性能。

## 模块结构

```
health/
├── __init__.py              # 模块入口
├── cli.py                   # 命令行接口
├── health_check.py          # 健康检查主类
├── config/                  # 配置文件目录
│   └── check_config.yaml    # 检查配置文件
├── checkers/                # 检查器模块目录
│   ├── __init__.py
│   ├── base_checker.py      # 基础检查器类
│   ├── command_checker.py   # 命令检查器
│   ├── database_checker.py  # 数据库检查器
│   ├── doc_checker.py       # 文档检查器
│   └── dependency_checker.py # 依赖检查器
└── reporters/               # 报告生成器
    ├── __init__.py
    ├── base_reporter.py
    ├── markdown_reporter.py
    └── json_reporter.py
```

## 使用方法

### 命令行使用

```bash
# 运行全部检查
python -m src.health.cli check

# 检查特定模块
python -m src.health.cli check --module database

# 生成详细的Markdown报告
python -m src.health.cli check --verbose --format markdown

# 使用自定义配置文件
python -m src.health.cli check --config path/to/config.yaml
```

### 配置文件

配置文件（check_config.yaml）定义了需要检查的项目：

```yaml
commands:
  required_commands:
    - name: "rule list"
      type: "rule"
      expected_output: ["规则列表"]

database:
  required_tables:
    - name: "rules"
      min_records: 1

documentation:
  required_readmes:
    - "src/db/README.md"
```

## 扩展开发

### 添加新的检查器

1. 在 `checkers` 目录下创建新的检查器类
2. 继承 `BaseChecker` 类
3. 实现 `check()` 方法
4. 在配置文件中添加相应的配置项

### 自定义报告格式

1. 在 `reporters` 目录下创建新的报告生成器
2. 继承 `BaseReporter` 类
3. 实现相应的报告生成方法

## 注意事项

1. 检查操作应该是只读的，不应修改任何系统状态
2. 配置文件中的路径应使用相对于项目根目录的路径
3. 检查超时时间默认为30秒，可在配置中调整
