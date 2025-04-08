# VibeCopilot 测试与 CI 说明

## 概述

VibeCopilot 项目使用 GitHub Actions 进行持续集成（CI），并使用 pytest 作为测试框架。本文档介绍如何在本地运行测试以及如何使用 CI 系统。

## 当前测试覆盖的模块

我们已经为以下关键模块添加了测试：

1. **数据库模型与服务** (`tests/db/`):
   - 数据库模型（Epic、Story、Task）的基本功能和关系
   - 数据库服务的 CRUD 操作

2. **向量存储** (`tests/db/vector/`):
   - VectorStore 抽象类
   - BasicMemoryAdapter 实现

3. **验证功能** (`tests/validation/`):
   - ValidationResult 类
   - BaseValidator 抽象类

4. **模板系统** (`tests/templates/`):
   - 模板加载器
   - 规则生成器
   - 模板引擎

5. **CLI 命令** (`tests/cli/`):
   - 基础命令功能
   - Memory 命令

6. **集成测试** (`tests/integration/`):
   - Memory 管理器与 BasicMemoryAdapter 的集成

## 本地运行测试

### 使用提供的脚本

我们提供了便利脚本来运行测试：

**Linux/Mac**:
```bash
# 运行所有测试
./scripts/run_tests.sh

# 运行特定模块的测试
./scripts/run_tests.sh db
./scripts/run_tests.sh validation
./scripts/run_tests.sh cli/commands/memory
```

**Windows**:
```batch
:: 运行所有测试
scripts\run_tests.bat

:: 运行特定模块的测试
scripts\run_tests.bat db
scripts\run_tests.bat validation
scripts\run_tests.bat cli\commands\memory
```

### 直接使用 pytest

```bash
# 运行所有测试
python -m pytest

# 运行特定模块的测试
python -m pytest tests/db
python -m pytest tests/validation
python -m pytest tests/cli/commands/memory

# 运行带标记的测试
python -m pytest -m unit
python -m pytest -m integration

# 详细输出
python -m pytest -v
```

## 生成覆盖率报告

我们提供了一个脚本来生成测试覆盖率报告：

```bash
./scripts/coverage.sh
```

这将运行所有测试并生成 HTML 格式的覆盖率报告，报告将保存在 `coverage/html/` 目录下。脚本会尝试自动打开报告。

您也可以直接使用 pytest：

```bash
python -m pytest --cov=src tests/ --cov-report=term --cov-report=html:coverage/html
```

## CI 配置

VibeCopilot 项目配置了两种 GitHub Actions 工作流：

1. **CI 工作流** (`.github/workflows/ci.yml`):
   - 在每次推送到 main 分支和每个 Pull Request 上运行
   - 使用 Python 3.9 和 3.10 环境
   - 运行代码风格检查、类型检查和所有测试

2. **全面测试工作流** (`.github/workflows/test-all.yml`):
   - 按计划运行（每周日）或手动触发
   - 使用 Python 3.9、3.10 和 3.12 环境
   - 对各个模块进行独立测试
   - 生成并上传测试覆盖率报告

## 添加新测试

添加新测试时，请遵循这些指导原则：

1. 为每个新功能或模块添加单元测试
2. 使用 `tests/<模块名>/test_<功能>.py` 的命名格式
3. 使用模拟对象隔离外部依赖
4. 尽量保持测试简单且关注单一功能点
5. 按照轻量级原则，只测试关键功能路径

例如，要为新模块 `roadmap_service` 添加测试：

1. 创建目录：`tests/roadmap/`
2. 创建测试文件：`tests/roadmap/test_roadmap_service.py`
3. 实现测试类和方法，专注于核心功能

## 测试技巧与最佳实践

- **使用 MagicMock 和 patch**: 隔离外部依赖
- **使用 fixture**: 在测试之间重用测试数据和设置
- **测试边缘情况**: 确保代码在异常情况下正常工作
- **避免过度测试**: 优先测试核心功能和关键路径
- **避免过度模拟**: 考虑使用集成测试验证组件的协作
