# GitHub Projects 开发者指南

本指南面向开发团队，详细说明如何在开发过程中高效使用 GitHub Projects 进行项目管理。

## 开发工作流集成

### 分支管理策略

1. **分支命名规范**
   ```bash
   feature/ISSUE-123-short-description  # 新功能
   bugfix/ISSUE-456-bug-description    # 问题修复
   hotfix/ISSUE-789-critical-fix       # 紧急修复
   docs/ISSUE-012-documentation        # 文档更新
   ```

2. **分支工作流**
   ```mermaid
   graph TD
   A[主分支 main] --> B[功能分支 feature/*]
   A --> C[修复分支 bugfix/*]
   B --> D[Pull Request]
   C --> D
   D --> A
   ```

### 自动化工作流

1. **Issue 模板配置**
   ```yaml
   name: Feature Request
   about: 新功能请求模板
   title: "[Feature] "
   labels: ["type:feature", "status:triage"]
   assignees: ""
   ```

2. **PR 模板设置**
   ```markdown
   ## 相关 Issue
   - Fixes #123

   ## 修改内容
   - [ ] 功能实现
   - [ ] 单元测试
   - [ ] 文档更新

   ## 测试说明
   1. 测试步骤 1
   2. 测试步骤 2
   ```

### CI/CD 集成

```yaml
name: Project Automation
on:
  issues:
    types: [opened, closed, reopened]
  pull_request:
    types: [opened, closed, reopened]

jobs:
  update_project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v6
      # 自动化步骤配置
```

## GitHub API 使用

### 1. API 基类使用

```python
from src.github.api import GitHubClient

# 创建基础客户端
client = GitHubClient()

# GraphQL 查询
query = """
query {
  viewer {
    login
    name
  }
}
"""
data = client.graphql(query)
print(f"当前用户: {data['data']['viewer']['name']}")

# REST API 请求
repo_data = client.get("repos/owner/repo")
print(f"仓库星标数: {repo_data['stargazers_count']}")
```

### 2. Issues API 使用

```python
from src.github.api import GitHubIssuesClient

# 创建Issues客户端
issues_client = GitHubIssuesClient()

# 获取问题列表
issues = issues_client.get_issues(
    owner="用户名",
    repo="仓库名",
    state="open",
    labels="priority:high"
)

# 创建新问题
new_issue = issues_client.create_issue(
    owner="用户名",
    repo="仓库名",
    title="新功能请求",
    body="详细描述",
    labels=["type:feature", "priority:medium"]
)

# 更新问题
updated_issue = issues_client.update_issue(
    owner="用户名",
    repo="仓库名",
    issue_number=123,
    state="closed"
)
```

### 3. Projects API 使用

```python
from src.github.api import GitHubProjectsClient

# 创建Projects客户端
projects_client = GitHubProjectsClient()

# 获取项目数据
project_data = projects_client.get_project_v2(
    owner="用户名",
    repo="仓库名",
    project_number=1
)

# 获取项目字段
fields = projects_client.get_project_fields(
    owner="用户名",
    repo="仓库名",
    project_number=1
)

# 添加问题到项目
projects_client.add_issue_to_project(
    owner="用户名",
    repo="仓库名",
    project_id="项目ID",
    issue_id="问题ID"
)
```

## 自定义视图和报告

### 处理路线图数据

```python
from src.github.projects.roadmap_processor import RoadmapProcessor
from src.github.api import GitHubProjectsClient

# 初始化
client = GitHubProjectsClient()
processor = RoadmapProcessor(client)

# 获取和处理项目数据
project_data = client.get_project_v2("用户名", "仓库名", 1)
roadmap_data = processor.process_roadmap_data(project_data)

# 使用处理后的数据
print(f"项目标题: {roadmap_data['title']}")
for task in roadmap_data['tasks']:
    print(f"- {task['title']} ({task['status']})")
```

### 生成路线图报告

```python
from src.github.projects.roadmap_generator import RoadmapGenerator

# 初始化生成器
generator = RoadmapGenerator(
    owner="用户名",
    repo="仓库名",
    project_number=1,
    output_dir="./reports"
)

# 生成多种格式的报告
results = generator.generate(formats=["json", "markdown", "html"])
print(f"报告已生成: {results}")
```

## 最佳实践和规范

