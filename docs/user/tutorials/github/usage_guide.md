# GitHub 项目管理工具使用指南

这份指南将帮助你掌握 VibeCopilot GitHub 项目管理工具的日常使用方法。

## 📋 日常任务管理

### 创建新任务

#### 方式一：通过网页界面（推荐）

1. 打开项目面板
2. 点击 "+" 按钮
3. 填写任务信息：
   - 标题：简短描述任务内容
   - 描述：详细说明任务要求
   - 标签：选择合适的标签
   - 优先级：设置任务优先级

#### 方式二：使用命令行

```bash
# 使用Python模块而非脚本
python -m src.github.issues.add_issue \
  --owner <用户名> \
  --repo <仓库名> \
  --title "实现登录功能" \
  --body "添加用户登录和认证功能" \
  --labels "priority:high,type:feature"
```

### 更新任务状态

#### 方式一：拖拽操作（推荐）

在看板视图中，直接拖拽任务卡片到对应状态列。

#### 方式二：使用命令行

```bash
python -m src.github.issues.update_issue \
  --owner <用户名> \
  --repo <仓库名> \
  --issue-number 123 \
  --state "closed" \
  --labels "status:completed"
```

### 添加任务评论

1. 点击任务卡片
2. 在评论框中输入更新信息
3. 使用特殊标记增加可读性：
   - 📝 更新内容
   - ❌ 遇到的问题
   - ✅ 已解决的问题

## 📊 项目视图使用

### 看板视图（任务管理）

- 查看任务状态分布
- 拖拽卡片更新状态
- 快速添加新任务

### 表格视图（详细信息）

- 查看所有任务的详细信息
- 批量编辑任务
- 自定义显示字段

### 时间线视图（进度跟踪）

- 查看项目时间线
- 跟踪里程碑进度
- 预览即将到期的任务

## 🏷️ 使用标签系统

### 常用标签

- 🔴 `priority:high`: 高优先级任务
- 🟡 `priority:medium`: 中优先级任务
- 🟢 `priority:low`: 低优先级任务
- 🐛 `type:bug`: 问题修复
- ✨ `type:feature`: 新功能
- 📚 `type:docs`: 文档相关

### 标签使用技巧

1. 组合使用标签，如 `type:bug` + `priority:high`
2. 根据需要创建自定义标签
3. 保持标签系统简洁明了

## 📈 生成报告

### 路线图进度报告

```bash
python -m src.github.projects.main generate \
  --owner <用户名> \
  --repo <仓库名> \
  --project-number 1 \
  --markdown \
  --output-dir ./reports
```

### 统计报告

```bash
python -m src.github.projects.roadmap_generator \
  --owner <用户名> \
  --repo <仓库名> \
  --project-number 1 \
  --format markdown \
  --output ./reports/stats.md
```

## 🔄 数据同步

### 导出项目数据

```bash
python -m src.github.projects.main export \
  --owner <用户名> \
  --repo <仓库名> \
  --project-number 1 \
  --format json \
  --output project_backup.json
```

### 导入项目数据

```bash
python -m src.github.projects.main import \
  --owner <用户名> \
  --repo <仓库名> \
  --file project_backup.json
```

## 📱 移动端使用

1. 下载 GitHub 移动应用
2. 登录你的账号
3. 访问项目面板
4. 执行基本操作：
   - 查看任务
   - 更新状态
   - 添加评论

## 💡 使用技巧

1. **快捷键**
   - `n`: 新建任务
   - `c`: 创建评论
   - `/`: 搜索

2. **任务描述模板**
   ```markdown
   ## 目标
   [简要描述任务目标]

   ## 具体要求
   - [ ] 要求1
   - [ ] 要求2

   ## 相关资源
   - [相关文档]
   - [设计稿]
   ```

3. **高效协作**
   - 使用 @提及 通知团队成员
   - 关联相关任务 (#任务编号)
   - 使用任务清单跟踪子任务

## 🆘 常见操作问题

1. **任务无法移动？**
   - 检查你的权限设置
   - 确认任务未被锁定

2. **找不到特定任务？**
   - 使用搜索功能
   - 检查筛选器设置

3. **报告生成失败？**
   - 验证数据访问权限
   - 检查命令参数
   - 确保设置了正确的GITHUB_TOKEN环境变量

需要更多帮助？请查看我们的[详细文档](../../../index.md)或[联系支持](mailto:support@vibecopilot.com.md)。
