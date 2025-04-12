# Memory系统改造计划

## 一、现状分析

### 1.1 当前架构

- 独立的Memory系统(`src/memory/`)
  - EntityManager: 知识实体管理
  - ObservationManager: 观察记录管理
  - RelationManager: 关系管理
  - SyncService: 同步服务
- 独立的MemoryItem存储(`src/db/models/memory_item.py`)
  - 基础的记忆项存储
  - 简单的标签和搜索功能

### 1.2 存在问题

1. 系统割裂
   - Memory系统与MemoryItem存储未打通
   - 数据存在重复存储风险
   - 检索接口不统一

2. 功能局限
   - 缺乏语义理解能力
   - 没有向量检索支持
   - 关系管理能力有限

3. 性能问题
   - 全文检索效率低
   - 缺乏缓存机制
   - 大数据量下可能存在性能瓶颈

## 二、改造目标

### 2.1 核心目标

1. 统一存储层
   - 将MemoryItem改造为索引结构
   - 统一管理本地存储和Basic Memory
   - 提供统一的检索接口

2. 增强语义能力
   - 集成向量数据库
   - 支持语义相似度搜索
   - 提供上下文关联能力

3. 优化性能
   - 引入缓存机制
   - 优化检索算法
   - 支持异步操作

### 2.2 具体指标

- 检索响应时间 < 100ms
- 语义相似度准确率 > 85%
- 系统吞吐量提升50%
- 存储空间优化30%

## 三、改造方案

### 3.1 存储层改造

1. 升级MemoryItem模型
   ```python
   class MemoryItem(Base):
       # 已完成改造，包含:
       - 基础元数据
       - 分类和标签
       - 存储位置
       - 关系映射
       - 向量表示
   ```

2. 引入向量数据库
   - 使用Milvus/Faiss作为向量存储
   - 实现向量索引和检索
   - 提供向量运算API

### 3.2 Manager层改造

1. EntityManager增强

```python
class EntityManager:
    def __init__(self):
        self.memory_repo = MemoryItemRepository()
        self.vector_store = VectorStore()

    async def create_entity(self, data: Dict):
        # 创建实体
        entity = await super().create_entity(data)
        # 创建索引
        await self.memory_repo.create(
            title=data["name"],
            summary=data["description"],
            category="entity",
            storage_type="basic_memory",
            storage_location=entity["id"]
        )
        return entity
```

2. ObservationManager增强

```python
class ObservationManager:
    async def record_observation(self, data: Dict):
        # 记录观察
        observation = await super().record_observation(data)
        # 创建索引
        await self.memory_repo.create(
            title=data["title"],
            summary=data["content"],
            category="observation",
            storage_type="basic_memory",
            storage_location=observation["id"]
        )
        return observation
```

3. RelationManager增强

```python
class RelationManager:
    async def create_relation(self, data: Dict):
        # 创建关系
        relation = await super().create_relation(data)
        # 更新相关索引
        await self.memory_repo.update_refs(
            entity_refs=[data["source_id"], data["target_id"]],
            relation_refs=[relation["id"]]
        )
        return relation
```

### 3.3 服务层改造

1. 同步服务升级

```python
class SyncService:
    async def sync_all(self):
        # 同步Basic Memory数据
        await self.sync_basic_memory()
        # 更新向量索引
        await self.update_vector_index()
        # 验证数据一致性
        await self.verify_consistency()
```

2. 新增缓存服务

```python
class CacheService:
    def __init__(self):
        self.cache = Redis()
        self.ttl = 3600  # 1小时过期

    async def get_or_create(self, key: str, creator: Callable):
        if cached := await self.cache.get(key):
            return cached
        value = await creator()
        await self.cache.set(key, value, ex=self.ttl)
        return value
```

## 四、实施步骤

### 4.1 第一阶段：基础改造

1. [x] 升级MemoryItem模型
2. [x] 改造MemoryItemRepository
3. [ ] 添加数据迁移脚本
4. [ ] 实现基础缓存机制

### 4.2 第二阶段：功能增强

1. [ ] 集成向量数据库
2. [ ] 实现向量检索
3. [ ] 升级Manager层
4. [ ] 改造同步服务

### 4.3 第三阶段：性能优化

1. [ ] 优化检索算法
2. [ ] 实现批量操作
3. [ ] 添加性能监控
4. [ ] 压力测试和调优

## 五、风险与应对

### 5.1 潜在风险

1. 数据迁移风险
   - 数据丢失或不一致
   - 迁移过程中断
   - 回滚困难

2. 性能风险
   - 向量检索性能不达标
   - 缓存策略不当
   - 内存占用过高

3. 兼容性风险
   - API接口变更
   - 依赖库冲突
   - 客户端适配问题

### 5.2 应对措施

1. 数据安全
   - 实施增量迁移
   - 保留完整备份
   - 提供回滚机制

2. 性能保障
   - 分批处理数据
   - 设置监控告警
   - 提供降级方案

3. 兼容处理
   - 保持API向后兼容
   - 提供过渡期支持
   - 完善文档说明

## 六、后续规划

### 6.1 功能扩展

1. 知识图谱可视化
2. 智能推荐系统
3. 自动标签生成

### 6.2 持续优化

1. 定期性能评估
2. 用户反馈收集
3. 迭代优化方案

## 七、评估指标

### 7.1 功能指标

- [ ] 索引覆盖率 100%
- [ ] 检索准确率 > 90%
- [ ] API向后兼容性 100%

### 7.2 性能指标

- [ ] 检索响应时间 < 100ms
- [ ] 系统吞吐量 > 1000 QPS
- [ ] 缓存命中率 > 80%

### 7.3 可靠性指标

- [ ] 系统可用性 > 99.9%
- [ ] 数据一致性 100%
- [ ] 故障恢复时间 < 5分钟
