"""用于解析命令帮助文本的工具函数"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_help_usage(usage_line: str) -> List[str]:
    """从 Usage 行解析位置参数名称.

    Args:
        usage_line: 帮助文本中的Usage行

    Returns:
        位置参数名称列表
    """
    # Example: Usage: vibecopilot task update [OPTIONS] TASK_ID
    # Regex to find uppercase words (arguments) after OPTIONS or command name
    match = re.search(r"Usage:.*? (?:\[OPTIONS\])?(.*)", usage_line)
    if not match:
        return []

    # Find all uppercase words, assuming they are args
    # Convert to snake_case for comparison
    args = [arg.lower() for arg in re.findall(r"\b[A-Z_]{2,}\b", match.group(1))]
    logger.debug(f"[parse_help_usage] 从Usage解析出的参数: {args}")
    return args


def parse_help_options(options_section: str) -> Dict[str, Optional[str]]:
    """从 Options 部分解析选项名称 (长格式和短格式).

    Args:
        options_section: 帮助文本中的Options部分

    Returns:
        选项映射字典，键为长格式名称，值为短格式名称
    """
    logger.debug(f"[parse_help_options] 开始解析 Options section (前 200 字符):\n{options_section[:200]}...")
    options = {}
    # Regex to capture short (-x), long (--option), or only long (--option)
    # Allows for optional type hints like TEXT, INTEGER after the option name
    # --- MODIFIED REGEX: Make the part after the option name more lenient ---
    # pattern = re.compile(r"^\\s+(-([a-zA-Z]),\\s+)?(--\\w[\\w-]*)(?:\\s+[A-Z_\\[\\]\\|]+)?")
    pattern = re.compile(r"^\\s+(-([a-zA-Z]),\\s+)?(--\\w[\\w-]*)(?:\\s+.*)?")

    lines = options_section.splitlines()
    logger.debug(f"[parse_help_options] 共 {len(lines)} 行需要处理")

    for i, line in enumerate(lines):
        line = line.rstrip()  # Remove trailing whitespace
        if not line.strip():  # Skip empty lines
            continue

        # logger.debug(f"[parse_help_options] 处理行 {i+1}/{len(lines)}: '{line}'") # Reduced verbosity
        match = pattern.match(line)
        if match:
            short_name = f"-{match.group(2)}" if match.group(2) else None
            long_name = match.group(3)
            # logger.debug(f"[parse_help_options]  -> 匹配成功: long='{long_name}', short='{short_name}'") # Reduced verbosity
            # Store long name as key, short name as value
            options[long_name] = short_name
        else:
            # Add logging for lines that *don't* match the pattern
            # Avoid logging the initial 'Options:' header line if it exists and doesn't match
            if not (line.strip().lower().startswith("options:") or line.strip().lower().startswith("arguments:")):
                logger.debug(f"[parse_help_options]  -> 未匹配到选项格式 (行 {i+1}): '{line}'")

    # Add implicit --help option if not found and if any options were parsed
    # Only add implicit help if options were actually found, otherwise it might be an empty/invalid section
    if options and "--help" not in options:
        logger.debug("[parse_help_options] 未找到显式 --help，添加隐式 '-h'.")
        options["--help"] = "-h"

    logger.debug(f"[parse_help_options] 解析完成，返回 options: {options}")
    return options
