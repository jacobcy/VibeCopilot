# VibeCopilot 路线图同步指南

本指南介绍了如何使用 VibeCopilot 的同步功能来导入、导出以及与外部系统（如 GitHub）同步路线图数据。

## 核心概念

- **YAML 同步**: 支持将路线图数据从 YAML 文件导入到系统数据库，或将系统中的路线图导出为 YAML 文件。导入过程中包含数据格式验证。
- **GitHub 同步**: 支持将系统中的路线图数据（包括 Epics, Stories, Tasks, Milestones）与关联的 GitHub Project 和 Issues 进行双向同步。

## 准备工作

### 1. 环境变量配置 (GitHub 同步)

若要使用 GitHub 同步功能，请在项目根目录的 `.env` 文件中配置以下环境变量：

```bash
# GitHub 认证与仓库配置
GITHUB_TOKEN=your_github_personal_access_token  # 需要 repo 和 project 权限
GITHUB_OWNER=your_github_username_or_organization
GITHUB_REPO=your_repository_name

# 可选：启用模拟模式以进行测试，避免真实 API 调用
# MOCK_SYNC=true
```
*参考： [`roadmap_github_sync.md`](../../examples/roadmap_sync/roadmap_github_sync.md) 获取更详细的 GitHub 配置和权限说明。*

### 2. 路线图 YAML 文件

- 路线图数据可以存储在 YAML 文件中。
- 系统提供了一个标准模板：[`templates/roadmap/standard_roadmap_template.yaml`](../../templates/roadmap/standard_roadmap_template.yaml)。
- 导入时，系统会验证 YAML 文件的格式和内容。

## 使用说明 (命令行)

*注意：以下命令为示例，请根据实际的 CLI 实现 (`src/cli/commands/roadmap/roadmap_click.py`) 进行调整。*

### 1. YAML 导入与验证

将本地 YAML 文件导入（或更新）到系统数据库。导入过程会自动进行验证。

```bash
# 导入新的路线图 (系统会自动生成或要求提供 roadmap_id)
vibecopilot roadmap import --source path/to/your_roadmap.yaml

# 更新现有路线图 (指定 roadmap_id)
vibecopilot roadmap import --source path/to/your_roadmap.yaml --roadmap existing-roadmap-id

# (可选) 单独验证 YAML 文件 (如果 CLI 支持此命令)
# vibecopilot roadmap validate --source path/to/your_roadmap.yaml
```
*如果导入失败，请检查错误信息，通常与 YAML 格式或必填字段有关。*

### 2. YAML 导出

将系统中的路线图导出为 YAML 文件。

```bash
# 导出当前活动路线图
vibecopilot roadmap export --output path/to/export.yaml

# 导出指定路线图
vibecopilot roadmap export --roadmap specific-roadmap-id --output path/to/export.yaml
```

### 3. GitHub 同步

*前提：已通过 YAML 导入路线图，并且在 `.env` 中正确配置了 GitHub 参数。路线图需要关联到 GitHub Project (通常在创建或同步时处理，具体机制参考 `RoadmapService` 或 GitHub 同步文档)。*

```bash
# 将本地路线图数据推送到 GitHub (创建或更新 Project Items/Issues)
# 需要指定要同步的本地 roadmap_id
vibecopilot roadmap sync --github --roadmap <local_roadmap_id> --direction push

# 从关联的 GitHub Project 拉取状态更新到本地路线图
# 需要指定要同步的本地 roadmap_id
vibecopilot roadmap sync --github --roadmap <local_roadmap_id> --direction pull

# (可能存在的简化命令，具体参考 CLI 实现)
# vibecopilot roadmap sync --github # 自动同步活动路线图
```
*详细的 GitHub 同步逻辑、数据映射和错误处理，请参考 [`roadmap_github_sync.md`](../../examples/roadmap_sync/roadmap_github_sync.md)。*

### 4. 切换活动路线图

切换 CLI 和其他服务默认操作的路线图。

```bash
# 查看可用路线图
vibecopilot roadmap list

# 切换活动路线图
vibecopilot roadmap switch <roadmap_id>

# 查看当前活动路线图状态
vibecopilot roadmap status
# 或
# vibecopilot status roadmap
```

