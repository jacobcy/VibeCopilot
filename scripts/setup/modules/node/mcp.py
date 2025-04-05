#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP服务器相关功能模块，检查和配置MCP服务器环境。
"""

from pathlib import Path

from ..common import IS_WINDOWS, PROJECT_ROOT, run_command


def check_uvx() -> tuple[bool, str]:
    """检查uvx是否已安装."""
    try:
        cmd = ["which", "uvx"] if not IS_WINDOWS else ["where", "uvx"]
        returncode, output = run_command(cmd)
        if returncode == 0:
            returncode, uvx_version = run_command(["uvx", "--version"])
            if returncode == 0:
                return True, uvx_version.strip()
            return True, "已安装，但无法获取版本"
        return False, "未找到uvx"
    except Exception:
        return False, "uvx未安装"


def install_uvx() -> bool:
    """安装uvx工具."""
    print("正在安装uvx...")

    # uvx通常通过npm安装
    returncode, output = run_command(["npm", "install", "-g", "@uvx/cli"])
    if returncode != 0:
        print(f"安装uvx失败: {output}")
        return False

    print("uvx安装成功")
    return True


def check_mcp_servers() -> None:
    """检查MCP服务器的可用性和现有配置."""
    print("\n---- MCP服务器检查 ----")

    # 检查基本工具
    npx_available = False
    uvx_available = False

    try:
        returncode, _ = run_command(["npx", "--version"])
        npx_available = returncode == 0
    except Exception:
        pass

    uvx_ok, uvx_version = check_uvx()
    uvx_available = uvx_ok

    # 输出结果
    if npx_available:
        print("✅ npx可用 - 可以使用@modelcontextprotocol/server-*服务器")
    else:
        print("❌ npx不可用 - 无法使用@modelcontextprotocol/server-*服务器")
        print("  建议安装npm: brew install node (macOS) 或 apt install npm (Linux)")

    if uvx_available:
        print(f"✅ uvx可用({uvx_version}) - 可以使用@uvx/*服务器")
    else:
        print("❌ uvx不可用 - 无法使用@uvx/*服务器")
        print("  uvx是临时执行工具，可以通过 npm install -g @uvx/cli 安装")

    # 提供使用说明
    print("\nMCP服务器是临时执行工具，使用示例:")
    print("  npx -y @modelcontextprotocol/server-filesystem ~/project")
    print("  uvx mcp-server-time --local-timezone Asia/Shanghai")
    print("  uvx basic-memory mcp --project ProjectName")
    print("  uvx mcp-server-git --repository ~/project")

    # 检查项目中的现有mcp.json文件
    mcp_json_path = PROJECT_ROOT / ".cursor" / "mcp.json"
    if mcp_json_path.exists():
        print(f"\n发现现有MCP配置文件: {mcp_json_path}")

        # 检查配置内容
        try:
            import json

            with open(mcp_json_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            servers = config.get("mcpServers", {})
            server_names = list(servers.keys())

            if server_names:
                print(f"配置文件包含以下服务器: {', '.join(server_names)}")
                print("✅ 配置文件格式正确")
            else:
                print("⚠️ 配置文件不包含任何服务器")

        except Exception as e:
            print(f"⚠️ 无法解析配置文件: {e}")
            print("请确保.cursor/mcp.json格式正确且包含必要的服务器配置")
    else:
        print(f"\n⚠️ 未找到MCP配置文件: {mcp_json_path}")
        print("请创建配置文件并添加所需的MCP服务器:")
        print("1. 在项目根目录创建 .cursor/mcp.json 文件")
        print("2. 添加所需的服务器配置，例如filesystem, sequential-thinking, time等")
        print("3. 确保配置正确的命令和参数")
        print("\n配置示例:")
        print(
            """
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/project/path"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "time": {
      "command": "uvx",
      "args": ["mcp-server-time", "--local-timezone", "Asia/Shanghai"]
    },
    "basic-memory": {
      "command": "uvx",
      "args": ["basic-memory", "mcp", "--project", "ProjectName", "--verbose"]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "~/project/path"]
    }
  }
}
        """
        )
