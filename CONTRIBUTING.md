# 贡献指南

感谢您考虑为VibeCopilot项目做出贡献！这里是一些指导方针，帮助您参与项目开发。

## 行为准则

本项目采用贡献者契约行为准则。参与者应遵守这一准则。请报告不可接受的行为。

## 如何贡献

### 提交问题

- 使用GitHub Issues提交问题或建议
- 在提交之前，请先搜索现有issues，避免重复
- 使用清晰的标题和详细描述，包括复现步骤（如果适用）
- 如果可能，提供错误日志、截图或相关环境信息

### 拉取请求（Pull Requests）

1. Fork仓库并创建您的分支
2. 确保代码符合项目的编码风格
3. 确保所有测试通过
4. 提交有意义的commit消息
5. 提交PR到`main`分支

### 分支命名约定

- 功能分支: `feature/description`
- 修复分支: `fix/issue-description`
- 文档分支: `docs/description`
- 重构分支: `refactor/description`

### 提交消息格式

我们遵循[Conventional Commits](https://www.conventionalcommits.org/)规范：

```
<类型>[可选作用域]: <描述>

[可选正文]

[可选页脚]
```

类型包括：

- feat: 新功能
- fix: 修复Bug
- docs: 文档更改
- style: 不影响代码含义的更改（空格、格式等）
- refactor: 既不修复错误也不添加功能的代码更改
- perf: 改进性能的代码更改
- test: 添加或修正测试
- build: 影响构建系统或外部依赖的更改
- ci: CI配置文件和脚本的更改

## 开发流程

### 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/yourjacobcy/vibecopilot.git
cd VibeCopilot

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 安装pre-commit钩子
pre-commit install
```

### 运行测试

```bash
# 运行所有测试
pytest

# 带覆盖率报告
pytest --cov=vibecopilot
```

### 代码质量检查

```bash
# 运行黑色格式化
black vibecopilot tests

# 运行isort导入排序
isort vibecopilot tests

# 运行flake8代码检查
flake8 vibecopilot tests

# 运行mypy类型检查
mypy vibecopilot
```

## 文档

- 为所有新功能添加文档
- 更新文档以反映代码变更
- 使用清晰简洁的语言

## 发布过程

项目维护者将负责发布流程：

1. 更新CHANGELOG.md
2. 更新版本号
3. 创建发布标签
4. 构建并发布到PyPI

## 获取帮助

如果您需要帮助，请：

- 在GitHub Issues上提问
- 联系项目维护者

再次感谢您的贡献！
