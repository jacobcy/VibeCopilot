# 工作流与阶段关系映射

## 工作流定义结构

VibeCopilot 支持多种工作流类型，每种工作流定义包含特定的阶段类型：

| 工作流类型 | 描述 | 可用阶段类型 |
|----------|-----|-------------|
| dev | 软件开发工作流 | story, spec, coding, test, review |
| research | 研究工作流 | investigation, analysis, reporting, optimization |
| design | 设计工作流 | discovery, ideation, prototyping, testing |
| docs | 文档创作工作流 | planning, drafting, review, publishing |

工作流定义是静态的模板，描述：

- 工作流包含哪些阶段
- 每个阶段的名称、说明和检查清单
- 阶段之间的依赖关系和顺序
- 阶段的交付物定义

## 工作流会话结构

工作流会话是工作流定义的运行实例，记录实际执行情况：

| 会话状态 | 描述 | 可执行操作 |
|---------|-----|-----------|
| ACTIVE | 会话处于活动状态，可继续执行阶段 | run, pause, abort |
| PAUSED | 会话已暂停，需要恢复后才能继续 | resume, abort, delete |
| COMPLETED | 会话已完成所有阶段 | delete, view |
| ABORTED | 会话被终止，不能继续执行 | delete, view |

工作流会话具有以下特性：

- **动态性**：会话状态会随着执行进度变化
- **持久性**：会话信息持久化存储，可以随时恢复
- **上下文**：会话维护一个共享上下文，在各阶段之间传递数据
- **进度追踪**：记录每个阶段的完成情况和总体进度

## 工作流定义与会话关系

- 一个工作流定义可以创建多个会话实例
- 会话实例基于工作流定义中的阶段创建阶段实例
- 会话记录阶段实例的执行状态和进度
- 阶段实例的状态变更会影响会话状态
- 会话的进度基于已完成的阶段实例数量

## 重要命令说明

### flow context 命令

`flow context` 命令用于获取特定工作流阶段的完整上下文信息。

**使用场景**：

- 当需要查看当前阶段的完整配置、要求和进度时
- 当需要恢复之前中断的工作时
- 当需要了解一个阶段的详细设置和已完成的工作项时

**命令格式**：
```bash
vibecopilot flow context <workflow_id> <stage_name> [--session=<session_id>]
```

**参数说明**：

- `workflow_id`: 工作流定义的ID
- `stage_name`: 阶段名称
- `--session`: (可选)指定工作流会话ID，如果提供，将显示该会话中指定阶段的实例上下文

### flow next 命令

`flow next` 命令用于基于当前工作流状态，智能推荐下一个应该执行的阶段。

**使用场景**：

- 当完成当前阶段，想知道应该进行哪个阶段时
- 当需要工作流引导，不确定下一步该做什么时
- 在复杂工作流中需要依赖关系指导时

**命令格式**：
```bash
vibecopilot flow next <session_id> [--current=<current_stage_instance_id>]
```

**参数说明**：

- `session_id`: 工作流会话ID
- `--current`: (可选)当前阶段实例ID，如果不提供，系统将基于会话中的最新状态推荐

### flow visualize 命令

`flow visualize` 命令用于生成工作流会话的可视化图表，展示阶段依赖关系和执行状态。

**使用场景**：

- 当需要直观了解工作流结构时
- 当需要查看当前执行进度和状态时
- 当需要分享工作流概览给团队成员时

**命令格式**：
```bash
vibecopilot flow visualize <session_id>
```

**参数说明**：

- `session_id`: 工作流会话ID

## 工作流命令示例

以下是工作流定义和会话管理的常见用法示例：

### 创建和查看工作流定义

```bash
# 创建新的开发工作流定义
vibecopilot flow create dev --name="用户认证开发流程" --desc="处理用户认证功能开发的标准流程"

# 输出
✅ 已创建工作流定义
- 工作流ID: dev-workflow-123
- 名称: 用户认证开发流程
- 类型: dev
- 阶段数: 5 (story, spec, coding, test, review)

# 查看工作流定义详情
vibecopilot flow show dev-workflow-123

# 输出
🔹 工作流定义: 用户认证开发流程 (ID: dev-workflow-123)
- 类型: dev
- 描述: 处理用户认证功能开发的标准流程
- 创建时间: 2023-06-15 10:30

阶段列表:
1. story - 用户故事和需求收集
2. spec - 技术规格和架构设计
3. coding - 代码实现
4. test - 测试验证
5. review - 代码审核和优化
```

### 启动工作流会话和执行阶段

