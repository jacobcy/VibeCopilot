---
task_id: T-MM-04
title: "模型统一迁移 - 处理枚举类型和共享类型"
description: "将原有规则和模板的数据模型实现迁移到统一模型，第四阶段：处理RuleType和TemplateVariableType枚举"
status: todo
priority: P1
created_at: 2024-06-01
estimated_hours: 2
assignees: ["jacobcy"]
tags: ["refactoring", "model-migration"]
---

# 模型统一迁移 - 处理枚举类型和共享类型

## 任务描述

根据模型统一迁移指南，将原有多个模型实现迁移到统一模型的第四阶段工作：更新所有使用旧版枚举类型（RuleType 和 TemplateVariableType）的代码，使用新的统一枚举定义。

## 实现细节

需要修改所有引用旧枚举定义的代码，更新为使用新的统一枚举定义。主要关注点在于将以下导入更改为使用新的路径：

```python
# 旧代码 - 从多个来源导入枚举
from src.rule_engine.models.rule import RuleType
from src.templates.models.template import TemplateVariableType
from src.db.models.template import TemplateVariableType

# 新代码 - 统一从base.py导入
from src.models.base import RuleType, TemplateVariableType
```

## 实现步骤

1. 识别所有使用旧枚举类型的模块：
   - 使用 RuleType 的模块
   - 使用 TemplateVariableType 的模块
   - 使用其他迁移到 base.py 的共享类型的模块

2. 更新每个模块中的枚举类型导入：
   - 修改 import 语句，使用新的枚举定义路径
   - 确保使用正确的枚举成员名称
   - 处理可能的枚举值比较逻辑

3. 处理因枚举定义微小变化导致的兼容性问题：
   - 检查枚举成员名称变更
   - 检查枚举比较逻辑
   - 处理字符串和枚举值转换

4. 执行测试确认变更正确：
   - 测试所有使用枚举类型的功能点
   - 验证枚举比较逻辑正常工作
   - 确保序列化和反序列化正确处理枚举

## 技术要点

- 新的统一枚举定义位于 `src.models.base` 模块中
- 枚举使用 `str, Enum` 作为基类，可以直接与字符串比较
- 注意检查代码中硬编码的枚举值字符串
- 检查 JSON 序列化和反序列化中对枚举的处理
- 可能需要更新使用枚举作为字典键的代码

## 完成标准

- 所有使用旧枚举定义的代码都已更新为使用新的统一枚举定义
- 枚举比较逻辑正常工作
- 枚举的序列化和反序列化正确
- 使用枚举的所有功能点正常工作
- 所有单元测试通过

## 相关资料

- 完整迁移指南：`docs/dev/model-migration-guide.md`
- 新枚举定义：`src/models/base.py`
- 原枚举定义：
  - `src/rule_engine/models/rule.py` 中的 RuleType
  - `src/templates/models/template.py` 中的 TemplateVariableType
  - `src/db/models/template.py` 中的 TemplateVariableType
