# VibeCopilot CLI用户体验长期改善方案

## 1. 命令错误处理框架

扩展我们对roadmap list命令的友好错误处理方案，构建一个通用框架：

```python
# 创建通用错误处理装饰器
def friendly_command_error(func):
    """为所有CLI命令提供友好的错误处理"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            console = Console()
            error_msg = str(e)

            # 处理参数错误情况
            if isinstance(e, (UsageError, BadParameter)) or "unexpected extra arguments" in error_msg:
                console.print("[bold red]命令格式错误[/bold red]")
                console.print(f"[red]{error_msg}[/red]")

                # 提取命令名称
                cmd_name = func.__name__.split("_")[0] if "_" in func.__name__ else func.__name__
                cmd_group = func.__globals__.get("__name__", "").split(".")[-2] if "." in func.__globals__.get("__name__", "") else ""

                console.print(f"\n[yellow]提示:[/yellow] 参数需要使用 '--' 前缀")
                console.print(f"[blue]查看帮助:[/blue] vibecopilot {cmd_group} {cmd_name} --help")

            # 处理缺少参数值的情况
            elif "requires an argument" in error_msg:
                # 从错误消息中提取选项名称
                option_match = re.search(r"Option '(--\w+)' requires an argument", error_msg)
                if option_match:
                    option_name = option_match.group(1).strip('-')  # 移除前导的--
                    console.print(f"[bold yellow]参数不完整[/bold yellow]: {option_name}")

                    # 获取命令和选项的上下文信息
                    cmd_name = func.__name__.split("_")[0] if "_" in func.__name__ else func.__name__
                    cmd_group = func.__globals__.get("__name__", "").split(".")[-2] if "." in func.__globals__.get("__name__", "") else ""

                    # 根据选项名称提供针对性建议
                    suggestions = get_option_suggestions(cmd_group, cmd_name, option_name)

                    if suggestions:
                        console.print("\n[green]可选的参数值:[/green]")
                        for value, desc in suggestions.items():
                            console.print(f"  --{option_name} {value}  # {desc}")

                        # 提供示例命令
                        first_value = next(iter(suggestions.keys())) if suggestions else "value"
                        console.print("\n[blue]示例:[/blue]")
                        console.print(f"  vibecopilot {cmd_group} {cmd_name} --{option_name} {first_value}")
                    else:
                        console.print(f"\n请为 --{option_name} 提供一个有效值")
                else:
                    console.print(f"[yellow]提示:[/yellow] 命令缺少必要参数")
            else:
                # 其他错误
                console.print(f"[bold red]执行错误:[/bold red] {error_msg}")

            return 1
    return wrapper

# 提供选项建议的辅助函数
def get_option_suggestions(cmd_group, cmd_name, option_name):
    """根据命令组、命令名和选项名提供建议值"""
    # 为常见选项预定义可能的值
    option_suggestions = {
        "roadmap": {
            "list": {
                "status": {
                    "todo": "待办任务",
                    "in_progress": "进行中",
                    "completed": "已完成",
                    "blocked": "被阻塞",
                    "review": "审核中",
                    "canceled": "已取消"
                },
                "type": {
                    "all": "所有类型",
                    "milestone": "里程碑",
                    "story": "用户故事",
                    "task": "任务",
                    "epic": "史诗"
                },
                "format": {
                    "text": "文本格式",
                    "json": "JSON格式",
                    "table": "表格格式"
                },
                "assignee": {"[用户名]": "指定负责人"}
            },
            "update": {
                "status": {
                    "active": "活动中",
                    "completed": "已完成",
                    "planned": "已计划",
                    "canceled": "已取消"
                },
                "priority": {
                    "p0": "最高优先级",
                    "p1": "高优先级",
                    "p2": "中等优先级",
                    "p3": "低优先级"
                }
            }
        },
        "task": {
            "create": {
                "priority": {
                    "p0": "最高优先级",
                    "p1": "高优先级",
                    "p2": "中等优先级",
                    "p3": "低优先级"
                },
                "status": {
                    "todo": "待办",
                    "in_progress": "进行中",
                    "review": "审核中"
                }
            }
        }
    }

    # 尝试获取特定命令和选项的建议
    if cmd_group in option_suggestions and cmd_name in option_suggestions[cmd_group]:
        cmd_options = option_suggestions[cmd_group][cmd_name]
        if option_name in cmd_options:
            return cmd_options[option_name]

    # 返回空字典表示没有具体建议
    return {}
```

