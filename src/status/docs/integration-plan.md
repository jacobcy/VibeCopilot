# Status模块与Health模块集成方案（基于事件订阅模式）

## 方案概述

本方案旨在利用Status模块的发布-订阅架构特性，实现Status模块与Health模块的松耦合集成。通过事件订阅机制，两个模块可以互相获取对方的信息，同时避免循环依赖问题，实现系统状态与健康的统一监控与评估。

## 集成目标

1. 轻量化整合，保持两个模块的独立性
2. 利用Status模块的订阅式架构实现松耦合设计
3. 避免模块间的循环依赖
4. 实现双向数据流：Health检查结果流向Status，Status状态信息流向Health
5. 统一系统健康报告格式，便于监控和问题诊断

## 主要实现内容

### 1. 健康检查结果订阅者(HealthCheckSubscriber)

在Status模块中新增订阅者，订阅Health模块的检查结果：

```python
from src.status.interfaces import IStatusSubscriber
from src.status.core.health_calculator import HealthCalculator

class HealthCheckSubscriber(IStatusSubscriber):
    """健康检查结果订阅者

    订阅health模块的检查结果，并更新状态管理器中的健康状态
    """

    def __init__(self):
        self.health_calculator = HealthCalculator()

    def on_status_changed(self, domain: str, entity_id: str, old_status: str,
                         new_status: str, data: Dict[str, Any]) -> None:
        """状态变更回调

        当health模块发布检查结果时被调用

        Args:
            domain: 领域名称（"health_check"）
            entity_id: 实体ID（检查模块名称）
            old_status: 旧状态
            new_status: 新状态（通过/警告/失败）
            data: 检查结果详情
        """
        if domain == "health_check":
            # 更新health_calculator中的组件健康状态
            components = data.get("components", {})
            for component, health_data in components.items():
                self.health_calculator.update_component_health(
                    component,
                    {
                        "health": health_data.get("health", 70),
                        "level": health_data.get("level", "good"),
                        "message": health_data.get("message", "健康检查完成")
                    }
                )

            # 记录健康检查事件
            logger.info(f"健康检查结果已更新: {entity_id} 状态为 {new_status}")
```

### 2. 健康检查结果发布机制

在Health模块中添加结果发布功能，将检查结果发布为事件：

```python
def publish_health_check_result(checker_name: str, result: CheckResult):
    """发布健康检查结果

    将health模块的检查结果转换为状态事件并发布

    Args:
        checker_name: 检查器名称
        result: 检查结果
    """
    from src.status.service import publish_status_change

    # 将健康检查结果转换为status模块期望的格式
    status_data = {
        "components": {},
        "details": result.details,
        "suggestions": result.suggestions
    }

    # 转换metrics为组件健康数据
    for key, value in result.metrics.items():
        if isinstance(value, dict):
            status_data["components"][key] = value
        else:
            # 对于简单指标，创建默认组件结构
            status_data["components"][key] = {
                "health": 100 if result.status == "passed" else (70 if result.status == "warning" else 40),
                "level": result.status,
                "message": f"{key}: {value}"
            }

    # 发布状态变更事件
    publish_status_change(
        domain="health_check",
        entity_id=checker_name,
        old_status="unknown",
        new_status=result.status,
        data=status_data
    )
```

### 3. 状态提供者(HealthProvider)

在Status模块中创建健康状态提供者，聚合来自Health检查的结果：

```python
from src.status.interfaces import IStatusProvider

class HealthProvider(IStatusProvider):
    """健康状态提供者

    提供来自health模块的健康检查状态
    """

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "health"

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取健康状态

        Args:
            entity_id: 可选，检查器名称。不提供则获取整体健康状态。

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        # 从某个持久化存储或缓存中获取最新的健康检查结果
        # 这里简化处理，实际实现应考虑持久化存储

        if entity_id:
            # 返回特定检查器的状态
            return {
                "domain": self.domain,
                "entity_id": entity_id,
                "status": "...",  # 从存储中获取
                "last_check": "...",
                "details": []
            }
        else:
            # 返回聚合的健康状态
            return {
                "domain": self.domain,
                "overall_status": "...",
                "checkers": [],
                "last_updated": "..."
            }

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新健康状态（可能由health模块直接调用）"""
        # 实现状态更新逻辑
        pass

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出健康检查器"""
        # 实现列出实体的逻辑
        pass
```

### 4. 状态查询接口(StatusAPI)

为Health模块提供一个查询Status状态的简单API，避免直接依赖：

```python
# src/health/status_api.py

from typing import Dict, Any, Optional

def get_status_health(domain: Optional[str] = None) -> Dict[str, Any]:
    """获取状态模块的健康信息

    Args:
        domain: 可选，特定领域的状态

    Returns:
        Dict[str, Any]: 状态健康信息
    """
    try:
        from src.status.service import get_domain_status

        if domain:
            return get_domain_status(domain)
        else:
            # 获取所有领域的状态
            # 实际实现可能需要调用多个API并聚合结果
            return {"overall_health": 0, "domains": []}
    except ImportError:
        # Status模块不可用时的优雅降级
        return {"error": "Status module unavailable", "overall_health": 0}
```

