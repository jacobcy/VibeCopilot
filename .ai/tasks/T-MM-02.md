---
task_id: T-MM-02
title: "模型统一迁移 - 更新数据库模型引用"
description: "将原有规则和模板的数据模型实现迁移到统一模型，第二阶段：更新数据库模型引用"
status: todo
priority: P1
created_at: 2024-06-01
estimated_hours: 3
assignees: ["jacobcy"]
tags: ["refactoring", "model-migration"]
---

# 模型统一迁移 - 更新数据库模型引用

## 任务描述

根据模型统一迁移指南，将原有多个模型实现迁移到统一模型的第二阶段工作：更新所有使用旧数据库模型的代码，确保它们引用新的统一数据库模型。

## 实现细节

需要修改所有引用旧数据库模型的代码，使其引用新的数据库模型。主要关注数据访问层的代码，包括存储库、服务类和数据访问对象。

具体更新方式如下：

```python
# 旧代码
from src.db.models.template import Template

# 新代码
from src.models.db import Template
```

## 实现步骤

1. 识别使用旧数据库模型的所有模块：
   - `src/db/repositories/` 下的存储库类
   - `src/db/service.py` 中的数据库服务
   - 其他直接与数据库模型交互的代码

2. 更新每个模块中的数据库模型引用：
   - 修改 import 语句，使用新的数据库模型路径
   - 确保导入的类名正确
   - 保持代码风格一致

3. 处理因数据库模型结构微小变化导致的兼容性问题：
   - 检查字段名称变更
   - 检查新增的必要字段
   - 检查关联关系变化

4. 执行测试确认变更正确：
   - 运行单元测试确保数据访问功能正常
   - 验证数据库操作的增删改查正常工作
   - 验证关联关系正确维护

## 技术要点

- 新的数据库模型位于 `src.models.db` 包下
- 数据库模型已提供与 Pydantic 模型的互相转换方法
  ```python
  # 数据库模型转 Pydantic 模型
  pydantic_rule = db_rule.to_pydantic()

  # Pydantic 模型转数据库模型
  db_rule = Rule.from_pydantic(pydantic_rule)
  ```
- 注意检查数据库操作中对模型特定字段的引用
- 可能需要更新查询条件中使用的字段名
- 注意检查 SQLAlchemy 关系定义的变化

## 完成标准

- 所有数据库相关代码都已更新为使用新的数据库模型
- 所有数据库操作正常工作
- 所有单元测试通过
- 与数据库模型相关的高级功能（如规则的持久化）正常工作
- 没有引入额外的 SQL 查询或性能下降

## 相关资料

- 完整迁移指南：`docs/dev/model-migration-guide.md`
- 新数据库模型定义：`src/models/db/` 目录
- 旧数据库模型定义：`src/db/models/` 目录
- 数据库仓库实现：`src/db/repositories/` 目录
