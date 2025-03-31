# VibeCopilot 测试与质量保障指南

本文档提供 VibeCopilot 项目的测试策略和质量保障最佳实践，确保项目代码质量和文档一致性。

## 1. 测试策略概述

VibeCopilot 采用多层次测试策略，确保软件质量和文档一致性：

| 测试层次 | 目标 | 工具 | 责任人 |
|---------|------|------|-------|
| 单元测试 | 验证独立组件功能 | Pytest, Jest | 开发人员 |
| 集成测试 | 验证组件间交互 | Pytest, Supertest | 开发人员 |
| 文档一致性测试 | 验证代码与文档同步 | 自定义工具 | 文档维护者 |
| 端到端测试 | 验证完整流程 | Playwright, Cypress | QA团队 |
| 性能测试 | 确保系统性能符合要求 | Locust, k6 | 性能工程师 |

## 2. 测试环境设置

### 2.1 本地测试环境

```bash
# Python项目
# 安装测试依赖
pip install pytest pytest-cov pytest-mock

# JavaScript项目
# 安装测试依赖
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
```

### 2.2 CI/CD 测试环境

VibeCopilot 使用 GitHub Actions 进行持续集成测试：

- `.github/workflows/test.yml` - 运行单元测试和集成测试
- `.github/workflows/docs.yml` - 验证文档一致性
- `.github/workflows/e2e.yml` - 运行端到端测试

### 2.3 测试数据管理

- 使用工厂模式创建测试数据
- 避免在测试中使用硬编码的数据
- 使用 fixtures 提供可重用的测试环境
- 所有敏感测试数据应从环境变量获取

## 3. 单元测试

### 3.1 单元测试标准

- 测试覆盖率目标：80%+ (关键模块 90%+)
- 每个公共函数/方法应有测试
- 测试应该独立且可并行运行
- 使用 Mock/Stub 隔离外部依赖

### 3.2 Python 单元测试示例

```python
# tests/test_document_generator.py
import pytest
from vibecopilot.generators import DocumentGenerator

def test_generate_prd_template():
    """测试PRD模板生成功能"""
    generator = DocumentGenerator()
    template = generator.generate_prd_template("Test Project")

    # 验证结果
    assert "# Test Project - 产品需求文档" in template
    assert "## 1. 项目背景与目标" in template
    assert "## 2. 用户画像与用户故事" in template
```

### 3.3 JavaScript 单元测试示例

```javascript
// tests/documentRenderer.test.js
import { render } from '@testing-library/react';
import DocumentRenderer from '../src/components/DocumentRenderer';

test('renders markdown document correctly', () => {
  const markdown = '# Test Heading\n\nTest paragraph';
  const { getByText } = render(<DocumentRenderer content={markdown} />);

  expect(getByText('Test Heading')).toBeInTheDocument();
  expect(getByText('Test paragraph')).toBeInTheDocument();
});
```

### 3.4 运行单元测试

```bash
# Python
pytest -v tests/unit/

# JavaScript
npm test -- --testPathPattern=unit
```

## 4. 集成测试

### 4.1 集成测试标准

- 验证模块间交互
- 测试数据流和状态传递
- 验证API接口行为
- 测试数据库交互

### 4.2 接口集成测试示例

```python
# tests/integration/test_github_integration.py
import pytest
from vibecopilot.integrations import GitHubIntegration

@pytest.mark.integration
def test_sync_issues_with_documents():
    """测试GitHub Issues与文档同步功能"""
    # 设置测试环境
    github = GitHubIntegration(
        repo="test-repo",
        token=os.environ.get("TEST_GITHUB_TOKEN")
    )

    # 执行集成操作
    result = github.sync_issues_with_documents("docs/test")

    # 验证结果
    assert result.success == True
    assert len(result.synced_issues) > 0
```

### 4.3 运行集成测试

```bash
# Python
pytest -v tests/integration/

# JavaScript
npm test -- --testPathPattern=integration
```

## 5. 文档一致性测试

### 5.1 文档一致性检查

VibeCopilot 的核心功能是确保文档与代码一致，因此我们提供专门的一致性测试：

```python
# tests/consistency/test_doc_code_consistency.py
import pytest
from vibecopilot.validators import DocumentCodeConsistencyValidator

def test_api_doc_consistency():
    """测试API文档与实际代码的一致性"""
    validator = DocumentCodeConsistencyValidator()
    result = validator.validate("docs/api", "src/api")

    # 验证结果
    assert result.consistency_score >= 0.9  # 90%一致性
    assert len(result.inconsistencies) == 0
```

