# Task命令重构方案

## 1. 日志控制优化

### 问题

- 非verbose模式下显示过多数据库日志
- 调试信息过于冗长
- 影响命令输出的清晰度

### 解决方案

1. 日志级别控制

```python
# 在TaskService初始化时设置日志级别
def __init__(self, verbose=False):
    self.logger = logging.getLogger(__name__)
    if not verbose:
        self.logger.setLevel(logging.WARNING)
        # 设置数据库日志级别
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
```

2. 数据库操作日志控制

```python
# 在DatabaseService中添加verbose控制
class DatabaseService:
    def __init__(self, verbose=False):
        self.verbose = verbose
        if not verbose:
            # 关闭数据库初始化日志
            self._disable_db_logs()
```

## 2. 任务名称唯一性控制

### 问题

- 当前允许创建同名任务
- 通过名称查找时可能返回多个结果
- 用户体验不佳

### 解决方案

1. 添加任务名称唯一性约束

```python
# 在Task模型中添加唯一性约束
class Task(Base):
    __table_args__ = (
        UniqueConstraint('title', name='uq_task_title'),
    )
```

2. 处理同名任务创建

```python
def create_task(self, title: str, force: bool = False):
    existing = self.find_by_title(title)
    if existing and not force:
        raise TaskExistsError(
            f"任务'{title}'已存在(ID: {existing.id})\n"
            "使用 --force 参数覆盖现有任务"
        )
```

## 3. YAML输出格式统一

### 问题

- 空值表示不一致（null/-）
- 格式化不够统一
- 缺乏清晰的层级结构

### 解决方案

1. 统一YAML序列化处理

```python
class TaskYAMLFormatter:
    @staticmethod
    def format_value(value):
        if value is None:
            return '-'  # 统一使用'-'表示空值
        return value

    def to_yaml(self, task):
        data = {
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'assignee': self.format_value(task.assignee),
            # ... 其他字段
        }
        return yaml.dump(data, sort_keys=False, allow_unicode=True)
```

2. 添加自定义YAML表示器

```python
def setup_yaml_formatter():
    def none_presenter(dumper, _):
        return dumper.represent_scalar('tag:yaml.org,2002:null', '-')
    yaml.add_representer(type(None), none_presenter)
```

## 4. 命令参数优化

### 问题

- 多标签参数使用不便
- 参数名称不够直观
- 缺少简写选项

### 解决方案

1. 支持逗号分隔的标签列表

```python
@click.option('--labels', '-l', help='逗号分隔的标签列表')
def create(labels):
    if labels:
        labels = [l.strip() for l in labels.split(',')]
```

2. 优化参数命名和别名

```python
@click.command()
@click.option('--title', '-t', required=True, help='任务标题')
@click.option('--desc', '-d', help='任务描述')
@click.option('--labels', '-l', help='标签(逗号分隔)')
@click.option('--assignee', '-a', help='负责人')
@click.option('--priority', '-p',
              type=click.Choice(['low', 'medium', 'high']),
              default='medium',
              help='优先级')
@click.option('--force', '-f', is_flag=True,
              help='强制创建(覆盖同名任务)')
def create(title, desc, labels, assignee, priority, force):
    pass
```

## 实现步骤

1. 日志控制优化
   - 修改 `TaskService` 和 `DatabaseService` 添加verbose控制
   - 更新日志配置系统
   - 测试不同模式下的日志输出

2. 任务名称唯一性
   - 更新数据库模型添加唯一约束
   - 添加任务存在性检查
   - 实现force参数处理逻辑
   - 添加数据迁移脚本

3. YAML格式化
   - 创建 `TaskYAMLFormatter` 类
   - 实现统一的空值处理
   - 更新所有输出相关代码

4. 命令参数
   - 更新命令参数定义
   - 添加参数处理逻辑
   - 更新帮助文档
   - 添加参数验证

## 测试计划

1. 日志控制测试

```bash
# 测试非verbose模式
vibecopilot task list
# 测试verbose模式
vibecopilot task list -v
```

2. 任务名称唯一性测试

```bash
# 创建任务
vibecopilot task create -t "测试任务"
# 尝试创建同名任务
vibecopilot task create -t "测试任务"
# 使用force参数
vibecopilot task create -t "测试任务" -f
```

3. YAML格式测试

```bash
# 测试各种字段组合
vibecopilot task show task_id
vibecopilot task list --format yaml
```

4. 命令参数测试

```bash
# 测试标签列表
vibecopilot task create -t "测试" -l "bug,feature,urgent"
# 测试各种参数组合
vibecopilot task create -t "测试" -d "描述" -p high -a jacob
```

## 注意事项

1. 数据库迁移
   - 添加唯一约束前需要处理现有的同名任务
   - 准备回滚方案

2. 向后兼容
   - 保持原有命令格式可用
   - 添加参数别名支持

3. 文档更新
   - 更新命令帮助文档
   - 添加新特性说明
   - 更新示例代码
