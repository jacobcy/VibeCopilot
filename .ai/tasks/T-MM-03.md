---
task_id: T-MM-03
title: "模型统一迁移 - 更新模型转换逻辑"
description: "将原有规则和模板的数据模型实现迁移到统一模型，第三阶段：更新模型转换逻辑"
status: todo
priority: P1
created_at: 2024-06-01
estimated_hours: 4
assignees: ["jacobcy"]
tags: ["refactoring", "model-migration"]
---

# 模型统一迁移 - 更新模型转换逻辑

## 任务描述

根据模型统一迁移指南，将原有多个模型实现迁移到统一模型的第三阶段工作：更新所有模型转换逻辑，使用新提供的转换方法替换旧的自定义转换代码。

## 实现细节

新的数据库模型已经提供了与 Pydantic 模型的互相转换方法，需要识别并更新所有自定义的模型转换逻辑，使用新提供的方法。

```python
# 旧代码 - 自定义转换
pydantic_rule = Rule(
    id=db_rule.id,
    name=db_rule.name,
    # ... 其他字段手动映射
)

# 新代码 - 使用内置转换方法
pydantic_rule = db_rule.to_pydantic()

# 旧代码 - 自定义转换
db_rule = models.Rule(
    id=pydantic_rule.id,
    name=pydantic_rule.name,
    # ... 其他字段手动映射
)

# 新代码 - 使用内置转换方法
db_rule = Rule.from_pydantic(pydantic_rule)
```

## 实现步骤

1. 识别所有包含模型转换逻辑的代码：
   - 数据访问层的 CRUD 操作
   - 从数据库记录创建领域模型的代码
   - 将领域模型持久化到数据库的代码

2. 更新模型转换代码：
   - 将手动映射字段的代码替换为使用内置转换方法
   - 确保使用正确的转换方向（数据库模型 -> Pydantic 或 Pydantic -> 数据库模型）
   - 处理任何特殊的转换逻辑或自定义映射

3. 处理新增字段和模型结构变化：
   - 检查新模型可能增加的字段
   - 处理字段类型或命名的变化
   - 确保所有必要的关联关系被正确处理

4. 执行测试确认变更正确：
   - 测试所有使用转换方法的功能点
   - 验证转换后的模型包含所有必要的数据
   - 确保复杂对象（如嵌套集合）的转换正确

## 技术要点

- 使用数据库模型的 `to_pydantic()` 方法将数据库模型转换为 Pydantic 模型
- 使用 `Model.from_pydantic()` 类方法将 Pydantic 模型转换为数据库模型
- 注意处理与模型转换相关的异常情况
- 确保转换过程中没有数据丢失
- 处理集合类型字段（如列表、字典）的正确转换
- 可能需要添加额外的转换逻辑处理特殊情况

## 完成标准

- 所有自定义的模型转换代码都已替换为使用内置转换方法
- 转换后的模型包含原模型的所有数据
- 转换过程中不会丢失或错误转换任何字段
- 与模型转换相关的所有功能点正常工作
- 所有单元测试通过

## 相关资料

- 完整迁移指南：`docs/dev/model-migration-guide.md`
- 新模型定义：`src/models/` 目录
- 数据库模型定义：`src/models/db/` 目录
- 数据库模型转换方法：`to_pydantic()` 和 `from_pydantic()`
