# MemoryService 开发者使用指南

本文档展示如何在Python代码中直接使用`MemoryService`接口进行知识库操作，适用于需要在其他模块或服务中集成知识库功能的开发者。

## 基本使用

### 导入MemoryService

首先，从`src.memory`模块导入`MemoryService`类：

```python
from src.memory import MemoryService

# 创建MemoryService实例
memory_service = MemoryService()
```

### 创建笔记

```python
def create_example_note():
    # 准备数据
    title = "API使用示例"
    folder = "dev_examples"
    content = "# 这是通过API创建的笔记\n\n使用MemoryService接口可以轻松创建笔记。"
    tags = "API,示例,开发"

    # 调用API创建笔记
    success, message, data = memory_service.create_note(
        content=content,
        title=title,
        folder=folder,
        tags=tags
    )

    # 处理结果
    if success:
        print(f"笔记创建成功: {message}")
        return data.get("permalink")  # 返回笔记的永久链接
    else:
        print(f"笔记创建失败: {message}")
        return None
```

### 读取笔记

```python
def read_note_example(path):
    # 调用API读取笔记
    success, message, data = memory_service.read_note(path=path)

    # 处理结果
    if success:
        print(f"笔记标题: {data.get('title')}")
        print(f"笔记内容: {data.get('content')[:100]}...")  # 显示前100个字符
        print(f"创建时间: {data.get('created_at')}")
        return data
    else:
        print(f"读取笔记失败: {message}")
        return None
```

### 更新笔记

```python
def update_note_example(path, new_content):
    # 调用API更新笔记
    success, message, data = memory_service.update_note(
        path=path,
        content=new_content
    )

    # 处理结果
    if success:
        print(f"笔记更新成功: {message}")
        return True
    else:
        print(f"笔记更新失败: {message}")
        return False
```

### 删除笔记

```python
def delete_note_example(path):
    # 调用API删除笔记
    success, message, data = memory_service.delete_note(
        path=path,
        force=True  # 强制删除，不提示确认
    )

    # 处理结果
    if success:
        print(f"笔记删除成功: {message}")
        return True
    else:
        print(f"笔记删除失败: {message}")
        return False
```

## 搜索和列表

### 列出笔记

```python
def list_notes_example(folder=None):
    # 调用API列出笔记
    success, message, data = memory_service.list_notes(folder=folder)

    # 处理结果
    if success:
        print(f"找到 {len(data)} 个笔记:")
        for idx, note in enumerate(data, 1):
            print(f"{idx}. {note.get('title')} ({note.get('folder')})")
        return data
    else:
        print(f"列出笔记失败: {message}")
        return []
```

### 搜索笔记

```python
def search_notes_example(query):
    # 调用API搜索笔记
    success, message, data = memory_service.search_notes(query=query)

    # 处理结果
    if success:
        print(f"搜索'{query}'找到 {len(data)} 个结果:")
        for idx, note in enumerate(data, 1):
            print(f"{idx}. {note.get('title')} (相关度: {note.get('score', 'N/A')})")
        return data
    else:
        print(f"搜索笔记失败: {message}")
        return []
```

## 同步和导入导出

### 同步知识库

```python
def sync_memory_example():
    # 调用API同步知识库
    success, message, data = memory_service.sync_all()

    # 处理结果
    if success:
        print(f"知识库同步成功: {message}")
        if data:
            print(f"同步详情: {data}")
        return True
    else:
        print(f"知识库同步失败: {message}")
        return False
```

### 导入文档

```python
def import_documents_example(source_dir):
    # 调用API导入文档
    success, message, data = memory_service.import_documents(
        source_dir=source_dir,
        recursive=True  # 递归导入子目录
    )

    # 处理结果
    if success:
        print(f"文档导入成功: {message}")
        if data and "imported_count" in data:
            print(f"共导入 {data['imported_count']} 个文档")
        return True
    else:
        print(f"文档导入失败: {message}")
        return False
```

## 完整示例

下面是一个将上述功能组合起来的完整示例：

```python
from src.memory import MemoryService

def memory_service_demo():
    # 创建MemoryService实例
    memory_service = MemoryService()

    # 创建笔记
    title = "API完整示例"
    folder = "dev_examples"
    content = "# MemoryService API示例\n\n这是一个完整的API使用示例。"
    tags = "API,示例,完整"

    print("1. 创建笔记...")
    success, message, data = memory_service.create_note(
        content=content,
        title=title,
        folder=folder,
        tags=tags
    )

    if not success:
        print(f"创建笔记失败: {message}")
        return

    path = f"{folder}/{title}"
    print(f"笔记创建成功: {path}")

    # 读取笔记
    print("\n2. 读取笔记...")
    success, message, data = memory_service.read_note(path=path)
    if success:
        print(f"笔记内容: {data.get('content')}")

    # 更新笔记
    print("\n3. 更新笔记...")
    updated_content = f"{content}\n\n## 更新\n\n这是更新后的内容。"
    success, message, _ = memory_service.update_note(
        path=path,
        content=updated_content
    )
    print(f"更新结果: {message}")

    # 搜索笔记
    print("\n4. 搜索笔记...")
    success, message, results = memory_service.search_notes(query="API示例")
    if success and results:
        print(f"找到 {len(results)} 个相关笔记")

    # 删除测试笔记
    print("\n5. 删除笔记...")
    success, message, _ = memory_service.delete_note(path=path, force=True)
    print(f"删除结果: {message}")

    print("\n演示完成.")

if __name__ == "__main__":
    memory_service_demo()
```

## 错误处理最佳实践

使用`MemoryService`时，建议以下错误处理方法：

```python
def safe_memory_operation(operation_name, operation_func, *args, **kwargs):
    """安全执行内存操作，带错误处理"""
    try:
        success, message, data = operation_func(*args, **kwargs)
        if not success:
            print(f"{operation_name}失败: {message}")
            return None
        return data
    except Exception as e:
        print(f"{operation_name}出错: {str(e)}")
        return None

# 使用示例
note_data = safe_memory_operation(
    "读取笔记",
    memory_service.read_note,
    path="folder/title"
)
```

## 注意事项

1. `MemoryService`是单例模式，可以在应用的不同部分共享同一个实例
2. 所有方法都返回三元组 `(success, message, data)`，确保始终检查`success`值
3. 对于批量操作，考虑使用异步处理或分批处理，避免阻塞主线程
4. 在处理大量数据时，可以使用流式处理方法
5. 接口设计遵循了一致性原则，所有方法返回格式相同

遵循本文档中的指南和示例，可以轻松地在各种Python应用中集成VibeCopilot的知识库功能。
