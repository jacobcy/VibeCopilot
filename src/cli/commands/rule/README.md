# 规则命令模块

此模块实现了VibeCopilot的规则管理命令，包括创建、查看、修改、删除规则等操作。

## 文件结构

- `__init__.py`: 模块初始化文件，导出RuleCommand类
- `rule_command.py`: 规则命令类的实现，包含命令参数解析和执行逻辑
- `rule_command_handlers.py`: 命令处理函数，实现各种规则操作的具体逻辑
- `rule_command_utils.py`: 辅助工具函数，提供通用功能支持

## 使用方法

```bash
# 列出所有规则
vibecopilot rule list [--type TYPE]

# 显示规则详情
vibecopilot rule show <rule_id>

# 创建新规则
vibecopilot rule create <template_type> <name> [--template-dir DIR] [--output-dir DIR] [--vars JSON] [--interactive]

# 编辑规则
vibecopilot rule edit <rule_id>

# 删除规则
vibecopilot rule delete <rule_id>

# 验证规则
vibecopilot rule validate <rule_id> [--all]

# 导出规则
vibecopilot rule export <rule_id> [output_path]

# 导入规则
vibecopilot rule import <rule_file>
```

## 依赖项

- `src.cli.base_command`: 基本命令类
- `src.cli.command`: 命令接口
- `src.templates`: 模板管理服务
- `src.models.db`: 数据库模型
