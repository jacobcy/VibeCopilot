# 状态系统与N8n自动化工作流集成开发计划

## 当前状态分析

### 已实现的组件

1. **N8n适配器**
   - N8nAdapter及其客户端类已完整实现，提供与N8n API的交互能力
   - 支持工作流、执行、凭证和变量管理

2. **状态同步适配器**
   - StatusSyncAdapter作为兼容层，委托实际工作给更专业的服务类
   - 基础服务类实现，包括WorkflowSync、ExecutionSync和N8nSync
   - StatusSyncSubscriber初步实现，可监听状态变更

3. **状态系统**
   - 已完成状态服务(StatusService)核心实现
   - 提供订阅机制和状态管理能力
   - 日志订阅者(LogSubscriber)已实现

### 缺失的组件与功能

1. **缺失集成注册**
   - 未将StatusSyncSubscriber注册到StatusService
   - 状态变更未能自动触发N8n工作流

2. **缺失配置与初始化**
   - 需要配置框架确保系统启动时自动建立集成
   - 针对不同开发环境的配置选项

3. **缺失触发机制**
   - 如何根据不同领域和状态变更触发不同的N8n工作流
   - 没有触发规则配置

4. **缺失错误处理与恢复机制**
   - 同步失败时的重试机制
   - 网络中断后的恢复机制

5. **缺失管理与监控**
   - 对集成状态的监控
   - 用户界面展示集成状态与历史

## 开发计划

### 第一阶段：基础集成（2周）

1. **实现状态系统与N8n的自动集成**

   ```python
   # src/app.py 或初始化脚本中
   def setup_status_n8n_integration():
       """设置状态系统与N8n的集成"""

       from adapters.status_sync.services.status_subscriber import StatusSyncSubscriber
       from src.status.service import StatusService
       from src.db import get_session

       # 创建状态同步订阅者
       session = get_session()
       status_subscriber = StatusSyncSubscriber(session)

       # 注册到状态系统
       status_service = StatusService.get_instance()
       status_service.register_subscriber(status_subscriber)

       logger.info("状态系统与N8n集成已设置")
   ```

2. **增强StatusSyncSubscriber**
   - 完善对所有领域状态变更的处理
   - 添加配置化规则系统决定哪些状态变更触发哪些工作流

3. **实现配置系统**
   - 在`src/core/config.py`增加N8n和状态同步相关配置
   - 支持从环境变量或配置文件加载配置

### 第二阶段：高级功能与错误处理（3周）

1. **实现重试与恢复机制**
   - 记录失败的同步请求
   - 实现定时任务重试失败的同步
   - 添加手动重试接口

2. **实现触发规则系统**
   - 基于领域、实体类型、状态变更定义触发规则
   - 支持条件触发和过滤

   ```python
   # 触发规则示例（配置或数据库形式）
   rules = [
       {
           "domain": "roadmap",
           "entity_types": ["task", "milestone"],
           "status_changes": [
               {"from": "*", "to": "completed", "workflow_id": "task-completed-notify"}
           ]
       },
       {
           "domain": "workflow",
           "entity_types": ["flow_session"],
           "status_changes": [
               {"from": "*", "to": "COMPLETED", "workflow_id": "flow-completed-actions"}
           ]
       }
   ]
   ```

3. **实现队列机制**
   - 使用消息队列处理状态同步请求
   - 防止同步过程阻塞主业务流程

### 第三阶段：监控与管理界面（2周）

1. **实现集成状态监控**
   - 记录同步历史
   - 统计成功/失败率
   - 性能监控

2. **实现管理接口**
   - 启用/禁用特定领域同步
   - 查看同步历史
   - 手动触发同步
   - 重置失败的同步

3. **实现Web管理界面**
   - 集成状态总览
   - 规则配置界面
   - 历史记录查询
   - 手动操作界面

## 技术实现细节

### 1. 状态同步数据模型

