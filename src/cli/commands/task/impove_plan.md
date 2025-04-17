# Task CLI 命令改进计划 (状态更新: YYYY-MM-DD)

本文档记录了`src/cli/commands/task`目录下代码存在的问题及修复计划。

---

**当前状态总结 (YYYY-MM-DD):**

* `delete.py`, `show.py`, `list.py`, `comment.py`, `link.py` 已基本实现命令层与服务层的分离。
* `create.py` 和 `update.py` 已初步重构，将数据库访问和文件引用逻辑委托给服务层 (`TaskService`, `MemoryService`)，但依赖服务层方法的完善。
* `TaskService` 的 `create_task`, `update_task`, `log_task_activity` 方法需要验证或实现以支持 CLI 的调用。
* `MemoryService` 的文件处理接口 (`create_note`) 已被 CLI 调用，但更新文件引用的逻辑（避免重复创建）可能需要优化。

---

**原始问题 (CLI核心命令层 与 服务层交互):**

1. **数据库访问混乱 (`core/*.py`)**:
    * [已处理] `create.py`, `update.py` 中直接访问仓库。

2. **文件引用处理不当 (`TaskService`, `core/update.py`, `core/create.py`)**:
    * [已处理] `create.py` 和 `update.py` 使用旧的 `store_ref_to_memory`。
    * [待优化] `update.py` 文件引用更新逻辑可能导致重复笔记。

3. **文件路径依赖 (`core/*.py`)**:
    * [已处理] `create.py` 和 `update.py` 包含直接的文件路径操作（如日志）。

**修复方案及当前进度:**

* **目标**: 修正文件引用处理逻辑，让 CLI 命令尽可能通过服务层接口执行操作。

1. **重构 `create.py`**: ✅ **(已完成 - CLI层)**
    * 已移除直接数据库访问和文件操作。
    * 已改为调用 `TaskService.create_task`。
    * 已改为调用 `MemoryService.create_note` 处理 `ref_path`。
    * 日志记录改为调用 `TaskService.log_task_activity` (如果存在)。

2. **重构 `delete.py`, `comment.py`, `link.py`, `list.py`**: ✅ **(已完成)**
    * 这些模块已调用对应的 `TaskService` 方法。

3. **重构 `update.py`**: ✅ **(已完成 - CLI层)**
    * 已移除直接数据库访问和文件操作。
    * 已改为调用 `TaskService.update_task`。
    * 已改为调用 `MemoryService.create_note` 处理 `ref_path`。
    * 日志记录改为调用 `TaskService.log_task_activity` (如果存在)。

4. **部分重构 `show.py`**: ✅ **(已完成)**
    * 使用 `TaskService` 获取任务信息和评论。

5. **验证/实现 `TaskService` 支持方法**: ⏳ **(进行中)**
    * **待办**: 确认/实现 `TaskService.create_task` 接受 CLI 参数并完成数据库操作。
    * **待办**: 确认/实现 `TaskService.update_task` 接受 CLI 参数并完成数据库操作。
    * **待办**: 确认/实现 `TaskService.log_task_activity` 用于记录任务活动。

6. **验证/优化 `MemoryService` 文件处理**: ⏳ **(进行中)**
    * **待办**: 考虑优化 `update.py` 文件引用逻辑，避免重复创建笔记。

**后续工作:**

* 完成 `TaskService` 相关方法的实现和验证。
* 测试 `task create` 和 `task update` 命令的功能，特别是文件引用和日志记录部分。
* 根据测试结果，优化 `update.py` 中文件引用的处理逻辑。
* 更新相关测试用例。
