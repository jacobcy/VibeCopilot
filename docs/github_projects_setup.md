# GitHub Projects 路线图设置指南

本指南详细说明如何将VibeCopilot的路线图数据导入到GitHub Projects中，建立一个动态可视化的项目管理系统。

## 准备工作

### 1. 创建GitHub个人访问令牌

1. 登录GitHub账户，点击右上角头像，选择"Settings"
2. 左侧菜单栏选择"Developer settings"
3. 选择"Personal access tokens" → "Tokens (classic)"或"Fine-grained tokens"
4. 点击"Generate new token"
5. 为令牌填写说明，如"VibeCopilot Roadmap Import"
6. 如果使用classic token，选择以下权限：
   - `repo` (完整访问权限)
   - `admin:org` (仅projects权限)
   - `project` (完整访问权限)
7. 如果使用fine-grained token，选择：
   - Repositories access：选择VibeCopilot仓库
   - Repository permissions：
     - Issues: Read and write
     - Projects: Read and write
   - Organization permissions：
     - Projects: Read and write
8. 设置合适的过期时间
9. 点击"Generate token"并妥善保存生成的令牌

### 2. 安装依赖

确保已安装必要的Python依赖：

```bash
pip install pyyaml requests
```

## 导入路线图数据

### 方法1：使用导入脚本

我们提供了一个Python脚本，可以自动将本地路线图数据导入到GitHub：

```bash
# 导出GitHub令牌到环境变量
export GITHUB_TOKEN="your-token-here"

# 运行导入脚本
python scripts/import_roadmap_to_github.py \
  --owner jacobcy \
  --repo VibeCopilot \
  --file data/roadmap.yaml \
  --create-project \
  --project-title "VibeCopilot Roadmap"
```

脚本将执行以下操作：
1. 创建所有必要的标签
2. 创建路线图中定义的里程碑
3. 为每个任务创建对应的Issues
4. 创建GitHub Project并设置自定义字段
5. 将所有Issues添加到Project中

### 方法2：手动设置GitHub Projects

如果您更喜欢手动设置，或者脚本遇到了问题，可以按照以下步骤操作：

#### 1. 创建标准标签

在GitHub仓库中创建以下标签：

**里程碑标签**：
- `milestone:M1` (#C5DEF5) - 准备阶段
- `milestone:M2` (#C5DEF5) - 核心功能开发阶段
- `milestone:M3` (#C5DEF5) - 功能扩展阶段
- `milestone:M4` (#C5DEF5) - 集成与测试阶段
- `milestone:M5` (#C5DEF5) - 发布与迭代阶段

**优先级标签**：
- `priority:critical` (#B60205) - 最高优先级 (P0)
- `priority:high` (#D93F0B) - 高优先级 (P1)
- `priority:medium` (#FBCA04) - 中优先级 (P2)
- `priority:low` (#0E8A16) - 低优先级 (P3)

**状态标签**：
- `status:planned` (#BFD4F2) - 计划中
- `status:todo` (#D4C5F9) - 待办
- `status:in-progress` (#FEF2C0) - 进行中
- `status:completed` (#C2E0C6) - 已完成

**类型标签**：
- `type:feature` (#006B75) - 新功能
- `type:bug` (#EE0701) - 缺陷
- `type:docs` (#1D76DB) - 文档
- `type:enhancement` (#5319E7) - 改进

#### 2. 创建里程碑

在GitHub仓库中创建以下里程碑：

1. **M1: 准备阶段**
   - 描述：完成项目基础规划、架构设计和开发环境搭建
   - 截止日期：2023-12-15
   - 状态：Closed

2. **M2: 核心功能开发阶段**
   - 描述：实现系统核心功能模块，建立基础架构
   - 截止日期：2024-03-01
   - 状态：Open

3. **M3: 功能扩展阶段**
   - 描述：在核心功能基础上扩展更多高级特性和用户界面
   - 截止日期：2024-05-15
   - 状态：Open

4. **M4: 集成与测试阶段**
   - 描述：确保系统各组件协同工作并满足质量要求
   - 截止日期：2024-07-15
   - 状态：Open

5. **M5: 发布与迭代阶段**
   - 描述：正式发布产品并持续优化
   - 截止日期：2024-08-15
   - 状态：Open

#### 3. 创建Project

1. 在GitHub仓库页面点击"Projects"选项卡
2. 点击"New project"，选择"Table"模板
3. 输入项目名称"VibeCopilot Roadmap"
4. 添加自定义字段：
   - 点击"+"按钮，选择"Single select"
   - 创建"里程碑"字段，选项为M1-M5
   - 创建"优先级"字段，选项为P0-P3
   - 创建"状态"字段，选项为"计划中"、"待办"、"进行中"、"已完成"

#### 4. 创建Issues并添加到Project

1. 参考`data/roadmap.yaml`中的任务数据，为每个任务创建对应的Issue
2. 为每个Issue添加适当的标签、里程碑和负责人
3. 在Issue页面，点击Projects侧边栏，将Issue添加到"VibeCopilot Roadmap"项目
4. 在Project视图中，为每个Issue设置自定义字段值

## 定制Project视图

导入数据后，您可以定制多种视图来浏览项目：

### 1. 看板视图

1. 点击"Views"下拉菜单，选择"New view" → "Board"
2. 选择按"状态"字段分组
3. 保存视图为"开发状态看板"

### 2. 路线图视图

1. 创建新视图，选择"Roadmap"
2. 设置按"里程碑"字段划分时间段
3. 保存视图为"开发路线图"

### 3. 任务优先级视图

1. 创建新视图，选择"Board"
2. 按"优先级"字段分组
3. 保存视图为"优先级看板"

## 使用GitHub Projects

成功设置后，您可以通过以下方式管理项目：

1. **查看项目状态**：使用不同视图浏览任务
2. **更新任务进度**：拖拽任务卡片或编辑状态字段
3. **按里程碑跟踪**：使用路线图视图查看整体进度
4. **筛选任务**：使用标签、里程碑、状态等筛选任务

## 与本地数据同步

为保持本地`data/roadmap.yaml`与GitHub Projects的同步，可以使用提供的脚本：

```bash
# 从GitHub获取最新项目数据并更新本地YAML
python scripts/github_projects.py -f json -s data/roadmap.json
```

这样可以保持GitHub上的在线管理与本地数据文件的一致性。