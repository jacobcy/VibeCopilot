我来给下一位开发者写一个关于任务系统与Memory对接的改动说明。

# 任务系统与Memory对接改动说明

## 目标

实现任务管理系统与Memory系统的深度集成，便于任务引用相关知识库内容，提升任务上下文的完整性。

## 当前实现

目前我们已经实现了：

- 任务日志系统（.ai/tasks/<task_id>/task.log）
- 基本参考文档关联功能（通过--ref参数）
- 日志查看命令（task show --log）
- 参考资料查看命令（task show --ref）

## 需要实现的内容

1. **Memory系统直接集成**
   - 使用Memory API代替当前的文件路径引用方式

2. **关联机制**
   - 从任务关联到Memory项目

3. **智能推荐系统**
   - 根据任务内容自动推荐相关Memory项
   - 关联后在任务显示中提供摘要

## 任务-Memory集成方案

### 1. 任务reposity扩展

扩展任务reposity结构，添加memory_references字段：

```python
{
    "id": "task_id",
    "title": "任务标题",
    "created_at": "2023-01-01T00:00:00",
    "memory_references": [
        {
            "permalink": "memory://references/document_name",
            "title": "文档名称",
            "added_at": "2023-01-01T00:00:00"
        }
    ]
}
```

### 2. 添加Memory引用功能

```python
# 在create.py和update.py添加以下函数
async def link_to_memory(task_id: str, file_path: str) -> Dict[str, Any]:
    """将文件存储到Memory并关联到任务

    Args:
        task_id: 任务ID
        file_path: 文件路径

    Returns:
        存储结果
    """
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return {"success": False, "error": f"读取文件失败: {e}"}

    # 准备元数据
    file_name = os.path.basename(file_path)
    metadata = {
        "title": file_name,
        "tags": f"reference,task:{task_id}",
        "related_task": task_id,
        "file_path": file_path
    }

    # 使用Memory系统存储
    from src.memory import EntityManager
    entity_manager = EntityManager()
    try:
        # 存储到references文件夹
        result = await entity_manager.create_entity(
            entity_type="reference",
            properties=metadata,
            content=content
        )

        # 更新任务元数据
        metadata_path = os.path.join(".ai", "tasks", task_id, "metadata.json")
        if os.path.exists(os.path.dirname(metadata_path)):
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    task_metadata = json.load(f)
            else:
                task_metadata = {"id": task_id, "memory_references": []}

            # 添加新引用
            if "memory_references" not in task_metadata:
                task_metadata["memory_references"] = []

            reference_info = {
                "permalink": result["permalink"],
                "title": metadata["title"],
                "added_at": datetime.now().isoformat()
            }

            # 避免重复添加
            existing_permalinks = [ref["permalink"] for ref in task_metadata["memory_references"]]
            if result["permalink"] not in existing_permalinks:
                task_metadata["memory_references"].append(reference_info)

                # 保存更新后的元数据
                os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(task_metadata, f, indent=2)

                # 记录到任务日志
                append_to_task_log(task_id, "添加参考文档", {
                    "文档路径": file_path,
                    "Memory链接": result["permalink"]
                })

                return {"success": True, "permalink": result["permalink"]}
            else:
                return {"success": True, "message": "文档已存在", "permalink": result["permalink"]}

    except Exception as e:
        logger.error(f"存储到Memory失败: {e}")
        # 仍然记录到任务日志，但标记为失败
        append_to_task_log(task_id, "添加参考文档失败", {
            "文档路径": file_path,
            "错误": str(e)
        })
        return {"success": False, "error": f"存储到Memory失败: {e}"}
```

### 3. 修改Task创建和更新命令

```python
# 在execute_create_task函数中添加
if ref_path:
    # 记录到任务日志
    create_task_log(new_task.id, title, description, assignee, ref_path)

    # 存储到Memory并关联
    await link_to_memory(new_task.id, ref_path)

# 在execute_update_task函数中添加
if ref_path:
    # 存储到Memory并关联
    await link_to_memory(task_id, ref_path)
```

### 4. 修改--ref显示实现

