# VibeCopilot 工作流用户指南

## 简介

VibeCopilot 工作流模块是一个轻量级的工作流指导工具，它能帮助您在开发过程中遵循标准化的流程和最佳实践。工作流基于 VibeCopilot 的规则系统自动生成，为您提供清晰的开发步骤、检查清单和交付物列表。

本指南将帮助您快速上手使用工作流功能，无需深入了解复杂的技术细节。

## 快速开始

### 1. 安装

确保您已安装 VibeCopilot：

```bash
# 如果尚未安装
pip install vibecopilot
```

### 2. 查看可用工作流

```bash
vibecopilot flow list
```

这将显示系统中所有可用的工作流。

### 3. 开始一个工作流

例如，要开始测试流程：

```bash
vibecopilot flow test
```

系统会自动加载测试工作流，并显示当前阶段的信息、检查清单和交付物。

## 常用命令

### 查看不同类型的工作流

VibeCopilot 支持多种预定义的工作流类型：

```bash
vibecopilot flow story    # 故事开发流程
vibecopilot flow spec     # 规格设计流程
vibecopilot flow coding   # 编码实现流程
vibecopilot flow test     # 测试流程
vibecopilot flow review   # 代码审查流程
vibecopilot flow commit   # 代码提交流程
```

### 跟踪工作流进度

在执行工作流时，您可以指定当前阶段和已完成的检查项：

```bash
vibecopilot flow test --stage test_execution --completed "准备测试环境" "编写测试用例"
```

这会更新工作流的当前状态，并为您提供下一步要做的任务。

### 导出工作流

您可以导出工作流为 JSON 或 Mermaid 图：

```bash
# 导出为 JSON
vibecopilot flow export test-workflow --format json --output test-flow.json

# 导出为 Mermaid 图
vibecopilot flow export test-workflow --format mermaid --output test-flow.md
```

Mermaid 图可以直接在 Markdown 文件中显示，方便您分享工作流程图。

## 工作流的组成部分

每个工作流包含以下主要组件：

1. **阶段 (Stages)**：工作流分为多个有序阶段，每个阶段代表一个开发步骤。
2. **检查清单 (Checklists)**：每个阶段包含一系列需要完成的任务。
3. **交付物 (Deliverables)**：每个阶段需要产出的文档或代码。
4. **转换 (Transitions)**：定义从一个阶段到另一个阶段的条件。

## 通过 Cursor 使用工作流

在 Cursor IDE 中，您可以使用斜杠命令快速访问工作流功能：

```
/flow list       # 列出所有工作流
/flow test       # 开始测试流程
/flow coding     # 开始编码流程
```

Cursor 代理会解析您的命令并执行相应的工作流操作，显示结果和下一步指导。

## 示例：完整的测试流程

下面是使用测试工作流的一个完整例子：

1. 开始测试准备阶段：
   ```bash
   vibecopilot flow test
   ```

2. 完成了解需求和准备环境：
   ```bash
   vibecopilot flow test --completed "理解需要测试的功能和预期行为" "准备测试环境和测试数据"
   ```

3. 进入测试执行阶段：
   ```bash
   vibecopilot flow test --stage test_execution
   ```

4. 完成单元测试和集成测试：
   ```bash
   vibecopilot flow test --stage test_execution --completed "执行单元测试并验证覆盖率" "执行集成测试验证组件交互"
   ```

5. 最后完成测试分析：
   ```bash
   vibecopilot flow test --stage test_analysis
   ```

每一步，系统都会为您提供当前进度、下一步任务和交付物提醒。

## 提示与技巧

- **配合规则使用**：工作流基于 VibeCopilot 的规则系统。查看规则可以帮助您更好地理解工作流的要求。
- **保持更新**：定期运行 `flow list` 查看是否有新的工作流可用。
- **结合状态系统**：工作流可以与 VibeCopilot 的状态系统集成，自动记录开发进度。
- **自定义工作流**：高级用户可以通过创建新的规则文件来定义自己的工作流。

## 常见问题

**Q: 我可以创建自定义工作流吗？**

A: 是的，您可以通过创建新的规则文件，然后使用 `vibecopilot flow create` 命令将其转换为工作流。

**Q: 如何查看某个工作流的详细信息？**

A: 使用 `vibecopilot flow view <workflow_id>` 命令可以查看工作流的完整定义。

**Q: 工作流是否会执行实际的操作？**

A: 不会。工作流是一个指导工具，它告诉您应该做什么，但不会自动执行任何操作。具体的开发工作仍然需要您手动完成。

**Q: 我可以在不同的项目中使用相同的工作流吗？**

A: 是的，工作流是通用的，可以应用于任何项目。但是，对于特定项目的需求，您可能需要创建自定义工作流。

---

希望本指南能帮助您充分利用 VibeCopilot 的工作流功能，提高开发效率和质量。如有更多问题，请查看开发者指南或联系支持团队。
