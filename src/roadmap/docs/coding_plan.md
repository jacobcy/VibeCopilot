
# 路线图命令实现计划

根据`dev_plan.md`的规划，我将分析现有代码并提供实现路线图命令的具体步骤。本计划注重复用现有功能，进行调试和优化，而非重写代码。

## 现有功能分析

已实现的命令：

- `create` - 创建路线图 (create_command.py)
- `list` - 列出路线图 (list_command.py)
- `sync` - 同步路线图数据 (sync_command.py)
- `update` - 更新路线图元素 (update_command.py)
- `switch` - 切换活动路线图 (switch_command.py)
- `story` - 查看路线图故事 (story_command.py)

## 需实现的命令与实现步骤

### 1. `validate` - 验证路线图YAML

**实现步骤**：

1. 创建`validate_command.py`文件，继承`base_command.py`的基础命令类
2. 复用`src/roadmap/sync/yaml_validator_cli.py`中的验证功能
3. 构建命令参数结构，支持`--source, --fix, --output, --template, --verbose`

**代码框架**：
```python
# src/cli/commands/roadmap/validate_command.py
import os
import click
from rich.console import Console
from src.cli.commands.roadmap.base_command import RoadmapBaseCommand
from src.roadmap.validator.yaml_validator  import RoadmapYamlValidator

console = Console()

class ValidateCommand(RoadmapBaseCommand):
    """验证YAML文件命令"""

    @click.argument("source", required=True, type=click.Path(exists=True))
    @click.option("--fix", is_flag=True, help="自动修复格式问题")
    @click.option("--output", type=click.Path(), help="修复后输出的文件路径")
    @click.option("--template", type=click.Path(exists=True), help="使用自定义模板验证")
    @click.option("--verbose", is_flag=True, help="显示详细信息")
    def execute(self, source, fix, output, template, verbose):
        """验证路线图YAML文件格式

        SOURCE: YAML文件路径
        """
        try:
            validator = RoadmapYamlValidator(template_path=template)
            is_valid, messages, fixed_data = validator.validate(source)

            # 显示验证结果
            if is_valid and not messages:
                console.print("[green]验证通过，文件格式正确[/green]")
                return 0

            # 显示消息
            for msg_type, msg in messages:
                if msg_type == "error":
                    console.print(f"[red]错误: {msg}[/red]")
                elif msg_type == "warning":
                    console.print(f"[yellow]警告: {msg}[/yellow]")
                else:
                    console.print(msg)

            # 处理修复
            if not is_valid and fix and fixed_data:
                output_path = output or f"{os.path.splitext(source)[0]}_fixed.yaml"
                validator.generate_fixed_yaml(fixed_data, output_path)
                console.print(f"[green]已修复并保存到: {output_path}[/green]")

            return 0 if is_valid else 1

        except Exception as e:
            console.print(f"[red]验证过程中出错: {str(e)}[/red]")
            return 1
```

### 2. `import` - 导入YAML文件

**实现步骤**：

1. 创建`import_command.py`，集成验证和导入功能
2. 复用`validate_command.py`的验证能力
3. 复用`sync_command.py`的YAML导入逻辑
4. 添加参数`--fix, --roadmap-id, --activate`

**代码框架**：
```python
# src/cli/commands/roadmap/import_command.py
import click
from rich.console import Console
from src.cli.commands.roadmap.base_command import RoadmapBaseCommand
from src.roadmap.validator.yaml_validator  import RoadmapYamlValidator
from src.roadmap import RoadmapService

console = Console()

class ImportCommand(RoadmapBaseCommand):
    """导入YAML文件命令"""

    @click.argument("source", required=True, type=click.Path(exists=True))
    @click.option("--roadmap-id", help="现有路线图ID，不提供则创建新路线图")
    @click.option("--fix", is_flag=True, help="自动修复格式问题")
    @click.option("--activate", is_flag=True, help="导入后设为当前活动路线图")
    @click.option("--verbose", is_flag=True, help="显示详细信息")
    def execute(self, source, roadmap_id, fix, activate, verbose):
        """从YAML文件导入路线图

        SOURCE: YAML文件路径
        """
        try:
            # 1. 验证YAML文件
            validator = RoadmapYamlValidator()
            is_valid, messages, fixed_data = validator.validate(source)

            if not is_valid:
                # 显示错误
                for msg_type, msg in messages:
                    if msg_type == "error":
                        console.print(f"[red]错误: {msg}[/red]")

                if not fix:
                    console.print("[yellow]可以使用 --fix 参数自动修复问题[/yellow]")
                    return 1

                if not fixed_data:
                    console.print("[red]无法自动修复[/red]")
                    return 1

                source_data = fixed_data
                console.print("[yellow]已自动修复YAML格式问题[/yellow]")

            # 2. 导入路线图
            service = RoadmapService()

            # 使用roadmap_id参数
            if roadmap_id:
                result = service.sync.yaml_sync.import_from_yaml(source, roadmap_id)
            else:
                result = service.sync.yaml_sync.import_from_yaml(source)

            # 处理结果
            if result.get("success"):
                roadmap_id = result.get("roadmap_id")
                console.print(f"[green]导入成功: 路线图ID {roadmap_id}[/green]")

                # 激活路线图
                if activate and roadmap_id:
                    service.set_active_roadmap(roadmap_id)
                    console.print(f"[green]已设置 {roadmap_id} 为活动路线图[/green]")

                return 0
            else:
                console.print(f"[red]导入失败: {result.get('error', '未知错误')}[/red]")
                return 1

        except Exception as e:
            console.print(f"[red]导入过程中出错: {str(e)}[/red]")
            return 1
```