### 5. 修改StatusChecker实现

更新StatusChecker，通过API查询Status模块状态：

```python
class StatusChecker(BaseChecker):
    """状态模块健康检查器，通过API查询状态"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def check(self) -> CheckResult:
        """执行status模块健康检查"""
        from src.health.status_api import get_status_health

        details = []
        suggestions = []
        metrics = {}

        try:
            # 通过API获取状态健康信息
            status_health = get_status_health()

            if "error" in status_health:
                details.append(f"状态模块查询错误: {status_health['error']}")
                suggestions.append("请检查status模块是否正常运行")
                return CheckResult(
                    status="failed",
                    details=details,
                    suggestions=suggestions,
                    metrics={"error": status_health["error"]}
                )

            # 处理状态健康信息
            overall_health = status_health.get("overall_health", 0)
            domains = status_health.get("domains", [])

            # 添加详情
            details.append(f"状态模块整体健康度: {overall_health}")
            for domain in domains:
                details.append(f"领域[{domain['name']}]健康度: {domain.get('health', 0)}")

            # 设置指标
            metrics["overall_health"] = overall_health
            metrics["domain_count"] = len(domains)

            # 确定检查结果状态
            if overall_health < 50:
                status = "failed"
                suggestions.append("状态模块健康度严重不足，请检查系统状态")
            elif overall_health < 70:
                status = "warning"
                suggestions.append("状态模块健康度存在警告，建议关注系统状态")
            else:
                status = "passed"

            # 发布健康检查结果
            self._publish_result("status", CheckResult(
                status=status,
                details=details,
                suggestions=suggestions,
                metrics=metrics
            ))

            return CheckResult(
                status=status,
                details=details,
                suggestions=suggestions,
                metrics=metrics
            )

        except Exception as e:
            details.append(f"状态检查过程发生错误: {str(e)}")
            suggestions.append("请检查status模块是否正常运行")
            return CheckResult(
                status="failed",
                details=details,
                suggestions=suggestions,
                metrics={"error": str(e)}
            )

    def _publish_result(self, checker_name: str, result: CheckResult):
        """发布检查结果到状态系统"""
        try:
            from src.health.result_publisher import publish_health_check_result
            publish_health_check_result(checker_name, result)
        except (ImportError, Exception) as e:
            logger.warning(f"发布检查结果失败: {str(e)}")
```

## 注册和配置

### 1. 注册健康检查订阅者

在status模块初始化时注册健康检查订阅者：

```python
# src/status/__init__.py

from src.status.subscribers.health_check_subscriber import HealthCheckSubscriber
from src.status.core.subscriber_manager import SubscriberManager

def initialize():
    # 其他初始化代码...

    # 注册健康检查订阅者
    subscriber_manager = SubscriberManager()
    subscriber_manager.register_subscriber(HealthCheckSubscriber())
```

### 2. 配置文件更新

更新status_check_config.yaml，适配新设计：

```yaml
# 状态模块健康检查配置

# API查询配置
api:
  # 查询超时(秒)
  timeout: 5
  # 失败重试次数
  retry_count: 2
  # 重试间隔(秒)
  retry_interval: 1

# 健康度评估配置
health_evaluation:
  # 最低整体健康度
  min_overall_health: 65
  # 关键领域列表及最低健康度
  critical_domains:
    - domain: "task"
      min_health: 70
    - domain: "workflow"
      min_health: 70

# 结果发布配置
result_publishing:
  # 是否发布检查结果
  enabled: true
  # 发布重试次数
  retry_count: 1
```

## 集成流程

### 数据流向图

```
┌─────────────────┐      检查结果事件      ┌─────────────────┐
│                 │───────────────────────>│                 │
│  Health 模块    │                        │  Status 模块    │
│                 │<───────────────────────│                 │
└─────────────────┘      状态查询API       └─────────────────┘
```

### 实现步骤

1. 在Status模块中创建HealthCheckSubscriber类
2. 在Health模块中创建结果发布功能和状态查询API
3. 在Status模块中创建HealthProvider类
4. 修改StatusChecker实现，使用API查询状态
5. 在模块初始化时注册订阅者
6. 更新配置文件和文档

## 优势分析

1. **避免循环依赖**：
   - Status模块不直接依赖Health模块的内部实现
   - Health模块通过API查询Status状态，不依赖具体实现

2. **松耦合设计**：
   - 通过事件机制和API接口实现松散集成
   - 任一模块变更不会直接影响另一模块

3. **容错性**：
   - 一个模块不可用不会导致另一个模块完全失效
   - 提供了优雅降级的错误处理

4. **可扩展性**：
   - 可轻松添加新的健康检查维度
   - 可方便地集成更多模块到健康监控系统

## 总结

通过利用Status模块的发布-订阅架构特性，实现了Status与Health模块的松耦合集成。这种基于事件的设计避免了循环依赖问题，同时实现了双向数据流：Health检查结果可以流向Status系统，Status的状态信息也可以被Health模块获取。这种设计不仅满足了轻量级集成的需求，还提高了系统的可维护性和可扩展性。