```python
# 在show.py中的show_ref处理部分
if show_ref:
    # 获取任务元数据
    metadata_path = os.path.join(".ai", "tasks", task_id, "metadata.json")
    memory_refs = []

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                task_metadata = json.load(f)

            # 获取Memory引用
            if "memory_references" in task_metadata and task_metadata["memory_references"]:
                from src.memory import EntityManager
                entity_manager = EntityManager()

                console.print("\n[bold green]参考资料:[/bold green]")

                # 获取并展示每个引用的详细信息
                for ref in task_metadata["memory_references"]:
                    permalink = ref["permalink"]
                    entity = await entity_manager.get_entity(permalink)

                    if entity:
                        title = entity["name"]
                        source_path = entity["properties"].get("file_path", "未知路径")
                        added_at = ref.get("added_at", "未记录时间")

                        console.print(f"- {title}")
                        console.print(f"  路径: {source_path}")
                        console.print(f"  添加时间: {added_at}")
                        console.print(f"  Memory链接: {permalink}")
                        console.print("")

                        memory_refs.append(permalink)
                    else:
                        console.print(f"- {ref['title']} [dim](不可访问)[/dim]")
        except Exception as e:
            logger.error(f"读取Memory引用时出错: {e}")

    # 如果没有从元数据中找到引用，回退到从日志中查找
    if not memory_refs:
        # 现有的从日志中提取参考文档的代码
        log_path = os.path.join(".ai", "tasks", task_id, "task.log")
        if os.path.exists(log_path):
            # 现有代码...
```

### 5. 添加Memory搜索功能

```python
# 添加基于任务搜索Memory的命令
@click.command(name="search-memory", help="搜索与任务相关的Memory内容")
@click.argument("task_id", required=False)
@click.option("--limit", "-l", default=5, help="最大结果数量")
def search_task_memory(task_id=None, limit=5):
    """搜索与任务相关的Memory内容"""
    result = execute_search_task_memory(task_id, limit)
    if result["status"] == "success":
        return 0
    else:
        return 1

async def execute_search_task_memory(task_id=None, limit=5):
    """执行任务相关Memory搜索"""
    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None
    }

    try:
        # 如果未提供task_id，使用当前任务
        if not task_id:
            current_task = task_service.get_current_task()
            if not current_task:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = "未指定任务ID且没有当前任务"
                console.print("[bold red]错误:[/bold red] 未指定任务ID且没有当前任务")
                return results
            task_id = current_task.id

        # 获取任务信息
        task = task_repo.get_by_id(task_id)
        if not task:
            results["status"] = "error"
            results["code"] = 404
            results["message"] = f"未找到任务 {task_id}"
            console.print(f"[bold red]错误:[/bold red] 未找到任务 {task_id}")
            return results

        # 使用任务标题和描述构建搜索查询
        search_query = f"{task.title} {task.description or ''}"

        # 使用Memory API搜索
        from src.memory import EntityManager
        entity_manager = EntityManager()
        search_results = await entity_manager.search_entities(search_query, limit=limit)

        # 显示结果
        console.print(f"\n[bold green]与任务 {task_id} 相关的Memory内容:[/bold green]")

        if search_results:
            for result in search_results:
                title = result["name"]
                entity_type = result["type"]
                permalink = result["permalink"]
                score = result.get("score", 0)

                console.print(f"- {title} [类型: {entity_type}] [相关度: {score:.2f}]")
                console.print(f"  链接: {permalink}")
                console.print("")
        else:
            console.print("[yellow]未找到相关内容[/yellow]")

        results["data"] = search_results
        results["message"] = f"成功搜索到与任务 {task_id} 相关的Memory内容"

    except Exception as e:
        logger.error(f"搜索Memory时出错: {e}")
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"搜索Memory时出错: {e}"
        console.print(f"[bold red]错误:[/bold red] {e}")

    return results
```

### 6. 集成到命令行

```python
# 在task_click.py中添加新命令
from .core.memory import search_task_memory

@task.command()
@click.pass_context
def search_memory(ctx, **kwargs):
    """搜索与任务相关的Memory内容"""
    return search_task_memory(**kwargs)
```

## 总结

这个实现方案的关键特点是：

1. **单向依赖**：Task系统依赖Memory系统，但Memory系统不依赖Task系统
2. **利用现有API**：直接使用Memory系统提供的API，不修改Memory系统代码
3. **最少修改**：只需修改Task相关代码，不影响其他系统
4. **向后兼容**：保留现有的参考资料记录方式，同时增强功能
5. **解耦设计**：Memory系统作为基础设施，Task系统作为客户端
6. **双级实现**：使用文件系统存储元数据作为索引，使用Memory系统存储实际内容

这个设计让Task系统能够利用Memory系统的强大功能，同时保持系统架构的清晰和模块化。