## 使用说明 (Python API)

可以通过 `RoadmapService` 在代码中执行同步操作。

```python
from src.roadmap import RoadmapService

# 获取服务实例
service = RoadmapService()
active_roadmap_id = service.get_active_roadmap_id() # 获取当前活动路线图ID

# YAML 导入 (内置验证)
try:
    result = service.import_from_yaml("path/to/your_roadmap.yaml", roadmap_id=active_roadmap_id)
    if result.get("success"):
        print("YAML 导入成功")
    else:
        print(f"YAML 导入失败: {result.get('error')}")
        # result 可能包含更详细的验证错误信息
except FileNotFoundError:
    print("错误: YAML 文件未找到")
except Exception as e:
    print(f"导入时发生错误: {e}")


# YAML 导出
try:
    success = service.export_to_yaml(active_roadmap_id, "path/to/export.yaml")
    if success:
        print("YAML 导出成功")
    else:
        print("YAML 导出失败")
except Exception as e:
    print(f"导出时发生错误: {e}")


# GitHub 同步 (确保环境变量已设置)
# 推送
try:
    push_result = service.sync_to_github(active_roadmap_id)
    if push_result.get("success"):
        print("成功推送到 GitHub")
    else:
        print(f"推送到 GitHub 失败: {push_result.get('error')}")

    # 拉取状态
    pull_result = service.sync_from_github(active_roadmap_id)
    if pull_result.get("success"):
        print("成功从 GitHub 拉取状态")
    else:
        print(f"从 GitHub 拉取状态失败: {pull_result.get('error')}")
except Exception as e:
    print(f"GitHub 同步时发生错误: {e}")

```

## 故障排除

### 1. YAML 验证失败

- **检查错误**: 仔细阅读 `import_from_yaml` 或 CLI 命令返回的错误信息。
- **参考模板**: 对照 [`templates/roadmap/standard_roadmap_template.yaml`](../../templates/roadmap/standard_roadmap_template.yaml) 检查格式、必填字段、状态/优先级枚举值等。
- **简化测试**: 尝试导入一个仅包含基本字段（如 `title`, `description`）的最小化 YAML 文件。

### 2. GitHub 同步失败

- **检查配置**: 确认 `.env` 文件中的 `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO` 是否正确无误。
- **检查权限**: 确保 `GITHUB_TOKEN` 具有访问仓库和项目的必要权限 (repo, project)。
- **检查关联**: 确认要同步的 `roadmap_id` 是否已正确关联到 GitHub Project ID（这通常在首次同步或通过特定服务方法设置）。参考 [`roadmap_github_sync.md`](../../examples/roadmap_sync/roadmap_github_sync.md)。
- **网络问题**: 检查网络连接是否能访问 GitHub API。
- **模拟模式**: 暂时启用模拟模式 (`MOCK_SYNC=true`) 看是否能模拟成功，以排除 API 调用本身的问题。

### 3. 数据库错误

- **检查初始化**: 确保数据库已通过 `vibecopilot db init` 初始化。
- **检查 `roadmap_id`**: 确认操作的 `roadmap_id` 在数据库中确实存在。

## 最佳实践

- **版本控制**: 将路线图 YAML 文件纳入 Git 版本控制。
- **定期同步**: 定期执行 GitHub 同步（推+拉）以保持数据一致性。
- **验证优先**: 在进行大规模导入或修改前，先验证 YAML 文件格式。
- **明确关联**: 确保本地 Roadmap 与 GitHub Project 的关联是明确和正确的。

## 参考资料

- **路线图模块**: [`src/roadmap/README.md`](./README.md)
- **GitHub 同步细节**: [`examples/roadmap_sync/roadmap_github_sync.md`](../../examples/roadmap_sync/roadmap_github_sync.md)
- **标准模板**: [`templates/roadmap/standard_roadmap_template.yaml`](../../templates/roadmap/standard_roadmap_template.yaml)
- **YAML 验证器 (内部实现)**: `src/roadmap/sync/yaml.py` (可能包含 `RoadmapYamlValidator` 类)
