# Health模块与Status模块集成文档

## 概述

本文档说明Health模块与Status模块的集成方案实现。该集成基于事件订阅模式，实现了两个模块的松耦合通信，避免了循环依赖问题，同时保持了两个模块的独立性。

## 集成架构

```
┌─────────────────┐      检查结果事件      ┌─────────────────┐
│                 │───────────────────────>│                 │
│  Health 模块    │                        │  Status 模块    │
│                 │<───────────────────────│                 │
└─────────────────┘      状态查询API       └─────────────────┘
```

## 关键组件

### Status模块

1. **健康检查订阅者 (HealthCheckSubscriber)**
   - 路径: `src/status/subscribers/health_check_subscriber.py`
   - 功能: 订阅Health模块发布的检查结果事件
   - 原理: 当Health模块发布检查结果时，更新Status模块中的健康状态

2. **健康状态提供者 (HealthProvider)**
   - 路径: `src/status/providers/health_provider.py`
   - 功能: 提供聚合的健康检查状态
   - 原理: 整合Health模块的检查结果，提供统一的健康状态查询接口

### Health模块

1. **结果发布器 (result_publisher)**
   - 路径: `src/health/result_publisher.py`
   - 功能: 将Health模块的检查结果发布为事件
   - 原理: 转换检查结果为Status模块可理解的格式，并发布为事件

2. **状态查询API (status_api)**
   - 路径: `src/health/status_api.py`
   - 功能: 提供查询Status模块状态的API
   - 原理: 通过API调用获取Status模块信息，避免直接依赖

3. **状态检查器 (StatusChecker)**
   - 路径: `src/health/checkers/status_checker.py`
   - 功能: 检查Status模块的健康状态
   - 原理: 通过API查询Status模块状态，而非直接依赖

## 数据流向

1. **Health → Status**:
   - Health模块执行检查产生结果
   - 结果通过`publish_health_check_result`发布为事件
   - Status模块的`HealthCheckSubscriber`接收事件并更新健康状态

2. **Status → Health**:
   - Health模块的`StatusChecker`需要检查Status模块状态
   - 通过`status_api.get_status_health`查询Status模块
   - 分析结果并生成健康检查报告

## 集成优势

1. **避免循环依赖**:
   - 通过事件机制和API接口实现松散集成
   - 避免了模块间的直接依赖

2. **错误隔离**:
   - 任一模块出错不会直接导致另一模块崩溃
   - 提供了优雅降级的错误处理机制

3. **可扩展性**:
   - 可轻松添加新的健康检查维度
   - 可方便地集成更多模块到健康监控系统

## 使用示例

### 在Status模块中获取Health检查结果

```python
# 直接查询健康领域状态
from src.status.service import get_domain_status

# 获取Health检查器结果
health_status = get_domain_status("health")
print(f"整体健康状态: {health_status['overall_status']}")

# 获取特定检查器结果
checker_status = get_domain_status("health", entity_id="database")
print(f"数据库健康状态: {checker_status['status']}")
```

### 在Health模块中获取Status模块状态

```python
# 通过API查询Status模块状态
from src.health.status_api import get_status_health

# 获取整体状态
status_health = get_status_health()
print(f"状态模块整体健康度: {status_health['overall_health']}")

# 获取特定领域状态
task_status = get_status_health(domain="task")
print(f"任务领域健康度: {task_status['health']}")
```

### 发布健康检查结果

```python
from src.health.checkers.base_checker import CheckResult
from src.health.result_publisher import publish_health_check_result

# 创建检查结果
result = CheckResult(
    status="passed",  # 可选: passed, warning, failed
    details=["测试通过", "响应时间: 30ms"],
    suggestions=["可以考虑优化缓存"],
    metrics={"response_time": 30, "success_rate": 100}
)

# 发布结果
publish_health_check_result("api_checker", result)
```

## 配置说明

### 状态检查配置

配置文件路径: `src/health/config/status_check_config.yaml`

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

## 测试方法

集成测试脚本: `src/tests/health_status_integration_test.py`

执行以下命令运行测试:

```bash
cd /path/to/project
python -m src.tests.health_status_integration_test
```

## 常见问题

1. **Status模块初始化失败**
   - 检查`src/status/__init__.py`中的初始化代码
   - 确保所有依赖组件可用

2. **结果发布失败**
   - 检查`src/health/result_publisher.py`中导入的Status服务函数
   - 查看日志中的详细错误信息

3. **无法查询Status状态**
   - 检查`src/health/status_api.py`中的导入路径
   - 确保Status模块正确初始化
