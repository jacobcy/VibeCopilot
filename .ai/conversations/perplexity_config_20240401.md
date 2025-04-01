# Perplexity API 配置记录

## 背景

- 时间：2024-04-01 16:45
- 目的：配置Cursor的Perplexity API工具

## 问题描述

Cursor的MCP配置文件中缺少Perplexity相关配置，导致无法使用Perplexity工具。

## 解决方案

1. 创建Python脚本`add_perplexity.py`添加Docker方式的Perplexity配置
2. 脚本主要功能：
   - 读取`~/.cursor/mcp.json`
   - 添加perplexity-ask配置
   - 备份原配置到`mcp.json.bak`
   - 写入新配置

## 关键代码

```python
config['mcpServers']['perplexity-ask'] = {
    "command": "docker",
    "args": [
        "run",
        "-i",
        "--rm",
        "--name",
        "mcp-perplexity-ask",
        "-e",
        "PERPLEXITY_API_KEY",
        "mcp/perplexity-ask"
    ],
    "envFile": ".env.perplexity"
}
```

## 执行结果

- 成功添加Perplexity配置
- 原配置已备份到`~/.cursor/mcp.json.bak`
- 需要重启Cursor以生效

## 后续操作

1. 完全关闭Cursor应用程序
2. 重新启动Cursor应用程序
3. 验证Perplexity工具可用性

## 相关文件

- 配置脚本：`add_perplexity.py`
- 配置文件：`~/.cursor/mcp.json`
- 环境变量：`~/.cursor/.env.perplexity`
