
# VibeCopilot 路线图命令参考文档 (更新版)

## 概述

VibeCopilot提供了一系列命令用于管理项目路线图，包括创建、导入、验证、同步和导出功能。本文档详细说明各命令的用法、参数和示例。

## 命令列表

### 1. `validate` - 验证路线图YAML文件

验证路线图YAML文件格式与内容是否符合规范。

```bash
# 基本用法
vibecopilot roadmap validate --source <yaml文件路径>

# 验证并自动修复
vibecopilot roadmap validate --source <yaml文件路径> --fix

# 验证并输出到新文件
vibecopilot roadmap validate --source <yaml文件路径> --fix --output <修复后文件路径>

# 使用自定义模板验证
vibecopilot roadmap validate --source <yaml文件路径> --template <模板文件路径>

# 详细输出
vibecopilot roadmap validate --source <yaml文件路径> --verbose
```

**参数说明：**

- `--source` (必填): YAML文件路径
- `--fix` (可选): 自动修复格式问题
- `--output` (可选): 修复后输出的文件路径
- `--template` (可选): 使用自定义模板进行验证
- `--verbose` (可选): 输出详细信息

### 2. `import` - 导入路线图YAML文件

从YAML文件导入路线图数据，支持创建新路线图或更新现有路线图。

```bash
# 导入新路线图
vibecopilot roadmap import --source <yaml文件路径>

# 导入到现有路线图
vibecopilot roadmap import --source <yaml文件路径> --roadmap-id <路线图ID>

# 导入并自动修复
vibecopilot roadmap import --source <yaml文件路径> --fix

# 导入并设为当前活动路线图
vibecopilot roadmap import --source <yaml文件路径> --activate
```

**参数说明：**

- `--source` (必填): YAML文件路径
- `--roadmap-id` (可选): 现有路线图ID，不提供则创建新路线图
- `--fix` (可选): 自动修复导入过程中的格式问题
- `--activate` (可选): 导入后设为当前活动路线图
- `--verbose` (可选): 输出详细信息

### 3. `list` - 列出路线图

列出系统中的路线图元素或所有路线图。

```bash
# 列出当前活动路线图中的元素
vibecopilot roadmap list

# 列出所有路线图及活动状态
vibecopilot roadmap list --all

# 显示详细信息
vibecopilot roadmap list --detail

# 按状态筛选
vibecopilot roadmap list --status <状态>

# 按类型筛选元素
vibecopilot roadmap list --type <milestone|story|task>

# 按负责人筛选
vibecopilot roadmap list --assignee <用户名>

# 格式化输出
vibecopilot roadmap list --format <json|text|table>
```

**参数说明：**

- `--all` (可选): 列出所有路线图及其活动状态，而非当前路线图中的元素
- `--detail` (可选): 显示详细信息
- `--type` (可选): 筛选元素类型 (milestone, story, task, all)
- `--status` (可选): 按状态筛选
- `--assignee` (可选): 按负责人筛选
- `--labels` (可选): 按标签筛选，多个标签用逗号分隔
- `--format` (可选): 输出格式（json, text, table）
- `--verbose` (可选): 输出详细信息

### 4. `show` - 查看路线图详情

显示路线图详细信息，包括里程碑、任务和进度。

```bash
# 查看当前活动路线图
vibecopilot roadmap show

# 查看指定路线图
vibecopilot roadmap show --id <路线图ID>

# 查看特定里程碑
vibecopilot roadmap show --id <路线图ID> --milestone <里程碑ID>

# 查看特定任务
vibecopilot roadmap show --id <路线图ID> --task <任务ID>

# 检查健康状态
vibecopilot roadmap show --id <路线图ID> --health
```

**参数说明：**

- `--id` (可选): 路线图ID，不提供则使用当前活动路线图
- `--milestone` (可选): 里程碑ID
- `--task` (可选): 任务ID
- `--health` (可选): 显示健康状态检查
- `--format` (可选): 输出格式（json, text, table）

### 5. `export` - 导出路线图为YAML

将路线图导出为YAML文件。

```bash
# 导出当前活动路线图
vibecopilot roadmap export --output <输出文件路径>

# 导出指定路线图
vibecopilot roadmap export --id <路线图ID> --output <输出文件路径>

# 导出特定部分
vibecopilot roadmap export --id <路线图ID> --milestone <里程碑ID> --output <输出文件路径>

# 使用特定模板格式
vibecopilot roadmap export --id <路线图ID> --template <模板ID> --output <输出文件路径>
```

