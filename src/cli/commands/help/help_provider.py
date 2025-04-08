#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帮助信息提供者模块

集中管理所有命令的帮助信息，确保帮助信息的一致性
"""

import logging
from typing import Dict, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


class HelpProvider:
    """帮助信息提供者类"""

    _instance = None
    _help_cache: Dict[str, str] = {}

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(HelpProvider, cls).__new__(cls)
        return cls._instance

    def get_command_help(self, command: str, verbose: bool = False) -> str:
        """获取命令的帮助信息"""
        if command == "rule":
            return """[bold cyan]规则管理命令[/]

[bold]用法:[/]
  /rule <子命令> [参数]
  //rule <子命令> [参数]

[bold]子命令:[/]
  [yellow]list[/]        列出所有规则
  [yellow]show[/]        显示规则详情
  [yellow]create[/]      创建新规则
  [yellow]edit[/]        编辑规则
  [yellow]delete[/]      删除规则
  [yellow]enable[/]      启用规则
  [yellow]disable[/]     禁用规则

[bold]选项:[/]
  [yellow]-h, --help[/]               显示帮助信息
  [yellow]-t, --type[/] <type>        规则类型 (core/dev/tech/tool)
  [yellow]-d, --desc[/] <desc>        规则描述
  [yellow]-p, --priority[/] <num>     规则优先级 (1-100)
  [yellow]-f, --force[/]              强制执行操作

[bold]示例:[/]
  # 列出所有规则
  [dim]/rule list[/]
  [dim]//rule list --type core[/]

  # 显示规则详情
  [dim]/rule show dev-rules/flow[/]

  # 创建新规则
  [dim]/rule create my-rule --type dev --desc "我的规则"[/]"""
        cache_key = f"{command}_{verbose}"
        if cache_key in self._help_cache:
            return self._help_cache[cache_key]

        help_method = getattr(self, f"_get_{command}_command_help", None)
        if help_method:
            help_text = help_method(verbose)
            self._help_cache[cache_key] = help_text
            return help_text
        return None

    def _get_rule_command_help(self, verbose: bool = False) -> str:
        """获取rule命令的帮助信息"""
        base_help = """
[bold]用法:[/bold]
```bash
/rule <子命令> [参数]
//rule <子命令> [参数]
```

[bold]子命令:[/bold]
[yellow]list[/yellow]     列出所有规则
[yellow]show[/yellow]     显示规则详情
[yellow]create[/yellow]   创建新规则
[yellow]edit[/yellow]     编辑规则
[yellow]delete[/yellow]   删除规则
[yellow]enable[/yellow]   启用规则
[yellow]disable[/yellow]  禁用规则

[bold]选项:[/bold]
[yellow]-h, --help[/yellow]              显示帮助信息
[yellow]-t, --type[/yellow] <type>       规则类型 (core/dev/tech/tool)
[yellow]-d, --desc[/yellow] <desc>       规则描述
[yellow]-p, --priority[/yellow] <num>    规则优先级 (1-100)
[yellow]-f, --force[/yellow]             强制执行操作

[bold]示例:[/bold]
```bash
# 列出所有规则
/rule list
//rule list --type core

# 显示规则详情
/rule show dev-rules/flow
//rule show tech-rules/frontend

# 创建新规则
/rule create my-rule --type dev --desc "我的规则"
//rule create my-rule -t dev -d "我的规则" -p 50

# 编辑和删除规则
/rule edit my-rule
//rule delete my-rule --force
```
"""
        if not verbose:
            return base_help

        # 详细帮助信息
        verbose_help = (
            base_help
            + """
[bold]详细说明:[/bold]

1. 规则类型:
   - core: 核心规则
   - dev: 开发规则
   - tech: 技术规则
   - tool: 工具规则

2. 规则优先级:
   - 1-100的整数
   - 数字越大优先级越高
   - 默认为50

3. 规则状态:
   - 启用: 规则正常生效
   - 禁用: 规则暂时停用

4. 规则文件格式:
   - 使用Markdown格式
   - 支持Front Matter
   - 支持代码块和表格

5. 注意事项:
   - 删除操作不可逆
   - 编辑会打开默认编辑器
   - 规则名称不能重复
"""
        )
        return verbose_help

    # 其他命令的帮助信息方法...
