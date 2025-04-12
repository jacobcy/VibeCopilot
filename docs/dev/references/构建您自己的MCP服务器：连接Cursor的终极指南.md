---
title: "构建您自己的MCP服务器：连接Cursor的终极指南"
source: "https://zhuanlan.zhihu.com/p/30079943120"
author:
  - "[[知乎专栏]]"
published:
created: 2025-04-09
description: "模型上下文协议（MCP）是AI领域的USB-C——一种正在改变我们与大型语言模型（LLM）交互方式的通用连接器。2024年底由Anthropic发布，MCP允许开发人员构建AI模型与外部工具或数据源之间的安全双向连接。 MCP服务器…"
tags:
  - "clippings"
---
[模型上下文协议](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=%E6%A8%A1%E5%9E%8B%E4%B8%8A%E4%B8%8B%E6%96%87%E5%8D%8F%E8%AE%AE&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiLmqKHlnovkuIrkuIvmlofljY_orq4iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNTUwMzgyNzAsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.cpVqSX593gCjCA-0m_Z-SIxoOMqR0g4qGm8k9SFYp0M&zhida_source=entity)（MCP）是AI领域的USB-C——一种正在改变我们与大型语言模型（LLM）交互方式的通用连接器。2024年底由Anthropic发布，MCP允许开发人员构建AI模型与外部工具或数据源之间的安全双向连接。

[MCP服务器](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=MCP%E6%9C%8D%E5%8A%A1%E5%99%A8&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiJNQ1DmnI3liqHlmagiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNTUwMzgyNzAsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.k0KzzK8YJISiK4sOlgzsoCvBlGo3EWpoP4LDaEu_8gQ&zhida_source=entity)使您能够在保持对数据完全控制的同时，为[Claude](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=Claude&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiJDbGF1ZGUiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNTUwMzgyNzAsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.irxNw4e7q19jnExoQ5fMRT6KPzX2g6jA3uADNy5wOQE&zhida_source=entity)、[Cursor](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=Cursor&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiJDdXJzb3IiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNTUwMzgyNzAsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.3C6vy7tGHPUYsK4RylKoys4Gw586fLhcO-EsoCEMR7w&zhida_source=entity)、[Windsurf](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=Windsurf&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiJXaW5kc3VyZiIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI1NTAzODI3MCwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.TKIuoOrdcMplQ2ZgXmuq8cqo01TyoL6vaGd84QrWxF8&zhida_source=entity)等编辑器扩展个性化功能。通过连接 MCP 服务器，显著提升了运行的稳定性和流畅性，简化了开发流程，通过集成多种外部工具和服务（如数据库管理、UI/UX设计、浏览器自动化等）扩展了功能，并增强了代码生成的准确性和相关性。此外，MCP协议支持多语言和跨平台，确保了数据的安全性和合规性，从而提高了整体工作效率和开发体验。

通过MCP，使得AI编程工具，例如Cursor、Windsurf、Claude Code和[Zed](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=Zed&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiJaZWQiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNTUwMzgyNzAsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.7ofovgO9vi_maHYQ3xZBcjMjv34Lgas33e6TUnPOTi8&zhida_source=entity)，现在可以访问：

- 您的本地文件和数据库
- 您创建的自定义工具
- 第三方API和服务
- 私有文档

同时将敏感数据保留在您的基础设施内。

## 开始MCP服务器开发

让我们构建一个简单但实用的MCP服务器，任何兼容的客户端都可以连接到它。我们将创建一个具有以下功能的服务器：

1. 智能搜索您的代码库
2. 执行自定义代码分析
3. 连接到外部开发API

### 先决条件

- [Python 3.10+](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=Python+3.10%2B&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiJQeXRob24gMy4xMCsiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNTUwMzgyNzAsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.2T5EQQkEbBPUOD4t6D8FPrLLSwuXEj6DcozxD3kOteA&zhida_source=entity) 或 [Node.js 16+](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=Node.js+16%2B&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiJOb2RlLmpzIDE2KyIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI1NTAzODI3MCwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.GGedYT_vv-lRaVqZmxPSIxKip8rFsFvByeUC0l2NtKA&zhida_source=entity)
- 基本了解 [JSON-RPC](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=JSON-RPC&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiJKU09OLVJQQyIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI1NTAzODI3MCwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.yVEhZHkzW3L2blZnQBp4j-2FdHrQxK5UYyaAyB8oqPY&zhida_source=entity)
- 一个MCP兼容的客户端（如Claude Desktop、Cursor、Windsurf、Zed等）

### 第一步：设置MCP服务器项目