### 3. `check` - 查看路线图详情

**实现步骤**：

1. 创建`check_command.py`，复用`list_command.py`和`story_command.py`的展示逻辑
2. 实现针对单个路线图、里程碑或任务的详细查看

**代码框架**：
```python
# src/cli/commands/roadmap/check_command.py
import click
from rich.console import Console
from rich.table import Table
from src.cli.commands.roadmap.base_command import RoadmapBaseCommand
from src.roadmap import RoadmapService

console = Console()

class CheckCommand(RoadmapBaseCommand):
    """查看路线图详情命令"""

    @click.option("--id", help="路线图ID，不提供则使用当前活动路线图")
    @click.option("--milestone", help="里程碑ID")
    @click.option("--task", help="任务ID")
    @click.option("--health", is_flag=True, help="显示健康状态检查")
    @click.option("--format", type=click.Choice(["json", "text", "table"]), default="table", help="输出格式")
    def execute(self, id, milestone, task, health, format):
        """查看路线图详情"""
        try:
            service = RoadmapService()
            roadmap_id = id or service.active_roadmap_id

            if not roadmap_id:
                console.print("[yellow]未指定路线图ID且无活动路线图，请使用 --id 参数指定路线图[/yellow]")
                return 1

            # 如果指定了任务ID
            if task:
                return self._show_task(service, roadmap_id, task, format)

            # 如果指定了里程碑ID
            if milestone:
                return self._show_milestone(service, roadmap_id, milestone, format)

            # 如果指定了健康检查
            if health:
                return self._show_health(service, roadmap_id, format)

            # 否则显示整个路线图详情
            return self._show_roadmap(service, roadmap_id, format)

        except Exception as e:
            console.print(f"[red]查看路线图详情时出错: {str(e)}[/red]")
            return 1

    def _show_roadmap(self, service, roadmap_id, format):
        """显示路线图详情"""
        # 实现路线图展示逻辑，复用list_command代码

    def _show_milestone(self, service, roadmap_id, milestone_id, format):
        """显示里程碑详情"""
        # 实现里程碑展示逻辑

    def _show_task(self, service, roadmap_id, task_id, format):
        """显示任务详情"""
        # 实现任务展示逻辑

    def _show_health(self, service, roadmap_id, format):
        """显示健康状态"""
        # 实现健康状态检查展示逻辑
```

### 4. `export` - 导出路线图为YAML

**实现步骤**：

1. 创建`export_command.py`，复用`sync_command.py`中YAML处理逻辑
2. 实现导出整个路线图或部分导出的功能

