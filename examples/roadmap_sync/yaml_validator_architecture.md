# 路线图YAML验证器架构设计

## 1. 架构概述

路线图YAML验证器采用了模块化设计，将大型验证器拆分为多个功能明确的小模块，每个模块遵循单一职责原则。这种设计提高了代码的可维护性、可测试性和可扩展性，同时降低了模块间的耦合度。

```
                      +-------------------+
                      | RoadmapYamlValidator |
                      +-------------------+
                              |
                              | 使用
                              v
+----------------+    +----------------+    +---------------+
| TemplateManager |--->| RoadmapValidator |--->| ValidatorOutput |
+----------------+    +----------------+    +---------------+
                              |
                              | 使用
                              v
                      +-------------------+
                      | SectionValidator  |
                      +-------------------+
                              |
                              | 使用
                              v
                      +-------------------+
                      | Schema Definitions |
                      +-------------------+
```

## 2. 模块说明

### 2.1 yaml_validator.py

**职责**: 提供统一的对外接口，作为其他模块的集成层
**设计思路**:

- 以简洁的API隐藏内部实现细节
- 组合各个子模块以实现完整功能
- 保持向后兼容性

关键方法:

- `validate()`: 验证YAML文件格式
- `check_and_suggest()`: 检查并提供修复建议
- `generate_fixed_yaml()`: 生成修复后的YAML文件
- `show_template()`: 显示标准模板

### 2.2 yaml_validator_schema.py

**职责**: 定义数据模式和常量
**设计思路**:

- 集中管理所有字段定义和枚举值
- 提供类型提示以增强代码可读性
- 独立于验证逻辑，便于修改和扩展

包含内容:

- 字段定义 (必填/可选)
- 状态枚举值
- 优先级枚举值
- 中文名称映射
- 默认模板结构

### 2.3 yaml_validator_template.py

**职责**: 管理模板加载和格式化
**设计思路**:

- 将模板管理逻辑与验证逻辑分离
- 提供灵活的模板加载策略
- 封装模板相关操作

关键方法:

- `_load_template()`: 加载模板数据
- `get_template()`: 获取模板数据
- `format_template()`: 格式化模板为YAML字符串

### 2.4 yaml_validator_section.py

**职责**: 验证路线图各部分（里程碑、史诗、故事、任务）格式
**设计思路**:

- 使用静态方法提供无状态验证功能
- 关注单个部分的验证细节
- 与上层验证逻辑分离

关键方法:

- `validate_section()`: 验证路线图的一个部分
- `get_section_name()`: 获取部分的中文名称

### 2.5 yaml_validator_core.py

**职责**: 实现核心验证逻辑
**设计思路**:

- 组织整体验证流程
- 调用各部分验证器
- 统一处理验证结果

关键方法:

- `validate_yaml()`: 验证YAML文件格式
- `_validate_roadmap_data()`: 验证路线图数据
- `_validate_*_section()`: 验证特定部分的方法

### 2.6 yaml_validator_output.py

**职责**: 处理验证结果输出
**设计思路**:

- 将输出格式化逻辑与验证逻辑分离
- 提供统一的报告生成接口
- 支持多种输出格式

关键方法:

- `generate_fixed_yaml()`: 生成修复后的YAML文件
- `format_check_report()`: 格式化检查报告

## 3. 工作流程

1. **初始化阶段**:
   - 创建`TemplateManager`实例
   - 创建`RoadmapValidator`实例，并传入模板管理器
   - 组装`RoadmapYamlValidator`接口

2. **验证阶段**:
   - 读取YAML文件
   - 验证整体结构 (由`RoadmapValidator`处理)
   - 验证各部分内容 (由`SectionValidator`处理)

3. **输出阶段**:
   - 生成验证报告 (由`ValidatorOutput`处理)
   - 可选生成修复后的文件

## 4. 设计原则

1. **单一职责原则**:
   每个模块只负责单一功能，如模板管理、部分验证等

2. **开放封闭原则**:
   模块设计为可扩展，无需修改现有代码即可添加新功能

3. **依赖倒置原则**:
   高层模块不依赖低层模块的具体实现

4. **接口隔离原则**:
   对外提供简洁统一的接口，隐藏内部实现细节

5. **组合优于继承**:
   使用组合方式组装模块，而非继承关系

## 5. 示例用法

```python
# 基本用法
from src.roadmap.validator.yaml_validator  import RoadmapYamlValidator

validator = RoadmapYamlValidator()
is_valid, report = validator.check_and_suggest("path/to/roadmap.yaml", fix=True)
print(report)

# 高级用法 - 直接使用子模块
from src.roadmap.validator.yaml_validator _template import TemplateManager
from src.roadmap.validator.yaml_validator _core import RoadmapValidator

template_manager = TemplateManager()
validator = RoadmapValidator(template_manager)
is_valid, messages, fixed_data = validator.validate_yaml("path/to/roadmap.yaml")
```

## 6. 扩展点

1. **添加新的验证规则**:
   - 在`yaml_validator_schema.py`中添加新的字段定义
   - 在`yaml_validator_section.py`中添加对应的验证逻辑

2. **支持新的输出格式**:
   - 在`yaml_validator_output.py`中添加新的格式化方法

3. **自定义模板加载策略**:
   - 扩展`TemplateManager`类的模板加载逻辑
