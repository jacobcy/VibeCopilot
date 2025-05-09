# 数据库会话管理统一 - CHANGELOG条目

## 当前版本 (vX.Y.Z)

### 改进

- **数据库会话管理统一**: 统一了数据库会话管理接口，所有模块现在都从`src.db`包直接导入`SessionLocal`和`get_db`，而不是使用`src.db.session`。原模块添加了弃用警告但保持向后兼容。
- **新增检查工具**: 添加了`scripts/check_db_session_imports.py`脚本，用于检查项目中是否有模块仍在使用过时的导入方式。

### 文档

- **添加迁移计划**: 新增`docs/dev/db_session_migration_plan.md`文档，详细说明数据库会话管理统一的迁移计划和进度。

## 下一个主版本 (v1.X.0) - 计划

### 改进

- **增强弃用警告**: 将更新`src.db.session`模块，添加更强烈的弃用警告，明确表示该模块将在v2.0.0版本中移除。

## 未来主版本 (v2.0.0) - 计划

### 破坏性变更

- **移除过时模块**: 完全移除`src.db.session`模块，所有数据库会话管理功能将只通过`src.db`包提供。