**参数说明：**

- `--id` (可选): 路线图ID，不提供则使用当前活动路线图
- `--output` (必填): 输出文件路径
- `--milestone` (可选): 只导出特定里程碑及其任务
- `--template` (可选): 使用特定模板格式

### 6. `sync` - 同步路线图数据

与外部系统同步路线图数据，包括GitHub和YAML文件。

```bash
# 从YAML同步
vibecopilot roadmap sync --source <yaml文件路径>

# 与GitHub同步
vibecopilot roadmap sync --source github:<仓库名> --theme <主题>

# 指定同步方向
vibecopilot roadmap sync --source github:<仓库名> --direction <to|from|both>

# 同步特定路线图
vibecopilot roadmap sync --id <路线图ID> --source github:<仓库名>
```

**参数说明：**

- `--source` (必填): 同步源（YAML文件路径或github:仓库名）
- `--id` (可选): 路线图ID，不提供则使用当前活动路线图
- `--direction` (可选): 同步方向（to, from, both），默认为both
- `--theme` (可选): GitHub项目主题（用于github同步）
- `--verbose` (可选): 显示详细输出

### 7. `create` - 创建路线图和元素

创建新的路线图或路线图元素（里程碑、任务等）。

```bash
# 创建新路线图
vibecopilot roadmap create <路线图名称> --description <描述>

# 创建里程碑
vibecopilot roadmap create milestone <里程碑名称> --description <描述> --roadmap <路线图ID>

# 创建任务
vibecopilot roadmap create task <任务名称> --description <描述> --milestone <里程碑ID> --roadmap <路线图ID>

# 设置额外属性
vibecopilot roadmap create task <任务名称> --priority P0 --status todo --assignee <用户>
```

**参数说明：**

- 第一个参数: 创建的对象类型（省略表示创建路线图，或milestone/task）
- 第二个参数: 名称
- `--description` (可选): 描述
- `--roadmap` (可选，创建元素时必填): 路线图ID
- `--milestone` (任务必填): 里程碑ID
- `--priority` (可选): 优先级（P0, P1, P2, P3）
- `--status` (可选): 状态（todo, in_progress, completed等）

### 8. `update` - 更新路线图和元素

更新现有路线图或路线图元素的信息。

```bash
# 更新路线图
vibecopilot roadmap update <路线图ID> --title <新标题> --description <新描述>

# 更新里程碑
vibecopilot roadmap update milestone <里程碑ID> --title <新标题> --status <新状态>

# 更新任务
vibecopilot roadmap update task <任务ID> --title <新标题> --status <新状态> --priority <新优先级>

# 更新进度
vibecopilot roadmap update milestone <里程碑ID> --progress <进度百分比>
```

**参数说明：**

- 第一个参数: 更新的对象类型（省略表示更新路线图，或milestone/task）
- 第二个参数: 对象ID
- `--title` (可选): 新标题
- `--description` (可选): 新描述
- `--status` (可选): 新状态
- `--priority` (可选): 新优先级
- `--progress` (可选): 新进度（0-100）

### 9. `delete` - 删除路线图和元素

删除路线图或路线图元素。

```bash
# 删除路线图
vibecopilot roadmap delete <路线图ID>

# 删除里程碑
vibecopilot roadmap delete milestone <里程碑ID>

# 删除任务
vibecopilot roadmap delete task <任务ID>

# 强制删除（不确认）
vibecopilot roadmap delete <路线图ID> --force
```

**参数说明：**

- 第一个参数: 删除的对象类型（省略表示删除路线图，或milestone/task）
- 第二个参数: 对象ID
- `--force` (可选): 强制删除，不请求确认
- `--cascade` (可选): 级联删除关联元素

### 10. `switch` - 切换活动路线图

切换当前活动的路线图，影响其他命令默认操作的路线图。

```bash
# 切换活动路线图
vibecopilot roadmap switch <路线图ID>

# 显示当前活动路线图
vibecopilot roadmap switch --show

# 关闭活动路线图（不设置活动路线图）
vibecopilot roadmap switch --clear
```

**参数说明：**

- 第一个参数: 路线图ID
- `--show` (可选): 只显示当前活动路线图
- `--clear` (可选): 清除当前活动路线图设置

### 11. `story` - 查看路线图故事

查看路线图中的用户故事信息。

