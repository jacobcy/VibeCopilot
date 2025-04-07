# Status 模块

## 简介

Status 模块是 VibeCopilot 的核心状态管理中心，负责统一管理和同步系统中各个领域的状态信息。它采用发布-订阅模式，将状态提供者和状态订阅者解耦，为整个系统提供一致的状态视图。

## 架构设计

```
┌───────────────┐      ┌──────────────┐      ┌─────────────────┐
│ 状态生产者     │──────▶│  Status模块  │──────▶│   状态订阅者    │
│ (Roadmap模块) │      │              │      │ (Status_Sync)   │
│ (Workflow模块) │      │              │      │                │
└───────────────┘      └──────────────┘      └─────────────────┘
                             │                        │
                             │                        ▼
                             │                ┌─────────────────┐
                             │                │   外部系统      │
                             │                │    (n8n)        │
                             ▼                └─────────────────┘
                      ┌──────────────┐
                      │   状态查询    │
                      │   (API)      │
                      └──────────────┘
```

### 核心组件

1. **StatusService**: 中央状态服务，管理状态提供者和订阅者
2. **IStatusProvider**: 状态提供者接口，由各领域模块实现
3. **IStatusSubscriber**: 状态订阅者接口，用于响应状态变更
4. **状态枚举**: 定义各领域的状态常量

## 模块结构

```
src/status/
├── __init__.py        # 模块入口，导出主要组件
├── enums.py           # 状态枚举定义
├── interfaces.py      # 接口定义
├── README.md          # 本文档
├── service.py         # 状态服务实现
└── providers/         # 状态提供者实现
    ├── __init__.py
    ├── roadmap_provider.py
    └── workflow_provider.py
```

## 主要接口

### IStatusProvider

```python
class IStatusProvider(Protocol):
    """状态提供者接口"""

    @property
    def domain(self) -> str:
        """获取领域名称"""
        ...

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取状态信息"""
        ...

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新状态"""
        ...

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出实体"""
        ...
```

### IStatusSubscriber

```python
class IStatusSubscriber(Protocol):
    """状态订阅者接口"""

    def on_status_changed(
        self,
        domain: str,
        entity_id: str,
        old_status: str,
        new_status: str,
        context: Dict[str, Any]
    ) -> None:
        """状态变更处理"""
        ...
```

## 使用方法

### 获取系统状态

```python
from src.status import StatusService

status_service = StatusService.get_instance()
# 获取系统整体状态
system_status = status_service.get_system_status()

# 获取特定领域状态
roadmap_status = status_service.get_domain_status("roadmap")
workflow_status = status_service.get_domain_status("workflow", workflow_id)
```

### 更新状态

```python
from src.status import StatusService, WorkflowStatus

status_service = StatusService.get_instance()
# 更新工作流状态
result = status_service.update_status(
    domain="workflow",
    entity_id=workflow_id,
    status=WorkflowStatus.ACTIVE
)
```

### 实现状态提供者

```python
from src.status.interfaces import IStatusProvider

class CustomStatusProvider(IStatusProvider):
    @property
    def domain(self) -> str:
        return "custom_domain"

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        # 实现获取状态的逻辑
        ...

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        # 实现更新状态的逻辑
        ...

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        # 实现列出实体的逻辑
        ...

# 注册到状态服务
status_service = StatusService.get_instance()
status_service.register_provider(CustomStatusProvider())
```

### 实现状态订阅者

```python
from src.status.interfaces import IStatusSubscriber

class CustomSubscriber(IStatusSubscriber):
    def on_status_changed(
        self,
        domain: str,
        entity_id: str,
        old_status: str,
        new_status: str,
        context: Dict[str, Any]
    ) -> None:
        # 实现状态变更处理逻辑
        print(f"状态变更: {domain}/{entity_id}: {old_status} -> {new_status}")

# 注册到状态服务
status_service = StatusService.get_instance()
status_service.register_subscriber(CustomSubscriber())
```

## 后续开发方向

1. **扩展状态提供者**：
   - 为更多领域添加状态提供者，如任务状态、项目状态等
   - 丰富现有提供者的功能，如添加状态历史记录

2. **增强订阅机制**：
   - 添加状态变更过滤功能，允许订阅者只关注特定领域或状态变更
   - 实现事件队列，提高系统吞吐量和稳定性

3. **系统集成**：
   - 与通知系统集成，提供状态变更通知
   - 提供API接口，允许外部系统查询和更新状态

4. **性能优化**：
   - 状态缓存机制，减少数据库访问
   - 批量状态更新支持

5. **监控与日志**：
   - 状态变更审计日志
   - 状态健康监控面板

6. **API集成**：
   - REST API接口，用于查询和更新状态
   - WebSocket支持，用于实时状态推送

## 最佳实践

1. **状态定义**：所有状态应在`enums.py`中集中定义，避免硬编码
2. **错误处理**：状态提供者和订阅者应妥善处理异常，避免影响整个应用
3. **状态一致性**：确保状态变更的原子性，避免状态不一致
4. **性能考虑**：状态订阅者的处理逻辑应尽量轻量，避免阻塞

## 示例流程

以下是一个工作流状态变更的完整流程示例：

1. 用户通过API请求激活工作流
2. Workflow模块更新工作流状态为"active"
3. Workflow模块调用Status服务的`update_status`方法
4. Status服务通知所有订阅者状态已变更
5. StatusSyncSubscriber接收通知并处理状态变更
6. StatusSyncSubscriber使用N8n适配器将状态同步到n8n系统
7. 状态变更完成，各系统状态一致
