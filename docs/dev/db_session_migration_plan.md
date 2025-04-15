# 数据库会话管理统一迁移计划

## 背景

当前项目中存在两种方式获取数据库会话：

1. 通过 `src/db/session.py` 导入 `SessionLocal` 和 `get_db`
2. 通过 `src/db/__init__.py` 导入的各种函数

为了统一代码风格并降低维护成本，我们决定统一使用 `src/db` 包提供的会话管理功能。

## 已完成迁移任务

1. ✅ `src/db/__init__.py` 已增加 `SessionLocal` 和 `get_db` 函数，保持与 `session.py` 提供的功能完全一致
2. ✅ `src/db/session.py` 已添加弃用警告，提示开发者使用 `src/db` 导入
3. ✅ 所有依赖`src/db/session`的文件已更新为使用`src/db`导入
4. ✅ 已创建并运行检查脚本`scripts/check_db_session_imports.py`，确认没有遗漏的导入

## 迁移进度

| 文件 | 状态 | 日期 |
|------|------|------|
| `src/templates/README.md` | ✅ 已修改 | 2024-06-XX |
| `src/cli/commands/memory/handlers/mcp_handlers.py` | ✅ 已修改 | 2024-06-XX |
| `src/memory/memory_manager.py` | ✅ 已修改 | 2024-06-XX |
| `src/flow_session/core/utils.py` | ✅ 已修改 | 2024-06-XX |
| `examples/memory_integration_example.py` | ✅ 已修改 | 2024-06-XX |

## 后续计划

1. 保持当前的双重支持状态一个版本周期，确保兼容性
2. 在下一个主版本更新（v1.X.0）中:
   - 修改`src/db/session.py`，添加强烈弃用警告，提示即将在下个版本中移除
   - 添加更新计划到版本发布文档中
3. 在后续主版本更新（v2.0.0）中:
   - 完全移除`src/db/session.py`文件
   - 确认没有依赖项引用此模块

## 注意事项

1. ✅ 所有新代码应直接使用 `from src.db import SessionLocal, get_db` 方式导入
2. ✅ 修改现有代码时，应同步更新导入方式
3. ✅ 在代码审查时注意确认导入方式是否符合新标准

## 预期收益

1. ✅ 统一的数据库会话管理接口
2. ✅ 降低维护成本和复杂度
3. ✅ 符合项目代码规范，提高可读性

## 经验总结

本次迁移成功统一了数据库会话管理接口，采用了渐进式迁移策略：

1. 先在`__init__.py`中增加兼容函数
2. 给原有模块添加弃用警告但保持功能正常
3. 通过脚本检查确保全部迁移完成
4. 计划在未来版本中完全移除过时模块

这种方式确保了平滑过渡，没有引入破坏性变更，可作为其他模块重构的参考模式。