## 2. 统一命令结构与接口

### 阶段一：命令标准化

1. 对所有主要命令组应用统一结构：
   - 标准化帮助信息格式
   - 统一错误处理
   - 统一输出风格

2. 为每个命令组实现四种标准交互模式：
   ```
   - 简洁模式（默认）
   - 详细模式（--verbose）
   - JSON输出（--format=json）
   - 交互式模式（--interactive）
   ```

3. 完善参数处理逻辑：
   - 支持缺少参数值的智能提示
   - 提供上下文相关的参数建议
   - 增强帮助信息，显示每个选项的可能值

### 阶段二：命令智能化

1. 实现命令联想与自动完成
   ```
   vibecopilot road<tab> → vibecopilot roadmap
   vibecopilot roadmap l<tab> → vibecopilot roadmap list
   ```

2. 智能参数推断与修正
   ```python
   # 根据参数关键字自动推断旗标类型
   def smart_arg_parser(args):
      # 例如：type转为--type，all转为--all=true
      # 自动补全：--status后面没有值时提供默认值或可选列表
      return processed_args
   ```

3. 上下文感知参数值建议
   ```python
   # 根据当前命令上下文提供建议
   async def get_context_suggestions(cmd, option, current_args):
      # 例如：如果指定了roadmap，则为milestone提供该roadmap下的可用里程碑
      if option == "milestone" and "roadmap_id" in current_args:
          return await db.get_milestones(current_args["roadmap_id"])
      return get_static_suggestions(option)
   ```

## 3. 路线图命令优化计划

### 优先任务

1. **完善现有命令**：
   - 优化`list`命令的输出格式
   - 完善`validate`、`import`和`export`命令实现
   - 为所有选项参数添加智能提示和默认值

2. **实现交互式命令**：
   ```
   vibecopilot roadmap plan --interactive
   ```
   引导用户通过问答创建或修改路线图

3. **命令迁移与增强**：
   ```python
   # 统一将ListCommand类改为Click命令，并添加参数提示功能
   @roadmap.command(name="list-elements")
   @click.option("--status", help="按状态筛选（todo, in_progress, completed, blocked, review, canceled）")
   @click.option("--type", help="元素类型（milestone, story, task, epic, all）")
   def list_elements(...):
      # 新实现
   ```

### 长期优化

1. **智能命令别名系统**
   ```
   vibecopilot alias add "rm-ls" "roadmap list --all"
   vibecopilot rm-ls  # 执行 roadmap list --all
   ```

2. **多级模糊匹配与智能纠错**
   - 允许部分命令名匹配：`vibecopilot ro li` → `vibecopilot roadmap list`
   - 允许命令选项缩写：`vibecopilot roadmap list -a` → `--all`
   - 智能纠正常见错误：`vibecopilot roadmap lst` → `list`
   - 自动修复错误参数：`vibecopilot roadmap list --stats active` → `--status active`

3. **交互式参数补全**
   - 当缺少参数值时进入交互模式
   ```
   $ vibecopilot roadmap list --status
   参数"status"缺少值，请选择:
   1) todo
   2) in_progress
   3) completed
   4) blocked
   输入选择 (1-4): _
   ```

## 4. 技术实现路线

### 阶段一：基础优化（2-4周）

1. 创建通用错误处理装饰器
2. 统一所有命令帮助信息
3. 标准化命令返回值处理
4. 为roadmap组完成所有命令实现
5. 构建选项值提示数据库

```python
# 示例：通用命令基类
class BaseClickCommand:
    """所有Click命令的基类"""
    @staticmethod
    def format_output(data, format="text", verbose=False):
        # 通用输出格式处理
        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "table":
            # 表格化处理
            pass
        # 其他格式...

    @staticmethod
    def get_option_suggestions(cmd_group, cmd_name, option_name):
        """获取选项的可能值建议"""
        return get_option_suggestions(cmd_group, cmd_name, option_name)

    @staticmethod
    def handle_missing_argument(ctx, option_name):
        """处理缺少参数值的情况"""
        suggestions = get_option_suggestions(ctx.command.name, option_name)
        if not suggestions:
            return None

        # 显示建议并请求用户输入
        console = Console()
        console.print(f"参数"{option_name}"缺少值，请选择:")
        for idx, (value, desc) in enumerate(suggestions.items(), 1):
            console.print(f"{idx}) {value} - {desc}")

        # 读取用户选择
        selection = console.input("输入选择: ")
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(suggestions):
                return list(suggestions.keys())[idx]
        except ValueError:
            pass

        return None
```

