# Memory 工具使用教程

## 会话信息

- 日期：2024-04-01
- 主题：Memory 工具使用教程与演示
- 目的：展示如何使用 Memory 工具保存和查询项目信息

## 演示流程

### 1. 信息保存流程

#### 1.1 创建实体

```typescript
// 创建会话实体
mcp_memory_docker_create_entities({
  name: "memory_demo_session_20240401",
  entityType: "conversation",
  observations: [...]
})

// 创建技术栈实体
mcp_memory_docker_create_entities({
  name: "VibeCopilot::tech_stack",
  entityType: "technology",
  observations: [...]
})
```

#### 1.2 建立关系

```typescript
// 建立实体间关系
mcp_memory_docker_create_relations({
  from: "VibeCopilot::tech_stack",
  to: "VibeCopilot::tech_stack::core_engine",
  relationType: "包含"
})
```

### 2. 信息查询方法

#### 2.1 搜索节点

```typescript
// 搜索特定实体
mcp_memory_docker_search_nodes({
  query: "VibeCopilot::tech_stack"
})
```

#### 2.2 打开节点

```typescript
// 查看具体实体详情
mcp_memory_docker_open_nodes({
  names: ["VibeCopilot::tech_stack::core_engine"]
})
```

## 最佳实践

### 1. 实体命名规范

- 使用命名空间方式：`项目::类别::名称`
- 包含时间戳：`名称_YYYYMMDD`
- 使用有意义的实体类型

### 2. 关系建立原则

- 明确关系类型
- 保持关系的单向性
- 避免冗余关系

### 3. 查询技巧

- 使用精确的查询词
- 结合多个查询方法
- 通过关系图谱导航

## 示例成果

本次演示成功保存了：

1. 项目技术栈信息
2. 核心模块设计
3. 模块间关系
4. 技术实现细节

## 后续建议

1. 定期更新知识图谱
2. 保持实体关系的清晰性
3. 及时清理过时信息
4. 建立完整的文档关联

## 相关文档

- [技术栈文档](../dev/architecture/7_Tech_Stack.md)
- [模块设计文档](../dev/architecture/6_modules.md)
