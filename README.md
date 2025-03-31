# VibeCopilot

VibeCopilot 是一个 AI 驱动的开发工作流助手，旨在通过结构化的方法和人工智能的辅助，为开发者提供更高效的编码体验。

## 特点

- 🧠 **AI 辅助开发**：集成 AI 模型，提供智能代码生成、重构和优化建议
- 📝 **文档生成**：自动生成项目文档、API 文档和开发指南
- 🔍 **项目分析**：分析代码结构、依赖关系和项目健康度
- 🛠️ **工作流管理**：提供结构化开发流程和任务管理
- 🧩 **模板系统**：支持各种项目类型的标准化模板

## 安装

```bash
# 使用pip安装
pip install vibecopilot

# 或者从源码安装
git clone https://github.com/jacobcy/VibeCopilot.git
cd VibeCopilot
pip install -e .
```

## 快速开始

初始化一个新项目：

```bash
vibecopilot init --name my-awesome-project --template python-web
```

分析现有项目：

```bash
vibecopilot analyze /path/to/project --output markdown
```

## 文档

查看我们的[完整文档](docs/)，了解更多关于：

- [项目需求文档](docs/1_Project_Requirements_Document_PRD.md)
- [应用流程](docs/2_App_Flow.md)
- [技术栈](docs/3_Tech_Stack.md)
- [前端指南](docs/4_Frontend_Guidelines.md)
- [后端结构](docs/5_Backend_Structure.md)
- [AI规则](docs/6_AI_Rules.md)
- [实施计划](docs/7_Implementation_Plan.md)
- [最佳实践](docs/8_Best_Practices.md)
- [开发路线图](docs/9_Development_Roadmap.md)

## 开发

设置开发环境：

```bash
# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 安装pre-commit钩子
pre-commit install
```

运行测试：

```bash
pytest
```

## 贡献

欢迎贡献！请查看我们的[贡献指南](CONTRIBUTING.md)了解如何参与项目。

## 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件。
