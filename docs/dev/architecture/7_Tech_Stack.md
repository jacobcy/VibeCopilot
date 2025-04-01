# VibeCopilot 技术栈

> **文档元数据**
> 版本: 1.1
> 上次更新: 2024-04-20
> 负责人: 技术架构团队

## 1. 技术选型策略

VibeCopilot采用"不重复造轮子"的策略，通过集成高质量开源库实现核心功能：

1. **轻量级包装**：薄包装层统一接口，不重新实现功能
2. **保持更新同步**：定期与上游库同步，获取最新功能和修复
3. **贡献优先**：功能缺失时，优先向原项目贡献而非分叉
4. **插件化架构**：各组件通过标准接口和事件系统松耦合

## 2. 核心技术栈与模块映射

### 核心引擎模块

- **主要技术**: TypeScript/Node.js
- **核心库**: EventEmitter3, ajv, fs-extra
- **实现功能**: 模块注册与发现、事件总线、配置管理
- **映射功能**: 核心引擎(5_functions.md)

```typescript
// 核心引擎实现示例
class CoreEngine implements ICoreEngine {
  private modules = new Map<string, Module>();
  private eventBus = new EventEmitter();
  private configManager = new ConfigManager();

  registerModule(moduleId: string, module: Module): void {
    this.modules.set(moduleId, module);
    module.initialize(this);
  }

  publishEvent(eventType: string, payload: any): void {
    this.eventBus.emit(eventType, payload);
  }
}
```

### 文档同步引擎模块

- **基于**: obsidiosaurus
- **技术栈**: TypeScript, markdown-it, remark/rehype
- **实现功能**: 文档变更监控、双向同步、冲突解决
- **映射功能**: 文档同步引擎(5_functions.md)

### AI规则生成器模块

- **基于**: cursor-custom-agents-rules-generator
- **技术栈**: JavaScript, OpenAI API客户端
- **实现功能**: 规则模板管理、自定义规则生成、验证与部署
- **映射功能**: AI规则生成器(5_functions.md)

### GitHub集成模块

- **基于**: Octokit, gitdiagram
- **技术栈**: TypeScript, GitHub API
- **实现功能**: API交互、文档与Issues关联、项目分析
- **映射功能**: GitHub集成模块(5_functions.md)

### 工具连接器模块

- **技术栈**: TypeScript
- **核心库**: 适配器模式实现各工具连接
- **实现功能**: 工具发现与连接、状态监控、配置管理
- **映射功能**: 工具连接器(5_functions.md)

### Docusaurus发布系统

- **技术栈**: React, MDX, TailwindCSS
- **核心库**: Docusaurus, React组件库
- **实现功能**: 内容筛选、格式转换、站点生成与部署
- **映射功能**: Docusaurus发布系统(5_functions.md)

## 3. 技术基础设施

### 存储与数据管理

- **本地存储**: SQLite (轻量级、无需安装)
- **配置存储**: JSON/YAML文件 (与集成库兼容)
- **版本控制**: Git (通过simple-git与gitdiagram集成)

### 通信与集成层

- **事件总线**: EventEmitter3 (模块间通信)
- **依赖注入**: 自定义DI容器 (模块组合)
- **命令模式**: 自定义CommandBus (请求-响应通信)

### 测试与质量保证

- **JavaScript测试**: Jest
- **Python测试**: pytest (Python组件)
- **代码质量**: ESLint/Prettier, pre-commit钩子

## 4. 模块间通信实现

```typescript
// 事件总线实现
class EventBusImpl implements EventBus {
  private emitter = new EventEmitter3();

  publish(eventType: string, payload: any): void {
    this.emitter.emit(eventType, eventType, payload);
  }

  subscribe(eventType: string, handler: EventHandler): Subscription {
    this.emitter.on(eventType, handler);
    return {
      unsubscribe: () => this.emitter.off(eventType, handler),
      isActive: () => this.emitter.listenerCount(eventType) > 0
    };
  }
}

// 依赖注入实现
class DependencyContainerImpl implements DependencyContainer {
  private registry = new Map<symbol | string, any>();

  register<T>(token: symbol | string, implementation: Constructor<T> | T): void {
    this.registry.set(token, implementation);
  }

  resolve<T>(token: symbol | string): T {
    const impl = this.registry.get(token);
    if (typeof impl === 'function' && !Object.getOwnPropertySymbols(impl).includes(Symbol.for('singleton'))) {
      return this.createInstance(impl);
    }
    return impl;
  }
}
```

## 5. 技术整合策略

### 微内核架构

- 轻量级核心引擎
- 功能主要通过插件和模块提供
- 标准化扩展点系统
- 严格的接口定义和版本控制

### 渐进式采用

1. 核心系统最小可用版本
2. 逐步添加功能模块
3. 迭代改进接口和实现
4. 根据实际使用反馈调整技术栈

## 6. 技术债务追踪与管理

| 模块 | 技术债务 | 优先级 | 解决方案 |
|------|---------|--------|---------|
| 文档同步引擎 | 冲突解决算法需优化 | P1 | 采用三路合并算法改进 |
| GitHub集成 | 多平台支持(GitLab等) | P2 | 实现通用VCS适配器 |
| AI规则生成器 | 多模型支持 | P1 | 接口抽象，支持插件化模型 |
| 工具连接器 | VS Code集成 | P2 | 开发VS Code接口适配器 |

通过这种集成驱动的技术策略，VibeCopilot可以快速构建功能完备的系统，同时保持技术灵活性和可持续性，专注于创建一个无缝整合的协同系统。