### 阶段二：命令增强（4-8周）

1. 实现命令自动完成
2. 添加智能参数解析
3. 开发交互式命令模式
4. 构建命令别名系统
5. 增强参数值提示，支持上下文感知

```python
# 示例：命令自动完成
def generate_completions():
    """生成shell自动完成脚本"""
    commands = collect_all_commands()
    # 生成适用于bash/zsh的自动完成脚本

# 示例：参数上下文感知
class ContextAwareOption(click.Option):
    """上下文感知的命令选项"""
    def __init__(self, *args, **kwargs):
        self.context_provider = kwargs.pop('context_provider', None)
        super().__init__(*args, **kwargs)

    def get_suggestions(self, ctx):
        """根据当前上下文获取建议值"""
        if self.context_provider:
            return self.context_provider(ctx)
        return {}

    def handle_parse_result(self, ctx, opts, args):
        # 如果选项存在但没有值，提供交互式选择
        if self.name in opts and opts[self.name] is None:
            suggestions = self.get_suggestions(ctx)
            if suggestions:
                # 显示并获取用户选择
                # ... 交互式选择实现 ...
                pass
        return super().handle_parse_result(ctx, opts, args)
```

### 阶段三：高级功能（8-12周）

1. 自适应命令提示
2. 多命令组合（管道）
3. 命令历史与恢复
4. 多语言支持
5. 动态参数学习

```python
# 示例：命令组合
def pipe_commands(cmd1, cmd2):
    """执行命令管道：cmd1 | cmd2"""
    result1 = execute_command(cmd1)
    return execute_command(cmd2, input=result1)

# 示例：参数使用学习
class SmartParameterTracker:
    """学习参数使用模式提供更智能的建议"""
    def __init__(self, history_file=".vibecopilot_param_history"):
        self.history_file = history_file
        self.param_history = self._load_history()

    def _load_history(self):
        """加载历史记录"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def track_param_usage(self, cmd_group, cmd_name, param_name, value):
        """记录参数使用"""
        key = f"{cmd_group}.{cmd_name}.{param_name}"
        if key not in self.param_history:
            self.param_history[key] = {}

        if value not in self.param_history[key]:
            self.param_history[key][value] = 0

        self.param_history[key][value] += 1
        self._save_history()

    def get_suggestions(self, cmd_group, cmd_name, param_name, max_suggestions=5):
        """获取基于历史的建议"""
        key = f"{cmd_group}.{cmd_name}.{param_name}"
        if key not in self.param_history:
            return {}

        # 按使用频率排序
        sorted_values = sorted(
            self.param_history[key].items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 返回前N个最常用值
        return {v: f"使用了{c}次" for v, c in sorted_values[:max_suggestions]}

    def _save_history(self):
        """保存历史记录"""
        with open(self.history_file, 'w') as f:
            json.dump(self.param_history, f)
```

## 5. 衡量标准

1. **易用性指标**：
   - 新用户首次使用成功率
   - 常见错误减少百分比
   - 命令完成平均时间
   - 参数提示有效率（用户采纳建议的比例）

2. **技术指标**：
   - 代码重复率降低
   - 测试覆盖率提升
   - 文档完整度
   - 错误处理覆盖率

3. **用户满意度指标**：
   - 参数补全使用频率
   - 命令中断率下降
   - 重复尝试次数减少

## 6. 总结

本方案围绕着提升用户体验设计，通过三个阶段逐步实现：

1. 基础优化：统一错误处理和输出，增加参数值提示
2. 命令增强：添加智能特性和上下文感知能力
3. 高级功能：实现更复杂的交互模式和自适应学习

特别针对"参数不完整"的情况（如 `vibecopilot roadmap list --status` 缺少值），我们提供了三层解决方案：

1. 立即效果：友好错误提示，显示可用选项
2. 中期改进：交互式参数补全，让用户选择值
3. 长期优化：上下文感知和历史学习，提供最可能的建议

同时，我们将保持向后兼容性，确保已有的脚本和工作流不会因为改进而中断。这个长期计划会使VibeCopilot CLI更加用户友好，减少使用摩擦，并提高开发效率。
