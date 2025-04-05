# 项目初始化与环境设置工具

本目录包含VibeCopilot项目初始化和环境设置的工具脚本。

## 主要功能

`init_project.py`是一个多功能工具，支持以下操作：

1. 基于模板创建新项目
2. 自动设置Python开发环境
3. 管理现有项目的依赖和环境

## 使用方法

### 查看可用模板

```bash
python scripts/setup/init_project.py list
```

### A. 创建新项目

```bash
# 基本使用
python scripts/setup/init_project.py init --name my-project --template basic

# 创建项目并自动设置环境
python scripts/setup/init_project.py init --name my-project --template basic --setup-env

# 指定输出目录
python scripts/setup/init_project.py init --name my-project --template basic --output /path/to/output

# 使用模板变量
python scripts/setup/init_project.py init --name my-project --template basic --var AUTHOR="My Name" --var VERSION="1.0.0"
```

### B. 设置现有项目环境

```bash
# 在VibeCopilot项目根目录运行
python scripts/setup/init_project.py setup
```

## 技术细节

- 使用Python 3.13作为默认Python环境
- 使用uv作为包管理工具
- 自动创建虚拟环境(.venv)
- 安装项目依赖(包括dev和docs可选依赖)
- 配置pre-commit钩子

## 依赖

- Python 3.13+ (`brew install python@3.13`)
- uv (自动安装)