### 1. Issue 管理规范

- **标题格式**：`[类型] 简短描述`
- **描述模板**：
  ```markdown
  ## 背景
  [问题/需求背景]

  ## 目标
  [预期达到的效果]

  ## 验收标准
  - [ ] 标准1
  - [ ] 标准2

  ## 技术方案
  [实现思路和方案]
  ```

### 2. PR 审核清单

- [ ] 代码符合项目规范
- [ ] 包含必要的测试
- [ ] 文档已更新
- [ ] 无安全隐患
- [ ] CI 检查通过
- [ ] 性能影响可接受

### 3. 项目看板使用规范

1. **任务卡片要素**
   - 明确的标题
   - 合适的标签
   - 负责人指派
   - 截止日期设置
   - 优先级标记

2. **状态列定义**
   - Backlog: 未规划任务
   - Todo: 已规划待开发
   - In Progress: 开发中
   - Review: 代码审核中
   - Done: 已完成部署

## 故障排除和调试

### 1. API 限制处理

```python
from src.github.api import GitHubClient
import time

client = GitHubClient()

def handle_rate_limit():
    """处理API速率限制"""
    try:
        # 获取当前速率限制状态
        rate_limit = client.get("rate_limit")
        remaining = rate_limit["resources"]["core"]["remaining"]

        if remaining < 10:
            reset_time = rate_limit["resources"]["core"]["reset"]
            current_time = time.time()
            sleep_time = max(0, reset_time - current_time) + 5

            print(f"API请求即将达到限制，等待 {sleep_time} 秒后重试")
            time.sleep(sleep_time)

        return True
    except Exception as e:
        print(f"检查速率限制失败: {e}")
        return False
```

### 2. 常见问题解决

#### 身份验证问题

```python
from src.github.api import GitHubClient

def verify_authentication():
    """验证GitHub令牌权限"""
    client = GitHubClient()
    try:
        user = client.get("user")
        print(f"认证成功: {user['login']}")

        scopes = client._make_rest_request("GET", "").headers.get("X-OAuth-Scopes")
        print(f"令牌权限: {scopes}")

        return True
    except Exception as e:
        print(f"认证失败: {e}")
        return False
```

#### 项目数据同步问题

```python
from src.github.projects.import_roadmap import RoadmapImporter

def repair_project_data(owner, repo, project_number):
    """修复项目数据问题"""
    importer = RoadmapImporter(owner, repo)

    # 1. 备份当前数据
    backup_path = f"backup_{owner}_{repo}_{project_number}.yaml"
    importer.export_data(project_number, backup_path)
    print(f"数据已备份到: {backup_path}")

    # 2. 验证数据结构
    success = importer.validate_project_data(project_number)
    if not success:
        print("数据结构验证失败，请考虑从备份恢复")

    return success
```

## 扩展和定制

### 1. 自定义字段配置

```graphql
mutation {
    createProjectV2Field(
        input: {
            projectId: "PROJECT_ID"
            dataType: SINGLE_SELECT
            name: "Priority"
            options: ["P0", "P1", "P2", "P3"]
        }
    ) {
        projectV2Field {
            id
        }
    }
}
```

### 2. 自动化规则示例

```yaml
name: Auto Label
on:
  issues:
    types: [opened]
jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v6
        with:
          script: |
            const issue = context.payload.issue;
            if (issue.title.includes('[Bug]')) {
              github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                labels: ['bug', 'triage']
              });
            }
```

## 性能优化建议

1. **批量操作**
   ```python
   def batch_update_items(items, updates):
       """批量更新项目条目"""
       with ThreadPoolExecutor(max_workers=5) as executor:
           futures = [
               executor.submit(update_item, item, update)
               for item, update in zip(items, updates)
           ]
       return [f.result() for f in futures]
   ```

2. **缓存策略**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def get_project_item(item_id):
       """获取项目条目（带缓存）"""
       return fetch_item_from_api(item_id)
   ```

## 资源和参考

- [GitHub Projects API 文档](https://docs.github.com/en/rest/reference/projects)
- [GitHub GraphQL API 文档](https://docs.github.com/en/graphql)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [项目最佳实践指南](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects)

---

通过本指南和VibeCopilot提供的工具，您可以高效地使用GitHub Projects管理开发过程，确保项目按计划有序进行。
