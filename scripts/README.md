# VibeCopilot 工具脚本

本目录包含VibeCopilot项目的各种工具脚本，用于自动化项目管理和开发流程。

## 目录结构

```
/scripts
├── github/            # GitHub相关工具
│   ├── api/           # GitHub API封装
│   ├── projects/      # GitHub Projects管理工具
│   └── issues/        # Issues和PR管理工具
├── setup/             # 环境设置和项目初始化工具
│   ├── init_project.py # 项目初始化脚本
│   └── ...
├── project/           # 项目管理工具
│   ├── docs_sync.py   # 文档同步检查
│   └── ...
└── utils/             # 通用工具函数
    ├── file_operations.py # 文件操作工具
    └── ...
```

## 使用方法

所有脚本都设计为命令行工具，支持`--help`参数查看详细用法：

```bash
python scripts/<script_path>.py --help
```

### 环境要求

- Python 3.8+
- 相关依赖在`requirements.txt`中指定

### 常用脚本

1. **项目初始化**

```bash
python scripts/setup/init_project.py --name "MyProject" --template python
```

2. **创建GitHub项目**

```bash
python scripts/github/projects/create_project.py --name "项目路线图"
```

3. **导入路线图**

```bash
python scripts/github/projects/import_roadmap.py --file docs/project/roadmap/development_roadmap.md
```

4. **添加Issues到项目**

```bash
python scripts/github/issues/add_to_project.py --title "实现功能X" --project-number 1
```

## 开发指南

如需添加新脚本，请遵循以下规范：

1. 按功能分类放置在合适的子目录中
2. 每个脚本只处理一个主要功能
3. 提供详细的命令行参数说明
4. 使用`utils`中的通用函数，避免代码重复
5. 添加适当的错误处理和日志记录
6. 遵循项目的编码规范和文档标准

## 贡献

欢迎提交PR改进这些脚本。请确保所有新脚本都包含详细的文档和测试。

## GitHub Projects路线图脚本

`github_projects.py`脚本用于从GitHub Projects中获取VibeCopilot项目路线图数据，生成结构化报告。

### 使用方法

1. 设置GitHub令牌（可选，但推荐）：

```bash
# 设置环境变量
export GITHUB_TOKEN="your-github-token"
```

2. 运行脚本生成Markdown格式报告：

```bash
python scripts/github_projects.py
```

3. 将报告保存到文件：

```bash
python scripts/github_projects.py -s reports/roadmap_status.md
```

4. 获取JSON格式数据：

```bash
python scripts/github_projects.py -f json
```

### 参数说明

```
-o, --owner      仓库所有者，默认为"jacobcy"
-r, --repo       仓库名称，默认为"VibeCopilot"
-p, --project    项目编号，默认为1
-f, --format     输出格式，可选"json"或"markdown"，默认为"markdown"
-t, --token      GitHub个人访问令牌，如未提供则从GITHUB_TOKEN环境变量获取
-s, --save       保存输出到指定文件路径
```

### 示例用法

1. 生成当前项目状态报告：

```bash
python scripts/github_projects.py -s reports/weekly_status.md
```

2. 查看不同仓库的路线图：

```bash
python scripts/github_projects.py -o otheruser -r otherrepo -p 2
```

3. 集成到自动化流程：

```bash
# 生成每日报告
python scripts/github_projects.py -s reports/daily/$(date +%Y-%m-%d).md

# 自动更新JSON数据源
python scripts/github_projects.py -f json -s data/roadmap.json
```

## 其他脚本

- （尚未添加其他脚本，后续会扩展）

## 注意事项

- 需要安装Python 3.6+
- 依赖库：`requests`（可通过 `pip install requests` 安装）
- 使用GitHub API可能受到请求速率限制，建议使用个人访问令牌
