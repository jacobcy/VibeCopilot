# VibeCopilot 项目脚本

本目录包含VibeCopilot项目中使用的各种辅助脚本。

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
