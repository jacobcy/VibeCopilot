# VibeCopilot - 智能项目管理助手

VibeCopilot是一个为开发者设计的智能项目管理工具，旨在通过AI辅助和规范化流程，提高项目质量和开发效率。

## 🌟 主要功能

- **规范化开发流程** - 引导开发者遵循专业的项目开发生命周期
- **AI辅助集成** - 优化与Cursor等AI工具的协作效率
- **文档生成与管理** - 自动化文档创建和更新
- **GitHub Projects集成** - 路线图和任务管理自动化
- **项目模板库** - 快速启动新项目的标准化模板
- **项目结构可视化** - 利用GitDiagram生成项目架构图

## 📋 项目结构

```
/VibeCopilot
├── .cursor               # Cursor AI配置
├── docs                  # 项目文档
│   ├── ai                # AI读取的文档
│   ├── human             # 人类阅读的文档
│   └── project           # 项目规划文档
├── modules               # 集成的外部模块
│   ├── cursor-custom-agents-rules-generator  # Cursor规则生成器
│   ├── gitdiagram        # 项目结构可视化工具
│   └── obsidiosaurus     # 文档生成工具
├── scripts               # 工具脚本
│   └── utils             # 工具类脚本
├── tools                 # 工具使用指南
├── templates             # 项目模板
└── src                   # 源代码(开发中)
```

## 🚀 快速开始

### 安装

1. 克隆仓库(包含子模块):

```bash
git clone --recursive https://github.com/yourusername/VibeCopilot.git
cd VibeCopilot
```

2. 创建虚拟环境:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows
```

3. 安装依赖:

```bash
pip install -r requirements.txt
```

### 使用方法

1. **查看入门指南**:

```bash
cat docs/human/guides/getting_started.md
```

2. **使用项目模板**:

```bash
python scripts/setup/init_project.py --name "MyProject" --template python
```

3. **与GitHub Projects集成**:

```bash
python scripts/github/create_project.py --name "项目路线图"
```

4. **生成项目结构图**:

```bash
python scripts/utils/generate_diagram.py . --setup
```

## 📚 文档

- **用户指南**: [docs/human/guides](docs/human/guides/)
- **教程**: [docs/human/tutorials](docs/human/tutorials/)
- **AI规则**: [docs/ai/rules](docs/ai/rules/)
- **工具指南**: [tools](tools/)

## 🛠️ 开发

### 开发流程

VibeCopilot采用"开发流程五步法":

1. **遵守规范** - 严格遵循项目编码和文档规范
2. **确认需求** - 明确开发目标和范围
3. **制定计划** - 分解任务，设计解决方案
4. **修改代码** - 实现功能，保证质量
5. **总结报告** - 记录过程和结果

### 集成的子模块

- **cursor-custom-agents-rules-generator** - Cursor规则生成器，提供自动化规则生成和管理
  - 作者: [jacobcy](https://github.com/jacobcy/cursor-custom-agents-rules-generator)
  - 主要功能: 自动规则生成、标准化文档格式、AI行为控制和优化

- **gitdiagram** - 项目结构可视化工具，将代码库转换为交互式架构图
  - 作者: [jacobcy](https://github.com/jacobcy/gitdiagram)
  - 主要功能: 即时可视化、交互式组件导航、快速生成项目架构图

- **obsidiosaurus** - Obsidian与Docusaurus集成工具
  - 作者: [CIMSTA](https://github.com/CIMSTA/obsidiosaurus)
  - 主要功能: 将Obsidian笔记转换为Docusaurus站点文档

### 贡献指南

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件

## 📞 联系方式

项目维护者 - [@yourusername](https://github.com/yourusername)

项目链接: [https://github.com/yourusername/VibeCopilot](https://github.com/yourusername/VibeCopilot)
