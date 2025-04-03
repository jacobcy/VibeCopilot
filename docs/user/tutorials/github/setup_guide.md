# 项目初始化指南

本指南将帮助你从零开始设置 GitHub 项目管理环境。跟随以下步骤，你就能快速开始使用我们的工具。

## 📋 准备工作

### 1. GitHub 账号设置

- 注册 GitHub 账号（如果还没有）
- 确保你有仓库的管理权限

### 2. 安装必要工具

1. 安装 Python（3.8 或更高版本）
2. 安装 Git

### 3. 获取访问令牌

1. 访问 GitHub 设置页面
2. 点击"Developer settings" → "Personal access tokens" → "Generate new token"
3. 勾选以下权限：
   - `repo` - 完整的仓库访问权限
   - `admin:org` - 组织管理权限
   - `project` - 项目管理权限
4. 生成并保存令牌（请妥善保管！）

## 🚀 开始设置

### 1. 下载工具

```bash
# 克隆仓库
git clone https://github.com/VibeCopilot/VibeCopilot.git
cd VibeCopilot

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境

创建 `.env` 文件并添加你的 GitHub 令牌：

```bash
GITHUB_TOKEN=your_token_here
GITHUB_OWNER=your_username
GITHUB_REPO=your_repository
```

### 3. 创建项目

#### 方式一：使用图形界面（推荐新手使用）

1. 访问你的 GitHub 仓库
2. 点击顶部的 "Projects" 标签
3. 点击 "New project"
4. 选择 "Board" 模板
5. 填写项目名称和描述

#### 方式二：使用命令行

```bash
# 使用我们的API客户端创建项目
python -m src.github.projects.main create \
  --owner <用户名> \
  --repo <仓库名> \
  --title "我的第一个项目" \
  --description "这是项目描述"
```

## 📝 初始化项目内容

### 1. 导入路线图（可选）

如果你已经有现成的路线图文件：

```bash
python -m src.github.projects.main import \
  --owner <用户名> \
  --repo <仓库名> \
  --file path/to/roadmap.yaml \
```

支持的格式包括：

- YAML格式 (.yaml, .yml)
- Markdown格式 (.md, .markdown)

### 2. 设置项目视图

1. 在项目页面点击 "Views"
2. 添加以下视图：
   - 📋 看板视图（任务管理）
   - 📊 表格视图（详细信息）
   - 📅 时间线视图（进度跟踪）

### 3. 配置工作流程

1. 添加状态列：
   - 待处理 (Todo)
   - 进行中 (In Progress)
   - 已完成 (Done)

2. 设置标签：
系统会自动创建以下标签：
   - 里程碑标签：`milestone:M1`, `milestone:M2`等
   - 优先级标签：`priority:high`, `priority:medium`, `priority:low`
   - 状态标签：`status:todo`, `status:in-progress`, `status:completed`
   - 类型标签：`type:feature`, `type:bug`, `type:docs`等

## ✅ 验证设置

运行测试命令确认一切正常：

```bash
python -m src.github.api.github_client
```

如果配置正确，将显示当前登录用户信息。

## 🎉 下一步

恭喜！你已经完成了项目的初始化设置。现在你可以：

1. [查看使用指南](usage_guide.md) 学习如何使用各项功能
2. 开始添加你的第一个任务
3. 邀请团队成员加入项目

## 💡 常见问题

1. **令牌不工作？**
   - 检查令牌权限是否正确
   - 确认令牌未过期
   - 验证环境变量是否正确设置

2. **找不到项目？**
   - 确认项目可见性设置
   - 检查你的访问权限
   - 使用正确的项目编号

3. **导入失败？**
   - 验证文件格式是否正确
   - 检查文件路径是否正确
   - 查看详细错误消息

需要更多帮助？欢迎查看我们的[常见问题解答](../faq.md)或[联系支持团队](mailto:support@vibecopilot.com.md)。
