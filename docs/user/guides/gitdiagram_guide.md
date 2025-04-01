# GitDiagram 使用指南

## 简介

GitDiagram 是VibeCopilot集成的一个强大工具，可以将任何GitHub仓库或本地项目转换为交互式的系统架构图，帮助您快速理解项目结构和组件关系。通过可视化的方式展示代码库，使项目文档更加直观，也便于团队成员之间的沟通和协作。

## 功能特点

- **即时可视化**：快速将任何仓库转换为系统设计/架构图
- **交互式组件**：点击组件可直接导航到源文件和相关目录
- **自定义图表**：通过自定义指令修改和重新生成图表
- **支持私有仓库**：通过GitHub Token访问私有仓库

## 使用方法

### 1. 基本使用

VibeCopilot提供了一个简便的Python脚本来生成项目结构图：

```bash
python scripts/utils/generate_diagram.py <仓库URL或本地路径> [选项]
```

#### 参数说明

- `<仓库URL或本地路径>`：指定要生成图表的GitHub仓库URL或本地项目路径
- `--setup`：首次使用时初始化GitDiagram环境
- `--start-backend`：启动GitDiagram后端服务
- `-o, --output`：指定输出文件路径

### 2. 首次使用

首次使用GitDiagram需要进行环境设置：

```bash
# 设置环境并生成当前项目的结构图
python scripts/utils/generate_diagram.py . --setup
```

这个命令会自动：

1. 为GitDiagram安装必要的依赖
2. 创建环境配置文件
3. 生成当前项目的结构图

### 3. 生成GitHub仓库图表

您可以直接生成任何GitHub仓库的结构图：

```bash
# 生成指定GitHub仓库的结构图
python scripts/utils/generate_diagram.py https://github.com/username/repo --start-backend
```

### 4. 使用Web界面

GitDiagram本质上是一个Web应用，提供了更丰富的交互功能：

1. 启动后端服务：
   ```bash
   cd modules/gitdiagram
   docker-compose up -d
   ```

2. 启动前端服务：
   ```bash
   cd modules/gitdiagram
   pnpm dev
   ```

3. 访问 `http://localhost:3000` 使用Web界面

### 5. 快捷URL

在任何GitHub仓库URL中，您可以将 `hub` 替换为 `diagram` 直接访问该仓库的图表：

原始URL：`https://github.com/username/repo`
图表URL：`https://gitdiagram.com/username/repo`

## 高级功能

### 自定义图表

通过Web界面，您可以：

- 添加自定义注释
- 调整组件布局
- 过滤特定文件或目录
- 重新生成具有特定焦点的图表

### 私有仓库访问

要访问私有仓库，您需要：

1. 创建具有 `repo` 权限的GitHub个人访问令牌
2. 在Web界面中选择"私有仓库"选项并提供令牌

## 故障排除

### 常见问题

1. **后端服务无法启动**
   - 确保已安装Docker和Docker Compose
   - 检查端口8000是否已被占用

2. **前端服务无法访问**
   - 确保后端服务已启动
   - 检查端口3000是否已被占用

3. **图表生成失败**
   - 检查仓库URL是否正确
   - 确保有足够的权限访问该仓库

### 获取帮助

如果您遇到任何问题，可以：

- 查看原始项目文档：[GitDiagram README](https://github.com/jacobcy/gitdiagram/blob/main/README.md)
- 在GitHub Issues中提出问题

## 实践案例

### 案例1：项目文档生成

将GitDiagram生成的架构图整合到项目文档中，提供系统概览：

```markdown
# 系统架构

以下是我们项目的系统架构图：

![系统架构图](./images/system_diagram.png)

该图由GitDiagram自动生成，展示了主要组件及其关系。
```

### 案例2：新团队成员引导

为新加入的团队成员提供项目结构快速了解：

1. 生成当前项目的架构图
2. 将图表作为入职文档的一部分
3. 通过交互式图表引导他们了解关键组件