**代码框架**：
```python
# src/cli/commands/roadmap/export_command.py
import os
import click
from rich.console import Console
from src.cli.commands.roadmap.base_command import RoadmapBaseCommand
from src.roadmap import RoadmapService

console = Console()

class ExportCommand(RoadmapBaseCommand):
    """导出路线图为YAML命令"""

    @click.option("--id", help="路线图ID，不提供则使用当前活动路线图")
    @click.option("--output", required=True, type=click.Path(), help="输出文件路径")
    @click.option("--milestone", help="只导出特定里程碑及其任务")
    @click.option("--template", help="使用特定模板格式")
    def execute(self, id, output, milestone, template):
        """导出路线图为YAML文件

        OUTPUT: 输出文件路径
        """
        try:
            service = RoadmapService()
            roadmap_id = id or service.active_roadmap_id

            if not roadmap_id:
                console.print("[yellow]未指定路线图ID且无活动路线图，请使用 --id 参数指定路线图[/yellow]")
                return 1

            # 确保输出目录存在
            output_dir = os.path.dirname(output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 导出路线图
            result = service.export_to_yaml(roadmap_id, output, milestone_id=milestone, template=template)

            if result.get("success"):
                console.print(f"[green]路线图已成功导出到: {output}[/green]")
                return 0
            else:
                console.print(f"[red]导出失败: {result.get('error', '未知错误')}[/red]")
                return 1

        except Exception as e:
            console.print(f"[red]导出过程中出错: {str(e)}[/red]")
            return 1
```

### 5. `delete` - 删除路线图和元素

**实现步骤**：

1. 创建`delete_command.py`
2. 实现对路线图、里程碑和任务的删除功能
3. 添加确认机制和级联删除功能

**代码框架**：
```python
# src/cli/commands/roadmap/delete_command.py
import click
from rich.console import Console
from src.cli.commands.roadmap.base_command import RoadmapBaseCommand
from src.roadmap import RoadmapService

console = Console()

class DeleteCommand(RoadmapBaseCommand):
    """删除路线图和元素命令"""

    @click.argument("type", required=False, type=click.Choice(["roadmap", "milestone", "task"]))
    @click.argument("id", required=True)
    @click.option("--force", is_flag=True, help="强制删除，不请求确认")
    @click.option("--cascade", is_flag=True, help="级联删除关联元素")
    def execute(self, type, id, force, cascade):
        """删除路线图或元素

        TYPE: 删除的对象类型 (roadmap, milestone, task)
        ID: 对象ID
        """
        try:
            service = RoadmapService()

            # 如果未指定type，默认为roadmap
            if not type:
                type = "roadmap"

            # 获取对象信息
            name = self._get_object_name(service, type, id)

            # 确认删除
            if not force:
                confirm = click.confirm(f"确定要删除{self._get_type_name(type)} '{name}' ({id})吗?")
                if not confirm:
                    console.print("[yellow]操作已取消[/yellow]")
                    return 0

            # 执行删除
            if type == "roadmap":
                result = service.delete_roadmap(id, cascade=cascade)
            elif type == "milestone":
                result = service.delete_milestone(id, cascade=cascade)
            elif type == "task":
                result = service.delete_task(id)

            # 处理结果
            if result.get("success"):
                console.print(f"[green]{self._get_type_name(type)} '{name}' ({id}) 已成功删除[/green]")
                return 0
            else:
                console.print(f"[red]删除失败: {result.get('error', '未知错误')}[/red]")
                return 1

        except Exception as e:
            console.print(f"[red]删除过程中出错: {str(e)}[/red]")
            return 1

    def _get_type_name(self, type):
        """获取类型名称"""
        mapping = {
            "roadmap": "路线图",
            "milestone": "里程碑",
            "task": "任务"
        }
        return mapping.get(type, type)

    def _get_object_name(self, service, type, id):
        """获取对象名称"""
        try:
            if type == "roadmap":
                obj = service.get_roadmap(id)
                return obj.get("title", "未命名路线图")
            elif type == "milestone":
                obj = service.get_milestone(id)
                return obj.get("title", "未命名里程碑")
            elif type == "task":
                obj = service.get_task(id)
                return obj.get("title", "未命名任务")
            return "未知对象"
        except:
            return "未命名对象"
```

### 6. `plan` - 互动式路线图规划

**实现步骤**：

1. 创建`plan_command.py`
2. 实现交互式流程，引导用户创建或修改路线图
3. 支持从模板开始和从YAML文件导入