我们将使用Python和官方[MCP SDK](https://zhida.zhihu.com/search?content_id=255038270&content_type=Article&match_order=1&q=MCP+SDK&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NDQzNjAzMDQsInEiOiJNQ1AgU0RLIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjU1MDM4MjcwLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.NzQ5Rs3XTi9scjhwlZjlAqkzZ4OH9nVuPl7tiGd5E5w&zhida_source=entity)来完成这个示例。创建一个新的项目目录并设置您的环境：

```
# 创建项目目录
mkdir my-mcp-server
cd my-mcp-server

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # 在Windows上：venv\Scripts\activate

# 安装依赖
pip install mcp httpx
```

### 第二步：实现基础MCP服务器

创建一个名为`server.py`的文件，并添加以下代码：

```
from mcp.server.lowlevel import Server
import mcp.types as types
import httpx
import os
import json
import glob

# 初始化服务器
app = Server("dev-tools-server")

@app.call_tool()
asyncdef call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理来自客户端的工具调用。"""
    if name == "search_code":
        returnawait search_code(arguments.get("query", ""), arguments.get("directory", ""))
    elif name == "analyze_dependencies":
        returnawait analyze_dependencies(arguments.get("directory", "."))
    elif name == "fetch_documentation":
        returnawait fetch_documentation(arguments.get("package", ""))
    else:
        return [types.TextContent(type="text", text=f"错误：未知工具：{name}")]

asyncdef search_code(query: str, directory: str) -> list[types.TextContent]:
    """在代码文件中搜索特定查询内容。"""
    results = []
    for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css']:
        for filepath in glob.glob(f"{directory}/**/*{ext}", recursive=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                if query.lower() in content.lower():
                    match_context = get_context(content, query)
                    results.append(f"文件：{filepath}\n{match_context}\n--")
            except Exception as e:
                continue
    if results:
        return [types.TextContent(type="text", text="搜索结果：\n\n" + "\n".join(results))]
    else:
        return [types.TextContent(type="text", text=f"在目录'{directory}'中未找到与'{query}'匹配的结果。")]

def get_context(content: str, query: str, context_lines: int = 3) -> str:
    """获取匹配项周围的上下文。"""
    lines = content.split('\n')
    matches = []
    for i, line in enumerate(lines):
        if query.lower() in line.lower():
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            context = "\n".join(lines[start:end])
            matches.append(f"行{start+1}-{end}:\n{context}")
    return"\n\n".join(matches)

asyncdef analyze_dependencies(directory: str) -> list[types.TextContent]:
    """分析项目依赖项。"""
    dependency_files = {
        'python': ['requirements.txt', 'setup.py', 'pyproject.toml'],
        'node': ['package.json'],
        'dotnet': ['*.csproj', '*.fsproj', '*.vbproj'],
    }
    results = []
    for lang, files in dependency_files.items():
        for file_pattern in files:
            for filepath in glob.glob(f"{directory}/**/{file_pattern}", recursive=True):
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                    results.append(f"在{filepath}中发现{lang}依赖项")
                except Exception:
                    continue
    if results:
        return [types.TextContent(type="text", text="依赖项分析：\n\n" + "\n".join(results))]
    else:
        return [types.TextContent(type="text", text=f"在目录'{directory}'中未找到依赖项文件。")]

asyncdef fetch_documentation(package: str) -> list[types.TextContent]:
    """获取包的文档。"""
    try:
        # 对于Python包
        url = f"https://pypi.org/pypi/{package}/json"
        asyncwith httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                summary = data.get("info", {}).get("summary", "无摘要可用")
                description = data.get("info", {}).get("description", "无描述可用")
                return [types.TextContent(type="text", text=f"{package}的文档：\n\n摘要：{summary}\n描述：{description}")]
    except Exception:
        pass
    # 如果PyPI失败，尝试npm包
    try:
        url = f"https://registry.npmjs.org/{package}"
        asyncwith httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                description = data.get("description", "无描述可用")
                return [types.TextContent(type="text", text=f"{package}的文档：\n\n描述：{description}")]
    except Exception:
        pass
    return [types.TextContent(type="text", text=f"无法获取'{package}'的文档。")]

@app.list_tools()
asyncdef list_tools() -> list[types.Tool]:
    """列出可用工具。"""
    return [
        types.Tool(
            name="search_code",
            description="在代码文件中搜索特定查询内容",
            inputSchema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "description": "要在代码文件中搜索的查询内容"},
                    "directory": {"type": "string", "description": "搜索目录（默认：当前目录）"}
                }
            }
        ),
        types.Tool(
            name="analyze_dependencies",
            description="分析项目依赖项",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "分析目录（默认：当前目录）"}
                }
            }
        ),
        types.Tool(
            name="fetch_documentation",
            description="获取包的文档",
            inputSchema={
                "type": "object",
                "required": ["package"],
                "properties": {
                    "package": {"type": "string", "description": "要获取文档的包名"}
                }
            }
        )
    ]

if __name__ == "__main__":
    import sys
    # 默认使用标准输入输出传输
    transport = "stdio"
    port = 8000
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "sse":
            transport = "sse"
        if len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
            except ValueError:
                pass
    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        import uvicorn
        sse = SseServerTransport("/messages/")
        asyncdef handle_sse(request):
            asyncwith sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ]
        )
        print(f"在端口{port}上启动MCP服务器，使用SSE传输")
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server
        import anyio
        asyncdef run_stdio():
            asyncwith stdio_server() as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        print("使用标准输入输出传输启动MCP服务器")
        anyio.run(run_stdio)
```

### 第三步：运行您的MCP服务器

您可以以两种模式运行服务器：

1. 标准输入输出模式（适用于桌面客户端，如Claude Desktop）：python server.py
2. 服务器发送事件（SSE）模式（适用于基于Web的客户端）：python server.py sse 8000

## 将您的MCP服务器连接到客户端

现在您已经有一个可以工作的MCP服务器，让我们将它连接到不同的客户端：

### Claude Desktop

1. 编辑您的Claude Desktop配置文件：

- 在macOS上： `~/Library/Application Support/Claude/claude_desktop_config.json`
- 在Windows上： `%APPDATA%\Claude\claude_desktop_config.json`
- 添加您的服务器配置：{
 "mcpServers": {
 "dev-tools": {
 "command": "python",
 "args": \["/absolute/path/to/my-mcp-server/server.py"\]
 }
 }
 }
- 重启Claude Desktop并查找工具图标出现。

### Cursor IDE

对于Cursor，您通常会使用SSE传输：

1. 以SSE模式运行您的服务器：python server.py sse 8000
2. 在Cursor中，转到设置 → 功能 → MCP服务器
3. 添加一个新的服务器，配置如下：

- 名称： `dev-tools`
- 类型： `sse`
- URL： `http://localhost:8000/sse`

### Windsurf和其他客户端

大多数较新的客户端遵循与Cursor类似的配置模式：

1. 以SSE模式运行您的服务器
2. 在客户端的设置中查找MCP配置
3. 使用SSE URL进行配置

## 高级MCP服务器功能

让我们为服务器添加一些更强大的功能：

### 添加文件资源支持

MCP服务器可以向客户端提供文件资源。这允许AI模型直接访问和读取文件：

```
@app.list_resources()
asyncdef list_resources() -> list[types.Resource]:
    """列出可用资源。"""
    resources = []
    # 添加README文件（如果存在）
    readme_paths = ['README.md', 'README.txt', 'Readme.md']
    for path in readme_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            resources.append(types.Resource(
                name="readme",
                description="项目README文件",
                content=[types.TextContent(type="text", text=content)]
            ))
            break
    return resources
```

### 添加交互式提示模板

MCP还支持提示模板，这些是引导模型响应的预写模板：

```
@app.list_prompts()
asyncdef list_prompts() -> list[types.Prompt]:
    """列出可用提示。"""
    return [
        types.Prompt(
            name="code_review",
            description="对特定文件进行代码审查",
            inputSchema={
                "type": "object",
                "required": ["filepath"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "要审查的文件路径"
                    },
                    "focus": {
                        "type": "string",
                        "description": "要重点关注的具体方面（例如，'安全性'）"
                    }
                }
            },
            template="""
            请审查以下来自{{filepath}}的代码：
            \`\`\`
            {{#file filepath}}
            \`\`\`
            {{#if focus}}
            专注于{{focus}}方面的审查。
            {{else}}
            进行一般性代码审查，重点关注：
            - 代码质量
            - 潜在错误
            - 性能问题
            - 安全问题
            {{/if}}
            提供具体的改进建议，并附上代码示例。
            """
        )
    ]
```

## 安全注意事项

在开发MCP服务器时，请牢记以下安全实践：

1. 输入验证：始终验证并清理来自客户端的输入。
2. 文件访问控制：限制文件访问到特定目录。
3. API密钥处理：不要将API密钥硬编码；使用环境变量。
4. 速率限制：为资源密集型操作实现速率限制。
5. 错误处理：返回信息丰富但不泄露过多细节的错误消息。

## 在实际开发中使用MCP服务器

MCP服务器不仅仅是一个酷炫的技术演示——它可以彻底改变您的开发工作流程：

### 个性化文档助手

将您的MCP服务器连接到内部文档、代码库和知识库，创建一个真正了解您项目的个性化助手：

```
async def search_internal_docs(query: str) -> list[types.TextContent]:
    # 实现搜索内部文档的功能
    # 这可以连接到公司Wiki、Confluence或其他系统
    pass
```

### 工作流自动化助手

直接从AI助手自动化常见的开发任务：

```
async def run_tests(test_path: str = None) -> list[types.TextContent]:
    """运行项目测试，可选路径过滤。"""
    command = ["pytest"]
    if test_path:
        command.append(test_path)
    # 运行测试并捕获输出
    # 将结果返回给AI
    pass
```

### 代码质量守护者

创建工具以在整个团队中强制执行代码质量标准：

```
async def lint_code(filepath: str) -> list[types.TextContent]:
    """对指定代码文件运行代码检查工具。"""
    # 实现运行代码检查工具并返回结果
    pass
```

## 重要实现说明

### 客户端支持状态

截至2025年3月，Claude Desktop和Cursor提供了强大的MCP支持，而Windsurf和Zed的实现可能在功能和稳定性方面有所不同。始终检查每个客户端的最新文档以获取当前兼容性信息。

### 代码实现

提供的代码示例仅供演示目的，在生产环境中可能需要额外的错误处理和优化。请将其视为一个起点，而不是一个生产就绪的解决方案。

### 安全改进

为了增强安全性，实现路径清理以防止目录遍历攻击：

```
import os.path
directory = os.path.normpath(os.path.join(base_directory, user_input))
if not directory.startswith(base_directory):
    return [types.TextContent(type="text", text="访问被拒绝：无效目录")]
```

### 客户端特定说明

对于Windsurf，MCP配置位于设置 → AI → 外部工具。

### 测试建议

在将MCP服务器投入生产之前，务必使用您集成的每个客户端进行彻底测试。

## 结论

MCP服务器代表了开发人员与AI交互方式的范式转变。通过构建您自己的MCP服务器，您创建了一个桥梁，将您的开发环境与AI助手连接起来，解锁了生产力和创造力的新可能性。

该技术仍在迅速发展，但早期采用者已经在工作流程中看到了显著的改进。无论您使用的是Claude、Cursor、Windsurf、Zed还是任何其他MCP兼容客户端，自定义MCP服务器都使您能够控制AI与您的开发环境的交互方式。

更多资源见星球，加入QuantML星球，与750+专业人士一起交流学习：

往期回顾

QuantML-Qlib开发版：

- [QuantML-Qlib重磅更新：DeepSeek核心模型结构用于选股](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247489025%26idx%3D1%26sn%3D35941156783794d719e6ff891ce720c3%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Factor | 融合TA-Lib100+技术指标，自定义构建AlphaZoo](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488425%26idx%3D1%26sn%3Da071798fdcc183b3d630e8bc0d637adf%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Model | 还在使用MSE？试试这些更加适合金融预测的损失函数](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247487997%26idx%3D1%26sn%3De05e8e0dafa605615d425ff1f0702c4b%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Model | 如何运行日内中高频模型](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247487722%26idx%3D1%26sn%3D4597316f8066c31d4bbf34226d888ef4%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Model | 超越GRU，液态神经网络LNN用于股票预测](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247487291%26idx%3D1%26sn%3Dba0c7cb11cbe247900fa326a50dd5dd9%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Model | 华泰SAM：提升AI量化模型的泛化性能 研报复现](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247487238%26idx%3D1%26sn%3D41cbb5b3bb3e5a277c9175ba64642259%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Model | 华泰AlphaNet模型复现](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247485666%26idx%3D1%26sn%3Dd9a7ec92f3f93d44d4620bb56ab0d620%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Model | 清华大学&华泰证券 在高胜率时交易](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247485500%26idx%3D1%26sn%3Db29e1d2efe2482165245ab6add4af051%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Factor | 高效优雅的因子构建方法：以开源金工切割动量因子为例](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247485016%26idx%3D1%26sn%3D17598e7dbdfcb7e908b2a393c5dd28ad%26chksm%3Dce7e6146f909e85067dd7de6ca5f02c12afb9f195f92871c87b0daed0153b1ea04f3057d9683%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Model | 滚动模型训练](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247485371%26idx%3D1%26sn%3D37b9d5c40f9b08244fd68ee73991218f%26chksm%3Dce7e60a5f909e9b373b4b850300768fd2dbe0250e1237e11132f3af9d54f9bde97ba84c47766%26scene%3D21%23wechat_redirect)
- [QuantML-QlibModel | KAN + GRU 时序模型用于股票预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484511%26idx%3D1%26sn%3Dbb9168cb75b1b31fea0b8a5c3ce61d84%26chksm%3Dce7e6341f909ea5755b03dec3d0407d15ac38b60a573cd5517a8a51ba047b1d630c7a15972cb%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | 蚂蚁&清华 TimeMixer：可分解多尺度融合的时间序列模型用于金融市场预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484961%26idx%3D1%26sn%3Dc5acb48d3c063c0a69d6566817875aee%26chksm%3Dce7e613ff909e8290602d7d0c32fd7d764fb25660956fbfc3238a7df3d41d5f7e0ffaa2cb6a8%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib Model | Kansformer：KAN+Transformer时序模型用于股票收益率预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484779%26idx%3D1%26sn%3Df417e4ef37562e22fa592ca280fe5a43%26chksm%3Dce7e6275f909eb63cf3410377b0c40a033fb2788b342665c3b266ecbfb426465dcf241bb847d%26scene%3D21%23wechat_redirect)
- [QuantML-QlibModel | 使用OPTUNA优化模型超参](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484466%26idx%3D1%26sn%3D8c6a69a98e64eeba373b1042d276fb81%26chksm%3Dce7e632cf909ea3ae70af5b1acee4163c7b85cb8170a0ef6a999130d05bdb5a54b89a895a0d8%26scene%3D21%23wechat_redirect)
- [QuantML-QlibDB | Clickhouse 行情存储与读取方案](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484391%26idx%3D1%26sn%3Db56d54740da5d77bef608d787033e321%26chksm%3Dce7e64f9f909edef46da039efbeaf07b636ef08477a3f4ba2b49dea329d2c29b71635a809aca%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib LLM | GPT-4o复现因子计算代码](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484355%26idx%3D1%26sn%3D0e2e068277314d93d0373ad5e1b0da82%26chksm%3Dce7e64ddf909edcb0f2894f353b26825800a7862dfb6a53b692b212ae5e93e43c0d7b1ee71cf%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | 最新xLSTM用于股票市场预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484305%26idx%3D1%26sn%3Ddeac6944b376b2e7d7cdb552b2bcc0b4%26chksm%3Dce7e648ff909ed99d80c0a73506003b9afbb1e414e748bb91e5b36e7ecb737ded8745d183518%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | 强化学习因子挖掘](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484272%26idx%3D1%26sn%3D0b9b53150500d4c77f6afc3267b1313f%26chksm%3Dce7e646ef909ed78bb3216dd647872ffc47fafc116021b34caef842d6b78c1cbf98c343e3fd2%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | 清华大学时序SOTA模型iTransformer用于股票市场预测QuantML-Qlib开发版 | 最新神经网络结构KAN用于因子挖掘](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484235%26idx%3D1%26sn%3D5f8f21ad605eee4a9152954164b9b441%26chksm%3Dce7e6455f909ed43d8e4c8d964b5d2d02ed448e8530f6bed0bce00fc8c5d823a82184af1e5c7%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | 直接读取pg/mysql/mongodb数据库](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484180%26idx%3D2%26sn%3D69ca761ab7d152740a3058b86ed02e6c%26chksm%3Dce7e640af909ed1cc246be0a4e683a9b45e8bf256cc034cba0a6d316f6e62f9858d4e75e4efb%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | MoE混合专家系统用于提升Transformer表现](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484124%26idx%3D1%26sn%3D735f6f9488e202679ad96b3d19329673%26chksm%3Dce7e65c2f909ecd438e908babf20726acc73162f9a5198c445f5bf3b1bc8ed6ed16474cbecfd%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | 一键数据更新](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484065%26idx%3D2%26sn%3Db2ad5cf74fcc452e49f7e4c4ec07439b%26chksm%3Dce7e65bff909eca9c28072649b39e7ad08b9db4a71e5d5d492bfca04ac6b720ca368a665257a%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | AAAI最佳论文Informer用于金融市场预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484065%26idx%3D1%26sn%3Dd666c3cd759ceffbdb304c1097a4ebb8%26chksm%3Dce7e65bff909eca9a4fedaef3b9edabf3d4d65c11f38d6edc80e973a9cc6d4c9944944666071%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | 取代Transformer的下一代神经网络结构Mamba用于金融市场预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247483988%26idx%3D1%26sn%3D214bf5cd0739cb26c4af3a56252a99eb%26chksm%3Dce7e654af909ec5cba364d5fea1cb170d9a5a7181b5ed063b97e2dbdff3a7a1fdfd587aafffd%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | 时序SOTA模型PatchTST用于金融市场预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247483873%26idx%3D1%26sn%3Dc2376b203dc69fc2b8df1db00c5246a0%26chksm%3Dce7e66fff909efe99c0f61c17f6226e7e310c8c0fbe900bb7bdad4aafece8aa85e98348297f7%26scene%3D21%23wechat_redirect)
- [QuantML-Qlib开发版 | 一行代码运行DLinear模型用于股票预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247483796%26idx%3D1%26sn%3Dc10f4d766eb52e8dee53ffb954beeafc%26chksm%3Dce7e668af909ef9c5a1a8c6ebc29566475af184ffdf503a0fda308f896eaf42272c6dd591fd2%26scene%3D21%23wechat_redirect)
 研报复现：
- [重磅更新！80+量化策略复现（持续更新中）](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488528%26idx%3D1%26sn%3Df9c98f60baca2b690956ff6b56a2553f%26scene%3D21%23wechat_redirect)
- [BARRA CNE6模型复现](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484419%26idx%3D1%26sn%3Dec71d0938e90e65145742754ddc4e6d9%26chksm%3Dce7e631df909ea0b60b8a41c67f03e193aff17c556ef30f83528d354e3256402a12205f40b91%26scene%3D21%23wechat_redirect)
- [研报复现 | QRS择时信号及改进](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247487334%26idx%3D1%26sn%3D110ef4c3ae5dce77260eab213d6163ac%26scene%3D21%23wechat_redirect)
- [研报复现 | 跳跃因子系列-下](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247486787%26idx%3D1%26sn%3Dbfe98c0b8d331027191761df3b85ea8c%26scene%3D21%23wechat_redirect)
- [研报复现 | 跳跃因子系列-上](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247486761%26idx%3D1%26sn%3D84a2de96dd3bc7a7fb38386684b3eec4%26scene%3D21%23wechat_redirect)
- [研报复现 | 锚定反转因子](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247486379%26idx%3D1%26sn%3Dd6763bb198d0706c101f2544aa752b4f%26scene%3D21%23wechat_redirect)
- [研报复现 | 另类ETF交易策略：日内动量](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247485900%26idx%3D1%26sn%3Dc7facdbd47ebc0161839fbea1def4ecc%26scene%3D21%23wechat_redirect)
- [研报复现 | 国盛金工：如何将隔夜涨跌变为有效的选股因子？——基于对知情交易者信息优势的刻画](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247485766%26idx%3D1%26sn%3D89d4060fb135105b969c0ef2f145a7e0%26scene%3D21%23wechat_redirect)
- [研报复现 | 招商证券：基于鳄鱼线的指数择时及轮动策略](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247485702%26idx%3D1%26sn%3D2b0ed284177a66ee9d0e8623cd9cb1b4%26scene%3D21%23wechat_redirect)
- [研报复现 | 华西金工-股票网络与网络中心度因子研究](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484829%26idx%3D1%26sn%3D3da8197374301bab9610f7ed5d4b715b%26chksm%3Dce7e6283f909eb9509b3ebc9989fe9d140d5ee663ac8749aeb608833ff37544421d0dcd0fa9c%26scene%3D21%23wechat_redirect)
- [研报复现 | 基于筹码分布的选股策略](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247485327%26idx%3D1%26sn%3D260ff24d4fde6fa394f989b23488780f%26chksm%3Dce7e6091f909e987086ba01ad8df6f3dd8ef0fa63fe41930e784f2648066e44bad6c24b02a91%26scene%3D21%23wechat_redirect)
- [研报复现 | 开源金工-高频追涨杀跌因子复现](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484915%26idx%3D1%26sn%3Da7279f3516c0998cd6c3e6fddec017a9%26chksm%3Dce7e62edf909ebfb211722e6bb19b4a43243c4751dd6e4143249b04afe3bed980ffb0ce68ff3%26scene%3D21%23wechat_redirect)
- [研报复现 | 开源证券 ：形态识别，均线的](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484616%26idx%3D1%26sn%3Dcbf8bf6df9906603258516c808e45b94%26chksm%3Dce7e63d6f909eac044db7ca34624d21c241c485bce4450e1ea23ccf4463414638c52cae5cbea%26scene%3D21%23wechat_redirect)
- [券商研报因子复现及表现研究](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484329%26idx%3D1%26sn%3D24f18ad20fc0a44ba09a19d43becf651%26scene%3D21%23wechat_redirect)
 前沿论文代码：
- [DeepSeek-TS+: MLA-Mamba及GRPO用于多序列预测统一框架](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247489198%26idx%3D1%26sn%3D4ea3856dcf099493c2ba6db7cf0e23a2%26scene%3D21%23wechat_redirect)
- [Hummingbot：开源加密货币做市机器人框架](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247489153%26idx%3D1%26sn%3D98198f6cca4aa5bc5646e926c358f01d%26scene%3D21%23wechat_redirect)
- [FinRLlama：基于强化学习和市场反馈的金融情感分析LLM优化方案](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247489127%26idx%3D1%26sn%3Dfaad16c8ac3ca02dcb982837d03b21ab%26scene%3D21%23wechat_redirect)
- [端到端基于LLM的增强型交易系统](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247489113%26idx%3D1%26sn%3Db145d87e23cfa5c9e780099fc7c1136c%26scene%3D21%23wechat_redirect)
- [基于分层强化学习的日内风险因子挖掘](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247489104%26idx%3D1%26sn%3Dc0b6938ebcf0cbd8244f87abe609798e%26scene%3D21%23wechat_redirect)
- [DeepScalper：深度强化学习捕捉日内交易的短暂机会](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247489018%26idx%3D1%26sn%3D1ea12b6de5e28e2700b4947081a32b7b%26scene%3D21%23wechat_redirect)
- [TradingAgents：基于多智能体LLM的金融交易框架](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488712%26idx%3D1%26sn%3Ddaa7fb4a9d49a621f9f54579dda4a184%26scene%3D21%23wechat_redirect)
- [Kaggle - Optiver trading at the close第一名解决方案及部分代码](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484474%26idx%3D1%26sn%3Dd7cb587cd3604299930006e2f0dd54cf%26chksm%3Dce7e6324f909ea320e815af314efc2f2eb4dd944ca56e0fccaf0990e099b001610461a1e798d%26scene%3D21%23wechat_redirect)
- [量化交易全攻略：从入门到精通的终极指南](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247485434%26idx%3D1%26sn%3D9ea5dd98ac51fa0eb0381d97fa2d2b78%26scene%3D21%23wechat_redirect)
- [普林斯顿&牛津大学 | 大模型在金融领域的应用、前景和挑战](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484935%26idx%3D1%26sn%3Dc04614316ebaaf46fe0ef35b88aba330%26chksm%3Dce7e6119f909e80fcc08f835d91cdddeb1e3dacf3bd924fcd5958381f13eaace114139af909b%26scene%3D21%23wechat_redirect)
- [Style Miner：基于强化学习算法的风格因子构造](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488487%26idx%3D1%26sn%3D82c708030492662f4bd958c09cd6ad35%26scene%3D21%23wechat_redirect)
- [AQR创始人Cliff Asness：市场效率下降假说](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488456%26idx%3D1%26sn%3D7014a441007cd69045f69cfada3f64fd%26scene%3D21%23wechat_redirect)
- [增强动量策略：动量Transformer模型](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488434%26idx%3D1%26sn%3De8431bb689e27562a620cdb6cf3c6d31%26scene%3D21%23wechat_redirect)
- [XGBoost 2.0 ：提升时间序列预测能力](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488387%26idx%3D1%26sn%3Dd123dcfc4c74e13b7bfd10a707eab81f%26scene%3D21%23wechat_redirect)
- [NIPS 24 | FinCon: 基于LLM的多智能体交易及组合管理框架](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488353%26idx%3D1%26sn%3Df6684d1c9788e0f9dcd09b781cbd619a%26scene%3D21%23wechat_redirect)
- [NIPS 24 | CausalStock: 基于端到端因果发现的新闻驱动股价预测模型](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488342%26idx%3D1%26sn%3D4793d31201295e14a5978556f449adca%26scene%3D21%23wechat_redirect)
- [JFE | 高效估计买卖价差的模型、实证与应用](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488303%26idx%3D1%26sn%3D60ab39ed1be0a71185396aadfa33aeee%26scene%3D21%23wechat_redirect)
- [超越传统网格交易：新型网格交易系统](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488269%26idx%3D1%26sn%3D7b9a60116d5c65278e6894ded1ce79aa%26scene%3D21%23wechat_redirect)
- [JFE | ETF日内套利研究](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488257%26idx%3D1%26sn%3D9eb00eade68c4f6816916330b859adb0%26scene%3D21%23wechat_redirect)
- [NIPS 24 | 超越CVXPY,新型端到端优化器](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247488193%26idx%3D1%26sn%3Da91d10d06dca7a988dda550ccaaa9941%26scene%3D21%23wechat_redirect)
- [揭秘Jane Street低延迟系统的优化技巧——减少系统抖动](https://link.zhihu.com/?target=https%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247487942%26idx%3D1%26sn%3D834867f33667a640961b34756c730ca9%26scene%3D21%23wechat_redirect)
- [南京大学LAMDA-强化学习DRL挖掘逻辑公式型Alpha因子](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484882%26idx%3D1%26sn%3De4fee58dd1ca85b6469e3803be5e97a5%26chksm%3Dce7e62ccf909ebdaa93ae29cef9c59c7f889d784b1c774014b339dc55a375d03443d61b48037%26scene%3D21%23wechat_redirect)
- [3万个因子，数据挖掘能超越同行审议的因子吗？](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484872%26idx%3D1%26sn%3D2f420bd9522473ad83dc6f825c421e5c%26chksm%3Dce7e62d6f909ebc05b45a79d8d6e96cac7910b7509ef168a2a7349f29a4c63dbbf7bb9b3ba11%26scene%3D21%23wechat_redirect)
- [KDD 24 | 基于增强记忆的上下文感知强化学习的高频交易框架](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484852%26idx%3D1%26sn%3D612490637ac96cfa86d829e9ed665c2b%26chksm%3Dce7e62aaf909ebbc864a29a4af3cc6db60eb2930f7dade6882515a61d46222e8877e8018fd07%26scene%3D21%23wechat_redirect)
- [FinRobot：用于金融领域的大模型AI平台](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484560%26idx%3D1%26sn%3D689e9b1ec3bf370e7332b538f3060ca1%26chksm%3Dce7e638ef909ea989847e2b1501d17f9524808ad0544ccceaba918b8fda7c13556522b740647%26scene%3D21%23wechat_redirect)
- [KDD 23 | DoubleAdapt: 显著提升各类模型表现的元学习模型](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484726%26idx%3D1%26sn%3D68a12011fce4197b96d2f67b92f7b5c2%26chksm%3Dce7e6228f909eb3e3ca1504f4b29adc1986cdb1bd451f73049077b864be1999d3b3fdcb860ad%26scene%3D21%23wechat_redirect)
- [市场微观结构教程：深度订单簿预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484660%26idx%3D1%26sn%3Dfc191107da65068ab9a5cd01135a5f1d%26chksm%3Dce7e63eaf909eafcc529fa1a5b07985b5b1e3a548c363134f0cc0ee57a5463ceaf91a2946af0%26scene%3D21%23wechat_redirect)
- [基于高频和日频因子的端到端直接排序组合构建模型](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484549%26idx%3D1%26sn%3D347c69bb297aef162bb364a1e68e9e72%26chksm%3Dce7e639bf909ea8d632046f8f9acac70209067aa1f4c142f3a26733262d298b097041744f92d%26scene%3D21%23wechat_redirect)
- [BOA 312页报告：Everything you wanted to know about quant](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484528%26idx%3D1%26sn%3D01c2c5c1be9c62ee11936badd36aca81%26chksm%3Dce7e636ef909ea7896cac5c96c66a9ec1c2626d68e67fcd52632aea20683643d2191d043f0a8%26scene%3D21%23wechat_redirect)
- [深度学习模型DeepLOB用于订单簿价格预测](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484318%26idx%3D1%26sn%3Dce53c0720707138434d539bf1fd265cc%26chksm%3Dce7e6480f909ed96c06a8a6caae8a38d312b9539364cca2570524f184f68d54783cf35a18b37%26scene%3D21%23wechat_redirect)
- [What KAN I say？KAN代码全解析](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484285%26idx%3D1%26sn%3D14a024ba53e87188e7f4eb5a6658744c%26chksm%3Dce7e6463f909ed75d6c00d19f0e5468b58fa19c8ac5e067bbd84111d4df8213a01b8d2cde5b0%26scene%3D21%23wechat_redirect)
- [取代MLP？MIT全新神经网络结构KAN,3天1.4k star](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484180%26idx%3D1%26sn%3D97c579083e1c9fa93e5c6b0310ddc306%26chksm%3Dce7e640af909ed1cf2718c8db750f10afbca50ab7d93cd4537547d8958db0c305b255a1f7e6d%26scene%3D21%23wechat_redirect)
- [WWW'24 | FinReport: 结合新闻语义信息的多因子模型显著提升预测准确性](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484046%26idx%3D1%26sn%3Dbcb0fff3bdf5f7b44f11200a6618ac01%26chksm%3Dce7e6590f909ec86a6c81cde08dd6cc7f45f40bda780014f9e19fa498b7b1e5f7111c2b28e0b%26scene%3D21%23wechat_redirect)
- [WWW'24 | UniTime: 融合文本信息的时间序列预测模型](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484032%26idx%3D1%26sn%3D604d6ba7bcd2fa070bc73909484b621d%26chksm%3Dce7e659ef909ec880ec0c0c1c9fb685b992e1ac84367e89d736578c665022d0bcf7bc14c7cd8%26scene%3D21%23wechat_redirect)
- [WWW'24 | EarnMore: 如何利用强化学习来处理可定制股票池中的投资组合管理问题](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247483897%26idx%3D1%26sn%3D00d406b6b8475c6e453e8cef837a5733%26chksm%3Dce7e66e7f909eff1a4b6347d4e21f8263962ec99207a3514f5f76f3747a533a2360b4fb7aa0d%26scene%3D21%23wechat_redirect)
- [KDD'23 | AlphaMix: 高效专家混合框架（MoE）显著提高上证50选股表现](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247483915%26idx%3D1%26sn%3D2dc8f2ceffdd225bd3b8ed70385a4a3a%26chksm%3Dce7e6515f909ec03ecdbf9258f1e73972e98229da395c79c7dd533d56455612ab248fc879ff6%26scene%3D21%23wechat_redirect)
- [IJCAI'23 | StockFormer: RL+Self-Attention优化摆动交易提高股票预测精度](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484098%26idx%3D1%26sn%3D40d40326f9a703296115e9720d776f48%26chksm%3Dce7e65dcf909ecca166614ff70d12bdcfb0265b99e8dddfeec75e579a1d3c6e62e5ae9446924%26scene%3D21%23wechat_redirect)
- [AAAI-24 | EarnHFT:针对高频交易的分层强化学习（RL）框架](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247483884%26idx%3D1%26sn%3Db6cde76f0cecd07f19179fce94b67922%26chksm%3Dce7e66f2f909efe4a8e9dcae71358111132135ba8f36bbe40faa5e0a2f42c2291f6ebbe9e4c6%26scene%3D21%23wechat_redirect)
- [AAAI-24 | MASTER 结合市场信息的自动特征选择的股票预测模型，25%年化收益](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247483818%26idx%3D1%26sn%3D8f17951f57c801a612c7d47f3e1c3a77%26chksm%3Dce7e66b4f909efa2a462cb0640427342a98fe733beeb3e275b1625b9e6f72dcd29a5adb196f6%26scene%3D21%23wechat_redirect)
- [COLING 2024 | AlphaFin: 结合深度学习及大模型用于股票预测和金融问答，击败现有预测模型](https://link.zhihu.com/?target=http%3A//mp.weixin.qq.com/s%3F__biz%3DMzg2MzAwNzM0NQ%3D%3D%26mid%3D2247484079%26idx%3D1%26sn%3D8459f251f43c453415a615c353c427d2%26chksm%3Dce7e65b1f909eca7fa00766474ddc207110b158528b6da2f6ec96a91a7fbb66727ea5e2a77f2%26scene%3D21%23wechat_redirect)

发布于 2025-03-13 21:33・IP 属地上海[服务器](https://www.zhihu.com/topic/19554575)[MCP(Model](https://www.zhihu.com/topic/586300002)
