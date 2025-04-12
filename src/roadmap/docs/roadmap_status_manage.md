# Roadmap 状态管理实现

## 状态数据持久化

VibeCopilot 路线图模块采用了可靠的状态持久化机制，确保系统重启或终端关闭后能够保持活动路线图的选择状态。

### 持久化机制

1. **系统配置存储**：活动路线图ID保存在`system_configs`表中
   - 使用键值对形式存储：`key = "active_roadmap_id"`, `value = "<roadmap_id>"`
   - 确保状态在会话间持久保持

2. **数据模型**：使用`SystemConfig`模型和`SystemConfigRepository`管理配置项
   - `SystemConfig`: 定义基本的键值对存储模型
   - `SystemConfigRepository`: 提供获取、设置和更新配置值的方法

3. **加载流程**：
   - `RoadmapService`初始化时自动从数据库加载活动路线图ID
   - 验证加载的路线图ID是否有效，无效则清除该配置

### 核心实现

1. **初始化加载**：
   ```python
   # RoadmapService中实现
   def _load_active_roadmap_id(self) -> None:
       """从数据库加载活动路线图ID"""
       config = self.config_repo.get_by_key("active_roadmap_id")
       if config and config.value:
           # 验证路线图存在
           self._active_roadmap_id = config.value
   ```

2. **切换机制**：
   ```python
   # 路线图切换时保证持久化
   def set_active_roadmap(self, roadmap_id: str) -> bool:
       """设置活动路线图ID并持久化"""
       # 更新或创建配置记录
       self.config_repo.set_value("active_roadmap_id", roadmap_id)
       # 确保提交事务
       self.session.commit()
   ```

3. **状态一致性**：
   - 所有路线图切换和创建操作确保及时更新持久化状态
   - 事务保证状态更新的原子性，避免数据不一致
   - 失败情况下进行回滚，避免错误状态

### 状态服务集成

活动路线图状态已完全集成到Status模块，通过以下方式检索状态：

1. **RoadmapStatusProvider**从`RoadmapService`获取活动路线图ID
2. 使用ID获取状态概览并提供给状态服务
3. 状态服务通过统一接口展示路线图状态

### 防错机制

1. **无效状态处理**：系统自动检测并清除无效的路线图ID配置
2. **事务安全**：所有状态更新操作使用事务保证原子性
3. **异常处理**：全面的异常捕获和日志记录，确保系统稳定性

通过这种机制，路线图状态管理实现了会话间的持久化，确保用户体验的连贯性和系统状态的可靠性。
