# 数据源统一方案

### 1. 总体架构调整

**核心原则：**

- 数据库作为唯一的权威数据源
- 文件系统仅用于备份/导入导出
- 不增加新的系统命令，利用现有的`db`命令

### 2. 同步策略

- `db backup`：将数据库内容导出为JSON到指定目录
- `db restore`：从JSON文件导入数据到数据库

### 3. 服务层代码调整

**workflow/service/**

- 重构所有`get_*`和`list_*`方法，直接从数据库读取
- 移除所有文件系统操作相关代码
- 保留文件导入导出功能，但移至独立模块

```python
# 修改前
def list_workflows():
    # 从文件系统读取
    workflows_dir = get_workflows_directory()
    # ...读取JSON文件

# 修改后
def list_workflows():
    # 直接从数据库读取
    with get_session_factory()() as session:
        repo = WorkflowDefinitionRepository(session)
        return [workflow.to_dict() for workflow in repo.get_all()]
```

### 4. CLI命令调整

1. **db命令增强**

```python
@db_group.command(name="backup", help="将数据库内容备份到文件系统")
@click.option("--output", "-o", help="输出目录路径")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def backup_db(output: Optional[str], verbose: bool):
    """备份数据库内容到文件系统"""
    # 实现备份逻辑

@db_group.command(name="restore", help="从文件系统恢复数据到数据库")
@click.option("--input", "-i", help="输入目录路径")
@click.option("--force", "-f", is_flag=True, help="强制覆盖已存在的数据")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def restore_db(input: Optional[str], force: bool, verbose: bool):
    """从文件系统恢复数据到数据库"""
    # 实现恢复逻辑
```

2. **保持其他命令不变**
   - flow、roadmap、rule、template命令保持不变
   - 它们底层实现改为从数据库读取

### 5. 工具实用函数实现

**数据库备份功能：**

```python
def backup_workflow_definitions(output_dir: str) -> Dict[str, Any]:
    """
    将工作流定义备份到JSON文件

    Args:
        output_dir: 输出目录

    Returns:
        备份结果统计
    """
    with get_session_factory()() as session:
        repo = WorkflowDefinitionRepository(session)
        workflows = repo.get_all()

        ensure_directory_exists(output_dir)
        count = 0

        for workflow in workflows:
            workflow_dict = workflow.to_dict()
            file_path = os.path.join(output_dir, f"{workflow.id}.json")
            write_json_file(file_path, workflow_dict)
            count += 1

    return {
        "count": count,
        "target_dir": output_dir,
        "type": "workflow_definitions"
    }
```

**数据库恢复功能：**

```python
def restore_workflow_definitions(input_dir: str, force: bool = False) -> Dict[str, Any]:
    """
    从JSON文件恢复工作流定义

    Args:
        input_dir: 输入目录
        force: 是否强制覆盖已存在的数据

    Returns:
        恢复结果统计
    """
    # 检查目录是否存在
    if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
        raise ValueError(f"输入目录不存在: {input_dir}")

    # 读取所有JSON文件
    files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    if not files:
        raise ValueError(f"目录中没有找到JSON文件: {input_dir}")

    with get_session_factory()() as session:
        repo = WorkflowDefinitionRepository(session)
        imported = 0
        updated = 0

        for file_name in files:
            file_path = os.path.join(input_dir, file_name)
            workflow_data = read_json_file(file_path)

            # 从数据检查ID
            workflow_id = workflow_data.get('id')
            if not workflow_id:
                logger.warning(f"文件缺少ID字段: {file_name}")
                continue

            # 检查是否已存在
            existing = repo.get_by_id(workflow_id)
            if existing:
                if not force:
                    logger.info(f"跳过已存在的工作流: {workflow_id}")
                    continue

                # 更新现有工作流
                for key, value in workflow_data.items():
                    if key != 'id' and hasattr(existing, key):
                        setattr(existing, key, value)
                updated += 1
            else:
                # 创建新工作流
                new_workflow = WorkflowDefinition(
                    id=workflow_id,
                    name=workflow_data.get('name', '未命名'),
                    type=workflow_data.get('type'),
                    description=workflow_data.get('description', ''),
                    stages=workflow_data.get('stages', []),
                    source_rule=workflow_data.get('source_rule')
                )
                session.add(new_workflow)
                imported += 1

        session.commit()

    return {
        "imported": imported,
        "updated": updated,
        "total": imported + updated,
        "source_dir": input_dir,
        "type": "workflow_definitions"
    }
```

### 6. 实施步骤

1. **准备阶段**
   - 创建数据库备份/恢复功能模块
   - 测试备份/恢复功能

2. **重构阶段**
   - 修改service层代码，改为从数据库读取
   - 保留文件系统导入/导出的功能
   - 更新CLI命令实现

3 **测试阶段**

- 单元测试各个组件
- 集成测试确保功能正常

4. **部署阶段**
   - 发布更新
   - 执行数据迁移脚本

### 7. 预期效果

**统一后的数据流模型：**
```
[用户命令] -> [CLI命令层] -> [服务层] -> [数据库层] <-> [数据]
                                     |
                                     v
                        [备份/恢复] <-> [文件系统]
```

这个方案不需要增加新的系统命令，同时保留了从文本读取到数据库和从数据库同步到文本的功能，符合你的要求。数据库作为唯一的权威数据源，文件系统仅用于备份和恢复操作。
