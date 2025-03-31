# VibeCopilot 快速入门指南

## 欢迎使用 VibeCopilot

VibeCopilot 是一个智能项目管理助手，旨在帮助开发者遵循规范化的开发流程，提高项目质量和开发效率。本指南将帮助您快速上手并充分利用 VibeCopilot 的功能。

## 1. 环境准备

### 基本要求

- Python 3.8+
- Git
- 支持的IDE: Cursor (推荐)、VS Code 或 其他支持 Copilot 的编辑器

### 安装步骤

1. **克隆仓库:**
   ```bash
   git clone https://github.com/yourusername/VibeCopilot.git
   cd VibeCopilot
   ```

2. **创建虚拟环境:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # 或
   .venv\Scripts\activate     # Windows
   ```

3. **安装依赖:**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量:**
   复制 `.env.example` 文件为 `.env` 并填写必要的配置项，如:
   ```
   GITHUB_TOKEN=your_github_token
   ```

## 2. 项目结构

VibeCopilot 采用标准化的目录结构，详细说明可在 `docs/ai/rules/project_structure.md` 文件中找到。主要目录包括:

- `/docs` - 项目文档，分为AI文档和人类文档
- `/scripts` - 工具脚本，用于自动化任务
- `/tools` - 工具使用指南
- `/templates` - 项目模板
- `/src` - 源代码(开发中)

## 3. 使用流程

### 第一步：初始化项目

运行初始化脚本来设置新项目:

```bash
python scripts/setup/init_project.py --name "MyProject" --template python
```

这将创建一个新的项目目录，并生成所有必要的文档和配置文件。

### 第二步：规划项目

1. 编辑 `docs/project/requirements/prd.md` 文件，定义项目需求
2. 使用 GitHub Projects 创建路线图:
   ```bash
   python scripts/github/create_project.py --name "MyProject Roadmap"
   ```

### 第三步：开发

遵循 `docs/ai/rules` 中的开发规范，利用 Cursor 和 AI 辅助工具进行开发:

1. 先阅读规划文档
2. 按功能点逐个实现
3. 提交代码时遵循 Commit 规范
4. 使用 GitHub Projects 跟踪进度

## 4. 常用命令

```bash
# 更新路线图
python scripts/github/update_roadmap.py

# 创建新功能分支
python scripts/github/create_feature_branch.py --name "feature-name"

# 检查文档同步状态
python scripts/project/check_docs_sync.py

# 生成开发进度报告
python scripts/project/generate_report.py
```

## 5. 最佳实践

- **定期更新文档**: 代码变更后及时更新相关文档
- **遵循开发流程**: 按照规划→设计→开发→测试→部署的流程进行
- **充分利用AI**: 善用Cursor和OpenAI API，但始终审核AI生成的代码
- **保持小步提交**: 频繁提交小的、功能完整的变更
- **先写测试**: 采用测试驱动开发(TDD)方法

## 6. 故障排除

常见问题及解决方案:

1. **GitHub API错误**: 检查您的GITHUB_TOKEN是否有效且具有足够权限
2. **依赖冲突**: 尝试使用`pip install -r requirements.txt --upgrade`更新依赖
3. **路径错误**: 确保在项目根目录下运行脚本

## 7. 获取帮助

- 查阅 `docs/human/tutorials` 目录下的详细教程
- 在GitHub Issues中提问
- 查看 `docs/human/references` 下的参考资料

---

通过遵循这个指南，您将能够快速上手并充分利用VibeCopilot的功能，提高您的开发效率和项目质量。
