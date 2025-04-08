# 规则命令参数说明

本文档详细说明 `vibecopilot rule` 命令及其子命令的参数用法。

## 基本用法

```bash
vibecopilot rule <子命令> [参数]
```

全局选项：

- `--help`: 显示帮助信息

## 子命令及参数

### 1. list - 列出规则

列出当前可用的所有规则。

```bash
vibecopilot rule list [选项]
```

| 参数     | 说明         | 必需 | 默认值 | 示例                       |
|----------|--------------|------|--------|----------------------------|
| `--type` | 按规则类型筛选 | 否   | -      | `--type=cmd`              |

示例：

```bash
# 列出所有规则
vibecopilot rule list

# 列出所有命令规则
vibecopilot rule list --type=cmd
```

### 2. show - 显示规则详情

显示特定规则的详细信息。

```bash
vibecopilot rule show <rule_id>
```

| 参数      | 说明   | 必需 | 默认值 | 示例             |
|-----------|--------|------|--------|------------------|
| `rule_id` | 规则ID | 是   | -      | `git-commit`     |

示例：

```bash
# 显示git-commit规则的详情
vibecopilot rule show git-commit
```

### 3. create - 创建新规则

基于指定模板创建新的规则。

```bash
vibecopilot rule create <template_type> <name> [选项]
```

| 参数             | 说明                     | 必需 | 默认值       | 示例                                |
|------------------|--------------------------|------|--------------|-------------------------------------|
| `template_type`  | 模板类型                 | 是   | -            | `cmd`                               |
| `name`           | 规则名称                 | 是   | -            | `git-commit`                        |
| `--template-dir` | 模板目录                 | 否   | 默认模板目录 | `--template-dir=/path/to/templates` |
| `--output-dir`   | 输出目录                 | 否   | `rules`      | `--output-dir=/path/to/output`      |
| `--vars`         | 变量值（JSON格式）       | 否   | -            | `--vars='{"key":"value"}'`          |
| `--interactive`  | 启用交互模式（待实现）   | 否   | `false`      | `--interactive`                     |

示例：

```bash
# 基本用法
vibecopilot rule create cmd git-commit

# 使用自定义变量
vibecopilot rule create cmd git-commit --vars='{"description":"Git提交规范","priority":"high"}'

# 使用交互模式（待实现）
vibecopilot rule create cmd git-commit --interactive
```

### 4. edit - 编辑规则（待实现）

编辑现有的规则。

```bash
vibecopilot rule edit <rule_id>
```

| 参数      | 说明   | 必需 | 默认值 | 示例           |
|-----------|--------|------|--------|----------------|
| `rule_id` | 规则ID | 是   | -      | `git-commit`   |

> 注意：此功能尚未实现。

### 5. delete - 删除规则

删除指定的规则。

```bash
vibecopilot rule delete <rule_id>
```

| 参数      | 说明   | 必需 | 默认值 | 示例           |
|-----------|--------|------|--------|----------------|
| `rule_id` | 规则ID | 是   | -      | `git-commit`   |

示例：

```bash
# 删除git-commit规则
vibecopilot rule delete git-commit
```

### 6. validate - 验证规则

验证规则的有效性。

```bash
vibecopilot rule validate [<rule_id> | --all]
```

| 参数      | 说明         | 必需 | 默认值 | 示例          |
|-----------|--------------|------|--------|---------------|
| `rule_id` | 规则ID       | 否   | -      | `git-commit`  |
| `--all`   | 验证所有规则 | 否   | `false`| `--all`       |

> 注意：验证逻辑尚未完全实现。

示例：

```bash
# 验证单个规则
vibecopilot rule validate git-commit

# 验证所有规则
vibecopilot rule validate --all
```

### 7. export - 导出规则（待实现）

将规则导出到指定文件。

```bash
vibecopilot rule export <rule_id> [output_path]
```

| 参数          | 说明     | 必需 | 默认值                | 示例                    |
|---------------|----------|------|------------------------|-----------------------|
| `rule_id`     | 规则ID   | 是   | -                      | `git-commit`           |
| `output_path` | 输出路径 | 否   | `<rule_id>_export.md`  | `/path/to/output.md`   |

> 注意：此功能尚未实现。

### 8. import - 导入规则（待实现）

从文件导入规则。

```bash
vibecopilot rule import <rule_file>
```

| 参数        | 说明       | 必需 | 默认值 | 示例                 |
|-------------|------------|------|--------|----------------------|
| `rule_file` | 规则文件路径 | 是   | -      | `/path/to/rule.md`   |

> 注意：此功能尚未实现。

## 常见问题

1. **参数冲突**
   - `validate` 命令中 `rule_id` 和 `--all` 不能同时使用

2. **JSON变量格式**
   - `--vars` 参数必须是有效的JSON格式，使用单引号包围，双引号表示JSON字符串

3. **路径注意事项**
   - 路径可以是相对路径或绝对路径
   - 相对路径基于当前工作目录计算
