# 增强型任务管理系统简化实现方案

## 1. 概述

本方案基于"增强型任务管理系统PRD"文档，提供一个高度简化的实现方案，专注于利用已有功能和命令进行整合，遵循以下原则：

1. 最小化代码改动，充分利用现有功能
2. 自动化任务管理工作流
3. 自然整合memory系统
4. 简单直观的用户体验

## 2. 核心整合思路

1. **重用现有命令**：不创建新命令，仅扩展现有命令功能
2. **专注核心路径**：只处理主要使用场景，避免边缘情况
3. **利用已有组件**：充分利用已有的memory系统和文件管理功能
4. **简单钩子机制**：在关键点添加简单钩子，自动触发辅助功能

## 3. 目录结构

保持简单的固定目录结构：

```
.ai/
  tasks/
    <task_id>/
      task.log        # 主日志文件（固定路径）
      metadata.json   # 任务元数据（包含关联的memory_item引用）
```

## 4. 简化实现方案

### 4.1 任务创建增强

```python
# 在现有task_create函数中添加简单钩子
def create_task_hook(task_id, task_data):
    """任务创建后自动调用的钩子函数"""
    # 创建固定路径目录
    task_dir = os.path.join(".ai", "tasks", task_id)
    os.makedirs(task_dir, exist_ok=True)

    # 创建日志文件
    with open(os.path.join(task_dir, "task.log"), "w") as f:
        f.write(f"# 任务日志: {task_data['title']} (ID: {task_id})\n\n")
        f.write(f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 任务创建\n")
        f.write(f"- 标题: {task_data['title']}\n")
        if task_data.get("description"):
            f.write(f"- 描述: {task_data['description']}\n")

    # 创建metadata.json
    metadata = {
        "id": task_id,
        "title": task_data["title"],
        "created_at": datetime.now().isoformat(),
        "memory_items": []  # 存储关联的memory_item ID
    }

    with open(os.path.join(task_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
```

### 4.2 任务更新与日志记录

简单地在现有更新函数中添加日志记录：

```python
def task_update_hook(task_id, updated_fields):
    """任务更新后调用的钩子函数"""
    log_path = os.path.join(".ai", "tasks", task_id, "task.log")

    # 确保日志文件存在
    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # 追加日志条目
    with open(log_path, "a") as f:
        f.write(f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 任务更新\n")
        for key, value in updated_fields.items():
            f.write(f"- {key}: {value}\n")
        f.write("\n")
```

### 4.3 参考资料与Memory集成

使用现有的memory系统功能，避免复杂的新实现：

```python
def add_reference_to_task(task_id, file_path):
    """为任务添加参考资料（使用现有memory功能）"""
    # 使用已有memory功能存储文档
    memory_item = memory_manager.store_document(file_path)

    # 获取元数据
    metadata_path = os.path.join(".ai", "tasks", task_id, "metadata.json")

    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # 添加memory_item ID到任务元数据
        if "memory_items" not in metadata:
            metadata["memory_items"] = []

        # 避免重复添加
        if memory_item["id"] not in metadata["memory_items"]:
            metadata["memory_items"].append(memory_item["id"])

            # 更新元数据文件
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            # 记录日志
            log_path = os.path.join(".ai", "tasks", task_id, "task.log")
            with open(log_path, "a") as f:
                f.write(f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 添加参考资料\n")
                f.write(f"- 文件: {os.path.basename(file_path)}\n")
                f.write(f"- Memory ID: {memory_item['id']}\n\n")
```

### 4.4 任务显示增强

简单修改现有`task show`命令实现，支持新增选项：

