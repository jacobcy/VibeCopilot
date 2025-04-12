"""
工作流命令模块 (Click 版本) - 兼容层

此文件作为兼容层保留，仅导入新的模块化结构中的内容。
在确认所有代码都已迁移到新结构后，此文件将在未来版本中移除。

!!! 已弃用 !!!
此文件已被拆分为多个较小的文件，位于 src/cli/commands/flow/commands/ 目录中。
请直接使用新的模块化结构:
    from src.cli.commands.flow.commands import flow
"""

import logging

# 从新的模块化结构导入
from src.cli.commands.flow.commands import flow

# 设置兼容性警告
logger = logging.getLogger(__name__)
logger.debug("从 flow_click.py 导入已被弃用。请使用 'from src.cli.commands.flow.commands import flow'。" "此兼容层将在将来的版本中移除。")

# 导出与以前相同的接口
__all__ = ["flow"]