### 5.2 自动修复文档

```bash
# 运行文档自动修复工具
python -m vibecopilot.tools.doc_repair --source=src --docs=docs
```

## 6. 端到端测试

### 6.1 端到端测试策略

- 验证关键用户场景
- 模拟真实用户行为
- 测试整个系统流程

### 6.2 端到端测试示例 (Playwright)

```javascript
// tests/e2e/document-workflow.spec.js
const { test, expect } = require('@playwright/test');

test('complete document workflow', async ({ page }) => {
  // 打开应用
  await page.goto('http://localhost:3000');

  // 创建新文档
  await page.click('text=Create New Document');
  await page.selectOption('select[name="template"]', 'prd');
  await page.fill('input[name="projectName"]', 'Test Project');
  await page.click('text=Generate');

  // 验证文档已创建
  await expect(page.locator('h1')).toContainText('Test Project - 产品需求文档');

  // 编辑文档
  await page.click('text=Edit');
  await page.fill('.editor', '## Modified Section\n\nThis is a test.');
  await page.click('text=Save');

  // 验证更改已保存
  await expect(page.locator('h2')).toContainText('Modified Section');
});
```

### 6.3 运行端到端测试

```bash
# 启动测试服务器
npm run start:test

# 另一个终端中运行测试
npx playwright test
```

## 7. AI 辅助测试

VibeCopilot 利用 AI 工具辅助测试过程:

### 7.1 AI 测试案例生成

```bash
# 根据API规范生成测试案例
python -m vibecopilot.tools.ai_test_generator --source=docs/api/spec.yaml --output=tests/generated
```

### 7.2 AI 代码审查

利用 AI 进行代码审查的最佳实践:

1. 提供明确的代码上下文
2. 指定特定的审查重点 (安全、性能、可读性等)
3. 使用以下 Cursor AI 提示模板:

```
请审查以下代码，重点关注:
1. 潜在的错误和漏洞
2. 代码风格是否符合项目规范
3. 是否有性能优化空间
4. 测试覆盖是否充分

代码:
[插入代码]
```

## 8. 代码审查流程

### 8.1 代码审查清单

每次 PR 必须通过以下审查清单:

- [ ] 代码遵循项目规范
- [ ] 单元测试覆盖了新功能
- [ ] 文档已更新
- [ ] 所有自动化测试通过
- [ ] 代码中没有敏感信息
- [ ] 性能影响已评估
- [ ] 错误处理完善

### 8.2 代码审查工具

- GitHub Pull Request 审查功能
- SonarQube 代码质量分析
- Codecov 测试覆盖率报告

### 8.3 自动化审查集成

将静态代码分析工具集成到 CI/CD 流程:

```yaml
# .github/workflows/code-review.yml
name: Code Review

on:
  pull_request:
    branches: [ main, dev ]

jobs:
  code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run flake8
        run: flake8 src tests
      - name: Run mypy
        run: mypy src
```

## 9. 质量指标与监控

### 9.1 关键质量指标

VibeCopilot 项目跟踪以下质量指标:

- 代码测试覆盖率
- 文档完整性得分
- 文档与代码一致性得分
- 静态分析问题数量
- 平均 PR 解决时间

### 9.2 质量仪表盘

使用 GitHub 项目的 Insights 和自定义仪表盘跟踪质量指标:

```bash
# 生成质量报告
python -m vibecopilot.tools.quality_dashboard --output=reports/quality
```

## 10. 持续改进

### 10.1 测试回顾会议

- 每个迭代结束后进行测试回顾
- 识别测试过程中的问题和改进机会
- 更新测试策略和工具

### 10.2 质量改进计划

- 维护已知问题和技术债务列表
- 定期分配时间处理质量问题
- 持续优化测试自动化流程

## 11. 资源与参考

- [Pytest 文档](https://docs.pytest.org/.md)
- [Jest 文档](https://jestjs.io/docs/getting-started.md)
- [Playwright 文档](https://playwright.dev/docs/intro.md)
- [GitHub Actions 文档](https://docs.github.com/en/actions.md)

---

本文档提供了 VibeCopilot 项目测试与质量保障的整体框架。团队成员应遵循这些指南，确保项目质量和文档一致性。随着项目发展，本指南将持续更新以反映最佳实践。