**代码框架**：
```python
# src/cli/commands/roadmap/plan_command.py
import os
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from src.cli.commands.roadmap.base_command import RoadmapBaseCommand
from src.roadmap import RoadmapService

console = Console()

class PlanCommand(RoadmapBaseCommand):
    """互动式路线图规划命令"""

    @click.option("--id", help="要修改的路线图ID")
    @click.option("--template", help="使用特定模板开始")
    @click.option("--from", "from_file", type=click.Path(exists=True), help="从YAML文件开始")
    @click.option("--interactive", is_flag=True, help="始终使用交互式模式")
    def execute(self, id, template, from_file, interactive):
        """互动式路线图规划"""
        try:
            service = RoadmapService()

            # 1. 确定工作模式和起始点
            roadmap = None
            if id:
                roadmap = service.get_roadmap(id)
                if not roadmap:
                    console.print(f"[red]未找到路线图: {id}[/red]")
                    return 1
                console.print(f"[green]正在修改路线图: {roadmap.get('title', id)}[/green]")

            # 2. 如果提供了YAML文件，导入它
            if from_file:
                if id:
                    # 导入到现有路线图
                    result = service.sync.yaml_sync.import_from_yaml(from_file, id)
                else:
                    # 创建新路线图
                    result = service.sync.yaml_sync.import_from_yaml(from_file)

                if result.get("success"):
                    id = result.get("roadmap_id")
                    roadmap = service.get_roadmap(id)
                    console.print(f"[green]已从 {from_file} 导入路线图[/green]")
                else:
                    console.print(f"[red]导入失败: {result.get('error', '未知错误')}[/red]")
                    return 1

            # 3. 开始交互式规划流程
            if not roadmap:
                # 创建新路线图
                title = Prompt.ask("请输入路线图标题")
                description = Prompt.ask("请输入路线图描述", default="")

                result = service.create_roadmap(title=title, description=description)
                if result.get("success"):
                    id = result.get("roadmap_id")
                    roadmap = service.get_roadmap(id)
                    console.print(f"[green]已创建路线图: {title} ({id})[/green]")
                else:
                    console.print(f"[red]创建路线图失败: {result.get('error', '未知错误')}[/red]")
                    return 1

            # 4. 引导用户添加/修改里程碑和任务
            # 这里实现交互式的里程碑和任务管理
            # ...

            # 5. 完成规划
            console.print("[green]路线图规划完成[/green]")

            # 询问是否设为活动路线图
            if Confirm.ask("是否将此路线图设为活动路线图?", default=True):
                service.set_active_roadmap(id)
                console.print(f"[green]已设置 {id} 为活动路线图[/green]")

            return 0

        except Exception as e:
            console.print(f"[red]规划过程中出错: {str(e)}[/red]")
            return 1
```

## 整合到命令系统

修改`src/cli/commands/roadmap/__init__.py`和`src/cli/commands/roadmap/roadmap_click.py`，注册新命令：

```python
# src/cli/commands/roadmap/__init__.py
from .validate_command import ValidateCommand
from .import_command import ImportCommand
from .check_command import CheckCommand
from .export_command import ExportCommand
from .delete_command import DeleteCommand
from .plan_command import PlanCommand

# 添加新命令到__all__
__all__ = [
    # 现有命令...
    "ValidateCommand",
    "ImportCommand",
    "CheckCommand",
    "ExportCommand",
    "DeleteCommand",
    "PlanCommand"
]
```

```python
# src/cli/commands/roadmap/roadmap_click.py
# 添加新命令
@roadmap.command("validate")
@click.pass_context
def validate_command(ctx, **kwargs):
    """验证路线图YAML文件"""
    return ValidateCommand().execute(**kwargs)

@roadmap.command("import")
@click.pass_context
def import_command(ctx, **kwargs):
    """导入路线图YAML文件"""
    return ImportCommand().execute(**kwargs)

# 添加其他命令...
```

## 测试计划

对每个新命令进行单独测试：

1. **validate命令测试**:
   ```bash
   python -m src.cli.main roadmap validate .ai/roadmap/cddrg_engine_roadmap.yaml
   python -m src.cli.main roadmap validate .ai/roadmap/cddrg_engine_roadmap.yaml --fix
   ```

2. **import命令测试**:
   ```bash
   python -m src.cli.main roadmap import --source .ai/roadmap/cddrg_engine_roadmap.yaml --activate
   ```

3. **check命令测试**:
   ```bash
   python -m src.cli.main roadmap check --id roadmap-cddrg
   python -m src.cli.main roadmap check --id roadmap-cddrg --milestone M1
   ```

4. **export命令测试**:
   ```bash
   python -m src.cli.main roadmap export --id roadmap-cddrg --output ./exported_roadmap.yaml
   ```

## 总结

通过以上步骤，我们可以复用现有代码基础，实现`dev_plan.md`中规划的所有路线图命令。这些实现方案注重：

1. 复用现有功能，避免重写代码
2. 遵循现有命令的设计模式和接口风格
3. 提供完善的错误处理和用户反馈
4. 优化命令参数和选项，增强用户体验

重点在于调试和优化，确保所有命令正常工作并且与现有系统无缝集成。