```bash
# 创建一个新的工作流会话
vibecopilot flow session create dev-workflow-123 --name="用户登录功能开发"

# 输出
✅ 已创建工作流会话
- 会话ID: dev-session-abc123
- 名称: 用户登录功能开发
- 基于工作流: dev-workflow-123 (用户认证开发流程)
- 状态: ACTIVE

# 在会话中运行第一个阶段(story)
vibecopilot flow run dev:story --session=dev-session-abc123 --name="用户登录需求分析"

# 输出
✅ 已在会话中启动story阶段
- 会话ID: dev-session-abc123
- 阶段实例ID: dev-story-def456
- 名称: 用户登录需求分析
- 当前阶段: story
- 已保存会话状态和上下文

# 查看当前上下文和任务 (context命令示例)
vibecopilot flow context dev-workflow-123 story --session=dev-session-abc123

# 输出
📋 用户故事阶段工作指南
--------------------
🔍 阶段说明: 收集和明确用户需求

✅ 检查清单:
  1. 确定用户角色和权限 [已完成]
  2. 定义登录流程和边界情况 [已完成]
  3. 明确安全需求和验证方式 [进行中]

📦 交付物:
  1. 用户故事文档
  2. 验收标准

🔄 上下文数据:
  - 会话ID: dev-session-abc123
  - 阶段实例ID: dev-story-def456
  - 创建时间: 2023-06-15 10:35
  - 最后更新: 2023-06-15 11:30
```

### 会话管理操作

```bash
# 查看会话详情和进度
vibecopilot flow session show dev-session-abc123

# 输出
📋 工作流会话: dev-session-abc123 (用户登录功能开发)

基本信息:
- 基于工作流: dev-workflow-123 (用户认证开发流程)
- 状态: ACTIVE
- 创建时间: 2023-06-15 10:30
- 最后更新: 2023-06-15 11:45

阶段进度:
▶️ story (用户登录需求分析) - 进行中
⏳ spec - 待进行
⏳ coding - 待进行
⏳ test - 待进行
⏳ review - 待进行

当前阶段详情:
- 名称: 用户登录需求分析
- 开始时间: 2023-06-15 10:35
- 已完成项: 2/3 (67%)

# 暂停会话，稍后继续
vibecopilot flow session pause dev-session-abc123

# 输出
⏸️ 已暂停会话: dev-session-abc123
- 当前状态已保存
- 使用 'flow session resume' 命令继续此会话
```

### 继续执行会话中的下一阶段

```bash
# 恢复暂停的会话
vibecopilot flow session resume dev-session-abc123

# 输出
▶️ 已恢复会话: dev-session-abc123
- 状态: ACTIVE
- 当前阶段: story (用户登录需求分析)

# 使用next命令推荐下一步操作
vibecopilot flow next dev-session-abc123

# 输出
📋 推荐的下一阶段
-----------------
✅ 当前: story (用户登录需求分析) - 进行中 (67% 完成)
➡️ 建议操作: 完成当前story阶段后，执行spec阶段
📝 说明: 根据工作流依赖关系，完成story阶段后应进行spec阶段以定义技术实现规格
💡 执行命令: vibecopilot flow run dev:spec --session=dev-session-abc123

# 完成story阶段，继续执行spec阶段
vibecopilot flow run dev:spec --session=dev-session-abc123 --name="用户认证系统设计"

# 输出
✅ 已在会话中启动spec阶段
- 会话ID: dev-session-abc123
- 阶段实例ID: dev-spec-ghi789
- 名称: 用户认证系统设计
- story阶段已标记为完成
- 当前阶段: spec
- 会话进度: 20% (1/5 阶段已完成)
```

### 工作流可视化

```bash
# 生成工作流会话的可视化图表
vibecopilot flow visualize dev-session-abc123

# 输出
📊 工作流会话可视化 (dev-session-abc123)

```mermaid
graph TD
  story["用户故事阶段"] --> |完成| spec
  style story fill:#c3e6cb,stroke:#28a745

  spec["技术规格阶段"] --> |进行中| coding
  style spec fill:#fff3cd,stroke:#ffc107

  coding["代码实现阶段"] --> |未开始| test
  style coding fill:#f8f9fa,stroke:#6c757d

  test["测试阶段"] --> |未开始| review
  style test fill:#f8f9fa,stroke:#6c757d

  review["审核阶段"] --> |未开始| end
  style review fill:#f8f9fa,stroke:#6c757d

  end["完成"]
  style end fill:#f8f9fa,stroke:#6c757d
```

🔹 图例说明:

- 绿色: 已完成阶段
- 黄色: 进行中阶段
- 灰色: 未开始阶段
- 箭头: 阶段间依赖关系

📈 总体进度: 20% (1/5 阶段已完成)
