# VibeCopilot MCP服务器

VibeCopilot MCP服务器是一个符合Model Context Protocol (MCP)标准的服务器实现，用于在Cursor IDE中提供命令处理和工具集成功能。

## 功能特点

- 完全符合MCP标准规范
- 支持标准化的初始化流程
- 提供完整的能力声明
- 标准化的错误处理
- 支持多种传输层（stdio和SSE）

## 支持的能力

- **prompts**: 提示模板管理
- **resources**: 资源暴露和更新
- **tools**: 工具发现和执行
- **logging**: 服务器日志配置
- **completion**: 参数补全建议

## 安装要求

- Python 3.10+
- MCP SDK (`pip install mcp`)
- Click (`pip install click`)
- Rich (`pip install rich`)

## 使用方法

### 1. 命令行启动

```bash
# 基本用法
python server.py

# 指定工作目录
python server.py --workspace /path/to/workspace

# 启用详细日志
python server.py --verbose

# 自定义端口和主机
python server.py --port 8888 --host 0.0.0.0
```

### 2. Cursor IDE配置

在项目根目录的 `.cursor/mcp.json` 中添加以下配置：

```json
{
    "mcpServers": {
        "vibe-copilot": {
            "command": "python",
            "env": {
                "PYTHONPATH": "${workspaceRoot}"
            },
            "args": [
                "${workspaceRoot}/src/cursor/server.py",
                "--workspace",
                "${workspaceRoot}",
                "--verbose"
            ],
            "capabilities": {
                "prompts": true,
                "resources": true,
                "tools": true,
                "logging": true,
                "completion": true
            }
        }
    }
}
```

## API参考

### 支持的方法

1. `vibecopilot.execute_command`
   - 执行VibeCopilot命令
   - 参数：`{"command": "命令字符串"}`

2. `vibecopilot.list_commands`
   - 获取所有可用命令列表
   - 无需参数

3. `vibecopilot.get_command_help`
   - 获取特定命令的帮助信息
   - 参数：`{"command": "命令名称"}`

### 错误码

| 错误码 | 描述 | 示例场景 |
|--------|------|----------|
| -32600 | 无效请求 | 请求格式错误或缺少必要字段 |
| -32601 | 方法不存在 | 调用了未定义的方法 |
| -32602 | 无效参数 | 缺少必要参数或参数类型错误 |
| -32603 | 内部错误 | 服务器执行过程中发生错误 |
| -32700 | 解析错误 | JSON解析失败 |

## 开发指南

### 添加新命令

1. 在 `command_handler.py` 中注册新命令
2. 实现命令处理逻辑
3. 添加命令帮助信息

示例：
```python
def register_new_command(self):
    @self.command
    def new_command(args):
        """新命令的帮助信息"""
        # 实现命令逻辑
        pass
```

### 错误处理

使用 `MCPError` 类抛出标准化错误：

```python
raise MCPError(
    code=-32602,
    message="错误描述",
    data={"additional": "error info"}
)
```

## 调试

1. 启用详细日志：

```bash
python server.py --verbose
```

2. 查看请求/响应日志：

```bash
tail -f vibecopilot-mcp.log
```

3. 使用调试工具：

```bash
# 测试服务器连接
curl -X POST http://localhost:8765 -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "vibecopilot.list_commands", "id": 1}'
```

## 最佳实践

1. **错误处理**
   - 使用标准错误码
   - 提供详细错误信息
   - 记录错误日志

2. **性能优化**
   - 异步处理长时间运行的命令
   - 实现请求超时机制
   - 合理使用缓存

3. **安全性**
   - 验证所有输入
   - 限制文件系统访问范围
   - 实现请求速率限制

## 常见问题

1. **服务器无法启动**
   - 检查端口是否被占用
   - 确认Python版本是否满足要求
   - 验证所有依赖是否正确安装

2. **命令执行失败**
   - 检查工作目录设置
   - 查看详细错误日志
   - 验证命令参数格式

3. **IDE集成问题**
   - 确认MCP配置文件格式
   - 检查环境变量设置
   - 验证服务器状态

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License