```python
# src/models/db/status_sync.py

class StatusSyncRule(Base):
    """状态同步规则"""

    __tablename__ = "status_sync_rules"

    id = Column(String(50), primary_key=True, default=generate_id)
    domain = Column(String(50), nullable=False)  # 领域
    entity_type = Column(String(50))  # 实体类型，可为空表示全部
    from_status = Column(String(50))  # 原状态，可为空表示全部
    to_status = Column(String(50), nullable=False)  # 新状态
    workflow_id = Column(String(50), nullable=False)  # 触发的工作流ID
    description = Column(Text)  # 规则描述
    is_active = Column(Boolean, default=True)  # 是否激活
    created_at = Column(String(50), default=lambda: get_current_time())
    updated_at = Column(String(50), default=lambda: get_current_time(), onupdate=lambda: get_current_time())

    def __repr__(self):
        return f"<StatusSyncRule {self.domain}/{self.entity_type}: {self.from_status}->{self.to_status}>"


class StatusSyncLog(Base):
    """状态同步日志"""

    __tablename__ = "status_sync_logs"

    id = Column(String(50), primary_key=True, default=generate_id)
    domain = Column(String(50), nullable=False)  # 领域
    entity_id = Column(String(50), nullable=False)  # 实体ID
    entity_type = Column(String(50))  # 实体类型
    old_status = Column(String(50))  # 原状态
    new_status = Column(String(50), nullable=False)  # 新状态
    workflow_id = Column(String(50))  # 触发的工作流ID
    execution_id = Column(String(50))  # 执行ID
    is_success = Column(Boolean, default=False)  # 同步是否成功
    error_message = Column(Text)  # 错误信息
    created_at = Column(String(50), default=lambda: get_current_time())

    def __repr__(self):
        return f"<StatusSyncLog {self.domain}/{self.entity_id}: {self.old_status}->{self.new_status}>"
```

### 2. 触发机制实现

```python
# adapters/status_sync/services/rule_matcher.py

class RuleMatcher:
    """规则匹配器，决定哪些状态变更触发哪些工作流"""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def match_rules(self, domain: str, entity_id: str, entity_type: str, old_status: str, new_status: str) -> List[Dict[str, Any]]:
        """匹配规则

        Args:
            domain: 领域
            entity_id: 实体ID
            entity_type: 实体类型
            old_status: 原状态
            new_status: 新状态

        Returns:
            匹配的规则列表
        """
        # 查询匹配的规则
        query = self.db_session.query(StatusSyncRule).filter(
            StatusSyncRule.domain == domain,
            StatusSyncRule.is_active == True
        )

        # 筛选实体类型
        query = query.filter(
            or_(
                StatusSyncRule.entity_type == None,
                StatusSyncRule.entity_type == entity_type
            )
        )

        # 筛选状态转换
        query = query.filter(
            or_(
                StatusSyncRule.from_status == None,
                StatusSyncRule.from_status == '*',
                StatusSyncRule.from_status == old_status
            ),
            StatusSyncRule.to_status == new_status
        )

        # 转换为字典列表
        return [
            {
                'id': rule.id,
                'workflow_id': rule.workflow_id,
                'domain': rule.domain,
                'entity_type': rule.entity_type
            }
            for rule in query.all()
        ]
```

### 3. 改进的状态同步订阅者

