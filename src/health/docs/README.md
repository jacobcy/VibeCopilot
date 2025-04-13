# 健康检查模块文档

## 模块状态

当前健康检查模块处于功能完善阶段，已实现以下检查器：

- `system` - 系统环境检查（已启用）
- `command` - 命令完整性检查（已启用）
- `database` - 数据库状态检查（已启用）
- `enabled_modules` - 启用模块检查（已启用）
- `status` - 状态模块健康检查（**已启用，使用模拟实现**）

## 已知问题

1. **Status模块检查问题**
   - 问题描述：`RoadmapStatusProvider`初始化失败，原因是`RoadmapService`对象没有`session`属性
   - 临时解决方案：为status检查提供模拟实现，避免实际调用Status模块API
   - 正式解决方案：请参见`src/status/docs/dev-plan.md`中的开发计划

2. **未实现的检查器**
   - 配置文件中引用了一些未实现的检查器：`general`, `global`, `report`, `notifications`, `documentation`
   - 这些已在配置中注释掉，当实现后可以启用

## 使用注意事项

1. 运行健康检查时，可以检查所有已实现的模块：

```bash
python -m src.health.cli check --module all
```

2. 也可以检查单个模块：

```bash
python -m src.health.cli check --module system
python -m src.health.cli check --module command
python -m src.health.cli check --module database
python -m src.health.cli check --module enabled_modules
python -m src.health.cli check --module status  # 将使用模拟实现
```

## 解决计划

1. 按照`src/status/docs/dev-plan.md`修复Status模块问题
2. 待Status模块修复后，恢复完整的status检查器功能
3. 后续将逐步实现其他检查器

## 开发者指南

添加新检查器的步骤：

1. 在`src/health/checkers/`目录下创建新的检查器类
2. 确保新检查器继承自`BaseChecker`
3. 实现`check()`方法
4. 在`src/health/config/check_config.yaml`中添加配置
5. 更新`src/health/checkers/__init__.py`导入和导出新检查器
