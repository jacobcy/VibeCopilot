---
task_id: T-MM-01
title: "模型统一迁移 - 更新导入路径"
description: "将原有规则和模板的数据模型实现迁移到统一模型，第一阶段：更新导入路径"
status: completed
priority: P1
created_at: 2024-06-01
completed_at: 2024-06-01
estimated_hours: 4
actual_hours: 2
assignees: ["jacobcy"]
tags: ["refactoring", "model-migration"]
---

# 模型统一迁移 - 更新导入路径

## 任务描述

根据模型统一迁移指南，将原有多个模型实现迁移到统一模型的第一阶段工作：更新所有模块中的导入路径，确保引用新的统一模型定义。

## 实现细节

需要修改所有引用旧模型定义的导入语句，将它们更新为使用新的模型路径。具体的旧路径到新路径的映射关系如下：

| 旧路径 | 新路径 |
|-------|--------|
| `from src.rule_engine.models.rule import *` | `from src.models.rule import *` |
| `from src.rule_engine.models.template import *` | `from src.models.template import *` |
| `from src.templates.models.rule import *` | `from src.models.rule import *` |
| `from src.templates.models.template import *` | `from src.models.template import *` |
| `from src.db.models import Base` | `from src.models.db import Base` |
| `from src.db.models.template import *` | `from src.models.db.template import *` |

## 实现步骤

1. 识别使用旧模型路径的所有模块：
   - `src/rule_engine/` 下的模块
   - `src/templates/` 下的模块
   - `src/adapters/rule_parser/` 下的模块
   - `src/db/` 下的模块

2. 更新每个模块中的导入语句：
   - 修改 import 语句，使用新的模型路径
   - 确保导入的类名和模块成员正确
   - 保持代码风格一致

3. 处理因模型结构微小变化导致的兼容性问题：
   - 检查字段名称变更
   - 检查新增的必要字段
   - 检查方法签名变化

4. 执行测试确认变更正确：
   - 运行单元测试确保功能正常
   - 验证规则的创建、读取、更新和删除功能
   - 验证模板的解析、渲染和应用功能

## 技术要点

- 引用新模型时，优先使用具体的类名而非星号导入
- 如果有对旧模型的扩展或自定义，需确保与新模型兼容
- 注意检查 `RuleType` 和 `TemplateVariableType` 枚举的引用
- 数据库模型与 Pydantic 模型的转换方法已更新，使用新提供的方法
- 定位所有导入点时，可以使用 grep 或编辑器的全局搜索功能

## 完成标准

- 所有模块中使用旧模型路径的导入语句都已更新为使用新模型路径
- 项目可以成功编译，没有导入错误
- 所有单元测试通过
- 规则的创建、读取、更新和删除功能正常
- 模板的解析、渲染和应用功能正常

## 相关资料

- 完整迁移指南：`docs/dev/model-migration-guide.md`
- 新模型定义：`src/models/` 目录
- 旧模型定义：
  - `src/rule_engine/models/`
  - `src/templates/models/`
  - `src/db/models/`
