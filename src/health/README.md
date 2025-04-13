# VibeCopilot 健康检查模块

## 模块说明

本模块提供了VibeCopilot系统的健康状态检查功能，是一个轻量级的系统完整性检查工具。主要用于：

1. 验证系统命令和参数的存在性
2. 检查基础组件的可用性
3. 确保配置文件的完整性
4. 验证文档结构的完整性
5. 监控系统状态和健康度

注意：本工具不是功能测试工具，不替代 pytest 等测试框架。具体的功能性测试、单元测试和集成测试仍需要使用 pytest 进行。

## 模块结构

```
health/
├── __init__.py              # 模块入口
├── cli.py                   # 命令行接口
├── health_check.py          # 健康检查主类
├── status_api.py            # Status模块状态查询API
├── result_publisher.py      # 检查结果发布器
├── config/                  # 配置文件目录
│   ├── check_config.yaml    # 检查配置文件
│   └── status_check_config.yaml # 状态检查配置文件
├── checkers/                # 检查器模块目录
│   ├── __init__.py
│   ├── base_checker.py      # 基础检查器类
│   ├── command_checker.py   # 命令检查器
│   ├── database_checker.py  # 数据库检查器
│   ├── system_checker.py    # 系统检查器
│   ├── status_checker.py    # 状态模块检查器
│   ├── doc_checker.py       # 文档检查器
│   └── dependency_checker.py # 依赖检查器
└── reporters/               # 报告生成器
    ├── __init__.py
    ├── base_reporter.py
    ├── markdown_reporter.py
    └── json_reporter.py
```

## 与Status模块集成

健康检查模块与状态管理模块(Status)实现了松耦合集成，基于事件订阅模式，主要包括：

1. **结果发布机制**：健康检查结果通过`result_publisher.py`发布为事件，被Status模块订阅
2. **状态查询API**：通过`status_api.py`提供查询Status模块状态的接口，避免直接依赖
3. **状态检查器**：`status_checker.py`通过API查询Status模块状态，执行相关健康检查

### 数据流向

```
┌─────────────────┐      检查结果事件      ┌─────────────────┐
│                 │───────────────────────>│                 │
│  Health 模块    │                        │  Status 模块    │
│                 │<───────────────────────│                 │
└─────────────────┘      状态查询API       └─────────────────┘
```

### 检查结果发布

检查器在执行检查后，可以通过`result_publisher.py`将结果发布到Status模块：

```python
from src.health.checkers.base_checker import CheckResult
from src.health.result_publisher import publish_health_check_result

# 创建检查结果
result = CheckResult(
    status="passed",  # 可选: passed, warning, failed
    details=["检查通过"],
    suggestions=["可优化建议"],
    metrics={"response_time": 30}
)

# 发布结果
publish_health_check_result("checker_name", result)
```

### 状态查询

可通过`status_api.py`查询Status模块的状态：

```python
from src.health.status_api import get_status_health

# 获取整体状态
status_health = get_status_health()

# 获取特定领域状态
task_status = get_status_health(domain="task")
```

## 使用方法

### 命令行使用

```bash
# 基本命令格式
python -m src.health.cli check [OPTIONS]

# 可用选项：
# --module [system|command|database|status|all]  选择要检查的模块
# --category TEXT                        命令类别（仅用于命令检查）
# --verbose                             显示详细信息
# --format [text|markdown|json]        报告输出格式
# -o, --output TEXT               报告输出文件路径，不指定则输出到控制台
# --help                          Show this message and exit.

# 使用示例：

# 运行全部检查
python -m src.health.cli check --module all

# 仅检查命令模块
python -m src.health.cli check --module command

# 检查特定类别的命令
python -m src.health.cli check --module command --category flow

# 检查状态模块健康状态
python -m src.health.cli check --module status

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

### 状态检查配置

状态检查配置文件（status_check_config.yaml）定义了状态检查的参数：

```yaml
# API查询配置
api:
  timeout: 5           # 查询超时(秒)
  retry_count: 2       # 失败重试次数
  retry_interval: 1    # 重试间隔(秒)

# 健康度评估配置
health_evaluation:
  min_overall_health: 65  # 最低整体健康度
  critical_domains:       # 关键领域列表及最低健康度
    - domain: "task"
      min_health: 70
    - domain: "workflow"
      min_health: 70

# 结果发布配置
result_publishing:
  enabled: true    # 是否发布检查结果
  retry_count: 1   # 发布重试次数
```

## 扩展开发

### 添加新的检查器

1. 在 `checkers` 目录下创建新的检查器类
2. 继承 `BaseChecker` 类
3. 实现 `check()` 方法
4. 在配置文件中添加相应的配置项
5. 如需发布结果，可以使用基类中的 `_publish_result()` 方法

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
7. 发布健康检查结果到Status模块是可选功能，可通过配置禁用
8. 健康模块与状态模块通过事件机制和API接口交互，避免直接依赖
