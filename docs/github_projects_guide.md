# VibeCopilot GitHub Projects使用指南

本指南提供了如何使用GitHub Projects管理VibeCopilot项目开发路线图的详细说明。

## 为什么使用GitHub Projects

GitHub Projects提供了与GitHub仓库紧密集成的项目管理能力，相比静态文档有以下优势：

- 实时反映项目进度
- 与Issues和Pull Requests直接关联
- 多种视图支持(看板、表格、甘特图等)
- 团队协作更便捷
- 自动化工作流

## VibeCopilot Roadmap项目设置

### 项目结构

VibeCopilot Roadmap项目使用以下结构：

1. **视图**
   - 看板视图：按开发阶段分组
   - 表格视图：所有任务的详细信息
   - 甘特图视图：时间线规划

2. **自定义字段**
   - 里程碑(M1-M5)：对应主要开发阶段
   - 优先级(P0-P3)：任务优先级
   - 估计工时：预计完成时间
   - 领域：功能所属模块

3. **状态列**
   - Backlog：未开始的任务
   - To Do：计划本次迭代完成的任务
   - In Progress：正在进行的任务
   - In Review：代码审核中
   - Done：已完成的任务

### 标签系统

我们使用以下标签体系组织任务：

- **里程碑标签**：milestone:M1, milestone:M2, ...
- **优先级标签**：priority:P0, priority:P1, ...
- **类型标签**：type:feature, type:bug, type:docs, ...
- **领域标签**：area:core, area:ai, area:cli, ...

## 使用工作流

### 1. 添加新任务

1. 创建GitHub Issue，填写详细描述
2. 添加相应标签
3. 将Issue添加到Project中
4. 设置自定义字段值(里程碑、优先级等)
5. 将任务放在适当的状态列

### 2. 任务开发过程

1. 开发者从To Do列选择任务
2. 将任务移至In Progress，并分配给自己
3. 创建功能分支(格式：`feature/issue-number-brief-description`)
4. 完成开发后提交PR，在PR描述中使用`Fixes #issue-number`语法
5. PR审核通过并合并后，任务自动移至Done列

### 3. 迭代计划

1. 在每个迭代开始，将本迭代计划完成的任务从Backlog移至To Do
2. 在迭代会议中讨论任务优先级和分配
3. 在迭代结束时审查完成和未完成的任务
4. 调整下一个迭代的计划

### 4. 路线图更新

1. 定期(如每月)审查路线图进度
2. 根据实际进展调整任务时间线和优先级
3. 更新里程碑的预计完成日期
4. 添加新识别的任务，移除不再相关的任务

## 自动化规则

我们配置了以下自动化规则简化工作流：

1. 当PR与Issue关联并合并后，自动将Issue移至Done
2. 当Issue被分配给开发者，自动将状态更新为In Progress
3. 当Issue添加了"blocked"标签，自动添加到"Blocked"视图
4. 每周自动生成进度报告

## 最佳实践

- 保持Issue描述详细具体，包含验收标准
- 使用检查表(checklist)跟踪子任务进度
- 在PR中参考相关Issue
- 定期更新Issue状态反映真实进度
- 使用Issue讨论功能进行相关讨论
- 保持Project视图整洁，及时归档完成的任务

## 报告与可视化

GitHub Projects提供了多种报告和可视化功能：

- 使用甘特图视图查看时间线和依赖关系
- 使用燃尽图跟踪迭代进度
- 按里程碑或优先级筛选任务
- 导出数据进行自定义报告

---

通过这种方式，我们可以将VibeCopilot的开发路线图从静态文档转变为动态管理工具，提高团队协作效率和项目透明度。
