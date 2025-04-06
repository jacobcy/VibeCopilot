# 路线图同步示例

这个目录包含与路线图同步相关的示例和工具，包括GitHub同步和YAML验证。

## 目录内容

### 1. GitHub同步工具

- `roadmap_github_sync.md` - GitHub同步详细文档
- `sync_instructions.sh` - 简洁的同步命令示例
- `demo_sync.py` - 功能完整的演示脚本
- `patch_db.py` - 数据库模拟修补工具

### 2. YAML验证工具

- `yaml_validator_usage.py` - YAML验证器使用示例脚本
- `yaml_validator_architecture.md` - 验证器架构文档
- `test_yaml_file.yaml` - 测试用例YAML文件
- `yaml_integration.py` - 验证器集成脚本
- `standard_roadmap_template.yaml` - 标准YAML模板

## YAML验证工具

VibeCopilot提供了一个路线图YAML验证工具，用于验证和修复路线图YAML文件格式。这个工具可以确保您的YAML文件满足路线图导入的要求。

### 功能特点

- ✅ 验证YAML文件格式和必填字段
- 🔍 检测无效的状态、优先级和进度值
- 🔧 自动修复常见错误并生成修复后的文件
- 📋 提供详细的错误和警告报告
- 📝 支持自定义模板和批量验证

### 使用方法

1. **通过使用示例**

   ```bash
   # 运行使用示例查看验证过程
   python examples/roadmap_sync/yaml_validator_usage.py
   ```

2. **通过命令行工具**

   ```bash
   # 验证YAML文件
   python src/roadmap/sync/yaml_validator_cli.py validate path/to/roadmap.yaml

   # 自动修复YAML文件
   python src/roadmap/sync/yaml_validator_cli.py validate path/to/roadmap.yaml --fix

   # 显示标准模板
   python src/roadmap/sync/yaml_validator_cli.py template

   # 生成标准模板文件
   python src/roadmap/sync/yaml_validator_cli.py template --output path/to/template.yaml
   ```

3. **在代码中使用**

   ```python
   from src.roadmap.sync.yaml_validator import RoadmapYamlValidator

   # 创建验证器
   validator = RoadmapYamlValidator()

   # 验证文件
   is_valid, messages, fixed_data = validator.validate("path/to/roadmap.yaml")

   # 检查验证结果
   if not is_valid:
       # 生成修复后的文件
       validator.generate_fixed_yaml(fixed_data, "path/to/fixed.yaml")
   ```

4. **集成到YAML同步服务**

   ```bash
   # 将验证器集成到YAML同步服务
   python examples/roadmap_sync/yaml_integration.py --integrate

   # 恢复原始YAML同步服务
   python examples/roadmap_sync/yaml_integration.py --restore

   # 测试验证功能
   python examples/roadmap_sync/yaml_integration.py --validate path/to/roadmap.yaml --fix
   ```

### 常见问题

1. **验证失败常见原因**
   - 缺少必填字段（title、description等）
   - 状态值无效（应使用指定的枚举值）
   - 进度数值超出范围（0-100）
   - 优先级值无效（应为P0、P1、P2、P3）

2. **模板路径问题**
   - 默认模板位于 `templates/roadmap/standard_roadmap_template.yaml`
   - 可以通过 `--template` 参数指定自定义模板

## GitHub同步指南

GitHub同步功能允许您将路线图数据同步到GitHub项目。详细使用说明请参考 [GitHub同步文档](roadmap_github_sync.md)。

## 完整开发流程

1. **创建路线图YAML文件**
   - 使用标准模板创建YAML文件
   - 通过验证工具确认格式正确

2. **导入到系统**
   - 使用YAML同步服务导入数据
   - 设置GitHub项目ID作为主题

3. **同步到GitHub**
   - 使用GitHub同步服务将数据同步到项目
   - 设置正确的环境变量和权限

4. **双向同步**
   - 支持从GitHub同步回本地数据库
   - 提供自动和手动同步选项

## 参考资料

- [VibeCopilot路线图YAML模板](../../templates/roadmap/standard_roadmap_template.yaml)
- [路线图服务实现](../../src/roadmap/service/roadmap_service.py)
- [YAML同步服务](../../src/roadmap/sync/yaml.py)
- [GitHub同步服务](../../src/roadmap/sync/github_sync.py)