```python
# adapters/status_sync/services/status_subscriber.py

def on_status_changed(
    self,
    domain: str,
    entity_id: str,
    old_status: str,
    new_status: str,
    context: Dict[str, Any],
) -> None:
    """状态变更事件处理（改进版）

    Args:
        domain: 领域
        entity_id: 实体ID
        old_status: 原状态
        new_status: 新状态
        context: 上下文信息
    """
    logger.info(f"状态变更: {domain}/{entity_id}: {old_status} -> {new_status}")

    try:
        # 获取实体类型
        entity_type = context.get("type", "unknown")

        # 匹配规则
        rule_matcher = RuleMatcher(self.db_session)
        matched_rules = rule_matcher.match_rules(
            domain, entity_id, entity_type, old_status, new_status
        )

        if not matched_rules:
            logger.debug(f"无匹配规则: {domain}/{entity_id}")
            return

        # 初始化N8n适配器
        from adapters.n8n.adapter import N8nAdapter
        from src.core.config import settings

        n8n_adapter = None
        if settings.n8n.enabled:
            n8n_adapter = N8nAdapter(
                base_url=settings.n8n.api_url, api_key=settings.n8n.api_key
            )
        else:
            logger.debug("N8n未启用，跳过状态同步")
            return

        # 记录日志
        sync_log = StatusSyncLog(
            domain=domain,
            entity_id=entity_id,
            entity_type=entity_type,
            old_status=old_status,
            new_status=new_status
        )

        # 对每个匹配规则，触发相应工作流
        from adapters.status_sync.services.execution_sync import ExecutionSync

        execution_sync = ExecutionSync(self.db_session, n8n_adapter)

        for rule in matched_rules:
            workflow_id = rule["workflow_id"]
            sync_log.workflow_id = workflow_id

            # 准备执行参数
            params = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "old_status": old_status,
                "new_status": new_status,
                "domain": domain,
                "timestamp": context.get("updated_at", ""),
                "context": context
            }

            # 创建执行
            execution_id = execution_sync.create_execution(workflow_id, params)

            if execution_id:
                logger.info(f"触发工作流执行: {workflow_id} (execution: {execution_id})")
                sync_log.execution_id = execution_id
                sync_log.is_success = True
            else:
                logger.warning(f"触发工作流执行失败: {workflow_id}")
                sync_log.error_message = "触发工作流执行失败"

            # 保存日志
            self.db_session.add(sync_log)
            self.db_session.commit()

    except Exception as e:
        logger.exception(f"同步状态时发生错误: {e}")
        # 保存错误日志
        try:
            sync_log = StatusSyncLog(
                domain=domain,
                entity_id=entity_id,
                entity_type=context.get("type", "unknown"),
                old_status=old_status,
                new_status=new_status,
                error_message=str(e)
            )
            self.db_session.add(sync_log)
            self.db_session.commit()
        except Exception:
            logger.exception("保存错误日志失败")
```

## 项目时间线

| 阶段 | 任务 | 时间估计 | 开始日期 | 结束日期 |
|-----|------|---------|---------|---------|
| 1 | 基础集成 | 2周 | 2023-04-15 | 2023-04-28 |
| 1.1 | 实现状态系统与N8n的自动集成 | 3天 | 2023-04-15 | 2023-04-17 |
| 1.2 | 增强StatusSyncSubscriber | 4天 | 2023-04-18 | 2023-04-21 |
| 1.3 | 实现配置系统 | 3天 | 2023-04-22 | 2023-04-24 |
| 1.4 | 测试与文档 | 4天 | 2023-04-25 | 2023-04-28 |
| 2 | 高级功能与错误处理 | 3周 | 2023-04-29 | 2023-05-19 |
| 2.1 | 实现重试与恢复机制 | 5天 | 2023-04-29 | 2023-05-03 |
| 2.2 | 实现触发规则系统 | 7天 | 2023-05-04 | 2023-05-10 |
| 2.3 | 实现队列机制 | 5天 | 2023-05-11 | 2023-05-15 |
| 2.4 | 测试与文档 | 4天 | 2023-05-16 | 2023-05-19 |
| 3 | 监控与管理界面 | 2周 | 2023-05-20 | 2023-06-02 |
| 3.1 | 实现集成状态监控 | 3天 | 2023-05-20 | 2023-05-22 |
| 3.2 | 实现管理接口 | 4天 | 2023-05-23 | 2023-05-26 |
| 3.3 | 实现Web管理界面 | 5天 | 2023-05-27 | 2023-05-31 |
| 3.4 | 测试与文档 | 2天 | 2023-06-01 | 2023-06-02 |

## 总结

当前的状态与N8n集成只实现了基础的适配器和服务类，但缺少将二者连接起来的关键环节。本开发计划提出了一个三阶段的实现方案，从基础集成到高级功能，再到监控与管理。通过实现这些功能，我们可以实现状态变更自动触发相应的N8n工作流，实现业务流程的自动化。
