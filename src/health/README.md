# VibeCopilot 健康检查模块

## 模块说明

本模块提供了VibeCopilot系统的健康状态检查功能，是一个轻量级的系统完整性检查工具。主要用于：

1. 验证系统命令和参数的存在性
2. 检查基础组件的可用性
3. 确保配置文件的完整性
4. 验证文档结构的完整性

注意：本工具不是功能测试工具，不替代 pytest 等测试框架。具体的功能性测试、单元测试和集成测试仍需要使用 pytest 进行。

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
# 基本命令格式
python -m src.health.cli check [OPTIONS]

# 可用选项：
# --module [system|command|database|all]  选择要检查的模块
# --category TEXT                        命令类别（仅用于命令检查）
# --verbose                             显示详细信息

# 使用示例：

# 运行全部检查
python -m src.health.cli check --module all

# 仅检查命令模块
python -m src.health.cli check --module command

# 检查特定类别的命令
python -m src.health.cli check --module command --category flow

# 显示详细检查信息
python -m src.health.cli check --verbose

# 运行所有检查并生成Markdown格式报告
python -m src.health.cli check --format markdown --output health_report.md

# 只检查数据库并输出为纯文本格式
python -m src.health.cli check --module database --format text

# 检查特定命令类别
python -m src.health.cli check --module command --category 任务管理
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
4. 本工具仅进行命令完整性和基础可用性检查，不涉及具体业务逻辑测试
5. 功能性测试应使用 pytest 进行，包括：
   - 单元测试
   - 集成测试
   - 端到端测试
   - 性能测试
6. 建议将本工具作为 CI/CD 流程的预检步骤，在主要测试之前运行