```bash
# 列出所有故事
vibecopilot roadmap story

# 查看特定故事详情
vibecopilot roadmap story <story_id>

# 查看里程碑下的所有故事
vibecopilot roadmap story --milestone <milestone_id>

# 列出进行中的故事
vibecopilot roadmap story --status=in_progress

# 按优先级降序列出故事
vibecopilot roadmap story --sort=priority --desc

# 以特定格式输出
vibecopilot roadmap story --format=json
```

**参数说明：**

- 第一个参数(可选): 故事ID
- `--milestone` (可选): 指定里程碑ID
- `--format` (可选): 输出格式 (table/json/yaml)
- `--sort` (可选): 排序字段 (id/title/status/priority/progress)
- `--desc` (可选): 降序排序
- `--assignee` (可选): 筛选指派人
- `--labels` (可选): 筛选标签
- `--status` (可选): 筛选状态

### 12. `plan` - 互动式路线图规划

启动互动式规划流程，创建或修改路线图。

```bash
# 开始新路线图规划
vibecopilot roadmap plan

# 修改现有路线图
vibecopilot roadmap plan --id <路线图ID>

# 使用模板
vibecopilot roadmap plan --template <模板名称>

# 从YAML开始
vibecopilot roadmap plan --from <yaml文件路径>
```

**参数说明：**

- `--id` (可选): 要修改的路线图ID
- `--template` (可选): 使用特定模板开始
- `--from` (可选): 从YAML文件开始
- `--interactive` (可选): 始终使用交互式模式

## 实现规划

### 现有命令

根据当前代码库，以下命令已实现：

- `create` - 创建路线图
- `list` - 列出路线图元素（需添加--all选项）
- `sync` - 同步路线图数据
- `update` - 更新路线图元素
- `switch` - 切换活动路线图
- `story` - 查看路线图故事
- `show` - 查看路线图详情（新实现）

### 待实现命令

以下命令需要实现或优化：

1. **优化`list`命令** - 添加`--all`选项
   - 整合原`all`子命令的功能到`list --all`
   - 提供更丰富的筛选选项

2. **`validate`** - 验证YAML文件格式
   - 基于`src/roadmap/sync/yaml_validator_cli.py`的功能
   - 需要集成到命令行接口

3. **`import`** - 导入YAML文件
   - 整合验证和修复功能
   - 使用`src.parsing`的LLM功能解析格式错误的YAML

4. **`export`** - 导出路线图为YAML
   - 支持整个路线图或部分导出
   - 提供多种模板格式

5. **`delete`** - 删除路线图和元素
   - 支持级联删除
   - 包含确认机制

6. **`plan`** - 互动式规划
   - 设计交互式流程
   - 支持模板和导入现有数据

## 实现注意事项

1. 使用已有的验证工具：
   ```python
   # 使用现有的YAML验证器
   python src/roadmap/sync/yaml_validator_cli.py validate path/to/roadmap.yaml
   ```

2. 导入时处理验证和修复：
   ```python
   # 验证并修复，使用parsing模块的LLM能力
   from src.parsing import llm_parser
   # 解析有问题的YAML并尝试修复
   ```

3. 确保命令之间的一致性：
   - 参数风格保持一致
   - 错误处理方式统一
   - 提供详细的帮助信息

4. 集成`status`模块:
   - 切换路线图时通知状态系统
   - 保持路线图状态与系统状态同步

5. 命令优化建议：
   - 将原独立的roadmap命令集成到`list`命令中，使用`--all`选项标识
   - 修改代码示例：
   ```python
   @roadmap.command(name="list", help="列出路线图元素或所有路线图")
   @click.option("--all", is_flag=True, help="列出所有路线图而非当前路线图中的元素")
   @click.option("--format", type=click.Choice(["text", "json", "table"]), default="text", help="输出格式")
   @click.option("--type", type=click.Choice(["all", "milestone", "story", "task"]), default="all", help="元素类型")
   # ...其他选项...
   @pass_service
   def list_roadmaps(service, all, format, type, ...):
       if all:
           # 显示所有路线图功能
           result = service.list_roadmaps()
           # ...处理和显示结果...
       else:
           # 显示当前路线图元素
           # ...列出当前路线图的元素...
   ```

## 结论

通过实现上述命令集，VibeCopilot将提供完整的路线图管理功能，使用户能够便捷地创建、导入、管理和同步项目路线图。特别是`list --all`选项的整合将提供更直观的命令结构，保持命令的一致性同时减少了不必要的子命令。建议优先实现这一优化，然后逐步扩展其他功能。
