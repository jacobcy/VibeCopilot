# VibeCopilot 测试指南

## 测试概述

VibeCopilot 使用 pytest 作为主要测试框架，测试代码位于 `tests/` 目录下。测试按模块和类型组织在不同子目录中。

目前测试覆盖的主要模块：

- 数据库模型与服务 (`tests/db/`)
- 向量存储 (`tests/db/vector/`)
- 验证功能 (`tests/validation/`)
- 模板系统 (`tests/templates/`)
- CLI命令 (`tests/cli/`)
- 集成测试 (`tests/integration/`)

## 运行测试

### 运行所有测试

```bash
python -m pytest
```

### 运行特定模块的测试

```bash
# 运行数据库测试
python -m pytest tests/db

# 运行验证测试
python -m pytest tests/validation

# 运行集成测试
python -m pytest tests/integration
```

### 使用详细输出

```bash
python -m pytest -v
```

### 生成覆盖率报告

```bash
python -m pytest --cov=src tests/
```

## CI/CD集成

VibeCopilot 使用 GitHub Actions 进行持续集成测试。在以下情况下会触发测试：

1. 每次推送到主分支
2. 每次创建 Pull Request
3. 每周定时运行全面测试 (每周日12:00 UTC)

## 测试标记

我们使用以下测试标记来分类测试：

- `unit`: 标记单元测试（不依赖外部服务的独立测试）
- `integration`: 标记集成测试（需要依赖外部服务的测试）

使用示例：

```bash
# 仅运行单元测试
python -m pytest -m unit

# 仅运行集成测试
python -m pytest -m integration
```

## 添加新测试

添加新测试时，请遵循以下规则：

1. 测试文件应命名为 `test_*.py`
2. 测试类应命名为 `Test*`
3. 测试方法应命名为 `test_*`
4. 每个测试应关注单一功能点
5. 测试应独立且可重复
6. 使用模拟对象隔离外部依赖
7. 对于集成测试，添加 `@pytest.mark.integration` 标记

## 测试数据

测试所需的模拟数据和测试资源应放在 `tests/fixtures/` 目录下。