```python
def show_task(task_id, show_log=False, show_ref=False):
    """显示任务信息，支持日志和参考资料显示"""
    # 获取基本任务信息
    task_data = get_task_by_id(task_id)

    # 基本信息输出
    result = [f"# 任务: {task_data['title']} (ID: {task_id})\n"]

    # 显示日志
    if show_log:
        log_path = os.path.join(".ai", "tasks", task_id, "task.log")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                result.append("## 任务日志\n")
                result.append(f.read())
        else:
            result.append("*未找到任务日志*\n")
        return "\n".join(result)

    # 显示参考资料
    if show_ref:
        metadata_path = os.path.join(".ai", "tasks", task_id, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            result.append("## 参考资料\n")
            if metadata.get("memory_items"):
                for item_id in metadata["memory_items"]:
                    # 使用现有memory查询功能获取摘要
                    memory_item = memory_manager.get_item_by_id(item_id)
                    if memory_item:
                        result.append(f"- {memory_item.get('title')}\n")
                        if memory_item.get("summary"):
                            result.append(f"  {memory_item['summary']}\n")
            else:
                result.append("*没有相关参考资料*\n")
        else:
            result.append("*未找到任务元数据*\n")
        return "\n".join(result)

    # 显示任务概要
    result.append(f"**状态**: {task_data.get('status', '未设置')}\n")
    if task_data.get("description"):
        result.append(f"**描述**: {task_data['description']}\n")

    # 检查是否有增强信息
    task_dir = os.path.join(".ai", "tasks", task_id)
    if os.path.exists(task_dir):
        result.append("\n## 增强信息\n")
        result.append(f"- [查看日志](file://{os.path.join(task_dir, 'task.log')})\n")

        # 显示关联的memory_items数量
        metadata_path = os.path.join(task_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            if metadata.get("memory_items"):
                result.append(f"- 关联参考资料: {len(metadata['memory_items'])} 项\n")
                result.append("  使用 `vc task show <id> --ref` 查看详情\n")

    return "\n".join(result)
```

## 5. 命令行整合方案

通过简单修改现有命令处理逻辑，实现功能整合：

```python
# 修改任务创建命令
def handle_task_create(args):
    # 现有的任务创建逻辑
    task = create_task(args.title, args.description, args.labels)

    # 创建后调用钩子函数
    create_task_hook(task["id"], task)

    # 如果指定了参考资料
    if args.ref:
        add_reference_to_task(task["id"], args.ref)

    return task

# 修改任务显示命令
def handle_task_show(args):
    return show_task(args.task_id, args.log, args.ref)

# 修改任务更新命令
def handle_task_update(args):
    # 获取要更新的字段
    update_fields = {}
    for field in ["title", "description", "status", "priority", "assignee"]:
        if hasattr(args, field) and getattr(args, field) is not None:
            update_fields[field] = getattr(args, field)

    # 更新任务
    task = update_task(args.task_id, **update_fields)

    # 调用更新钩子
    task_update_hook(args.task_id, update_fields)

    # 如果有参考资料参数
    if args.ref:
        add_reference_to_task(args.task_id, args.ref)

    return task
```

## 6. 现有命令参数扩展

仅需修改已有命令的参数解析部分：

```python
# 扩展task show命令参数
task_show_parser.add_argument("--log", action="store_true", help="显示任务日志")
task_show_parser.add_argument("--ref", action="store_true", help="显示任务参考资料")

# 扩展task create命令参数
task_create_parser.add_argument("--ref", help="为任务添加参考文件")

# 扩展task update命令参数
task_update_parser.add_argument("--ref", help="为任务添加参考文件")
```

## 7. 整合与Memory系统

利用现有MemoryManager实现参考资料功能：

```python
# 在任务创建和更新时使用
def search_related_references(task_id, task_data):
    """查找与任务相关的参考资料"""
    search_query = f"{task_data['title']} {task_data.get('description', '')}"

    # 使用现有memory搜索功能
    results = memory_manager.search(search_query)

    # 将结果关联到任务
    for result in results:
        add_memory_item_to_task(task_id, result["id"])

# 简单的memory item关联函数
def add_memory_item_to_task(task_id, memory_item_id):
    """将memory item关联到任务"""
    metadata_path = os.path.join(".ai", "tasks", task_id, "metadata.json")

    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # 添加memory_item ID到任务元数据
        if "memory_items" not in metadata:
            metadata["memory_items"] = []

        # 避免重复添加
        if memory_item_id not in metadata["memory_items"]:
            metadata["memory_items"].append(memory_item_id)

            # 更新元数据文件
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
```

## 8. 总结

本实施方案通过最小化修改，实现了核心功能需求：

1. **简单直接**：仅添加必要钩子和扩展，无需大量新代码
2. **重用现有功能**：充分利用已有的命令和memory系统
3. **保持一致性**：保持命令格式一致，降低学习成本
4. **自动化整合**：在关键点自动触发功能整合

优势：

1. 实现简单，改动量小
2. 容易维护和扩展
3. 充分利用已有系统能力
4. 用户体验一致
5. 无需新增复杂组件或模型

本方案专注于实现PRD中定义的核心功能，同时大幅简化实现复杂度，确保系统的可维护性和可靠性。
