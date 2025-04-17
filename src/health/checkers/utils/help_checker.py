"""
用于执行命令帮助信息检查的核心逻辑。
"""

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

# Define the signature for the command execution function
RunCommandFunc = Callable[[str], Tuple[int, str, str]]
# Define signatures for parsing functions
ParseUsageFunc = Callable[[str], List[str]]
ParseOptionsFunc = Callable[[str], Dict[str, Optional[str]]]


# --- Basic Help Format Check ---
def check_basic_help_format(help_text: str) -> Tuple[bool, List[str]]:
    """检查帮助文本是否符合最基本的格式规范。

    规范包括:
    1. 包含 Usage: 行 (忽略大小写)
    2. 包含 Options: 行 (忽略大小写) 或至少一个选项样式的行。

    Args:
        help_text: 命令的 --help 输出文本。

    Returns:
        一个元组 (is_valid, error_details)。
        is_valid 为 True 表示符合规范，False 表示不符合。
        error_details 包含具体的格式错误信息（如果不符合规范）。
    """
    errors = []
    is_valid = True

    # 1. Check for Usage: line
    usage_pattern = r"^\s*Usage:.*$"
    if not re.search(usage_pattern, help_text, re.MULTILINE | re.IGNORECASE):
        errors.append("帮助文本缺少 'Usage:' 行。")
        is_valid = False

    # 2. Check for Options: line OR option-like lines
    options_header_pattern = r"^\s*Options:.*$"
    option_line_pattern = r"^\s+(-|--)\w"
    has_options_info = False
    if re.search(options_header_pattern, help_text, re.MULTILINE | re.IGNORECASE):
        has_options_info = True
    elif re.search(option_line_pattern, help_text, re.MULTILINE):
        has_options_info = True

    if not has_options_info:
        errors.append("帮助文本缺少 'Options:' 部分或有效的选项定义行 (例如，以'-'或'--'开头的行)。")
        is_valid = False

    return is_valid, errors


def perform_help_check(
    run_command_func: RunCommandFunc,
    parse_usage_func: ParseUsageFunc,
    parse_options_func: ParseOptionsFunc,
    cmd_name: str,
    cmd_config: Dict[str, Any],
    cmd_prefix: str,
    logger: logging.Logger,
    verbose: bool = False,
) -> Dict:
    """执行命令帮助信息的详细检查。

    Args:
        run_command_func: 用于执行命令的函数。
        parse_usage_func: 用于解析Usage行的函数。
        parse_options_func: 用于解析Options部分的函数。
        cmd_name: 要检查的命令名称。
        cmd_config: 该命令在YAML中的配置。
        cmd_prefix: 命令前缀 (例如 'vibecopilot').
        logger: 日志记录器实例。
        verbose: 是否启用详细输出。

    Returns:
        一个包含检查结果的字典，details 字段会包含更详细的执行上下文。
    """
    check_result = {"name": f"命令帮助检查: {cmd_name}", "status": "passed", "details": [], "suggestions": []}

    help_cmd = f"{cmd_prefix} {cmd_name} --help"
    code, stdout, stderr = run_command_func(help_cmd)
    output = stdout + stderr

    if verbose:
        logger.debug(f"--- Help Output for {cmd_name} ---")
        logger.debug(output)
        logger.debug("--- End Help Output ---")

    # Basic checks (execution, output presence)
    if code != 0 or not output.strip():
        check_result["status"] = "failed"
        # 添加更详细的执行信息到 details
        check_result["details"].append(f"命令执行失败: '{help_cmd}'")
        check_result["details"].append(f"返回码: {code}")
        if not output.strip():
            check_result["details"].append("命令无输出")
        if stderr:
            check_result["details"].append(f"错误输出(前200字符): {stderr[:200]}")
        check_result["suggestions"].append("检查命令实现和其 --help 输出.")
        return check_result

    # Parameter Consistency Check
    yaml_args = {arg["name"]: arg for arg in cmd_config.get("arguments", [])}
    yaml_opts = cmd_config.get("options", {})

    usage_section = ""
    options_section = ""
    parsing_error = False
    try:
        # --- Extract Usage Section ---
        usage_pattern = r"^\s*Usage:\s*(.*)$"
        usage_match = re.search(usage_pattern, output, re.MULTILINE | re.IGNORECASE)
        if usage_match:
            usage_section = usage_match.group(1)
            if verbose:
                logger.debug(f"提取到 Usage section: {usage_section[:150]}...")  # Show more context
        else:
            logger.warning(f"({cmd_name}) 未找到 Usage: 行。")
            # Add warning detail to the report
            check_result["details"].append("无法从帮助输出中解析 Usage 行。")
            check_result["status"] = "warning"

        # --- Extract Options Section ---
        options_pattern = r"^\s*Options:\s*?\n(.*?)(?:^\s*\w|\Z)"
        options_match = re.search(options_pattern, output, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if options_match:
            options_section = options_match.group(1).strip()
            if verbose:
                logger.debug(f"提取到 Options section: {options_section[:150]}...")  # Show more context
        else:
            logger.warning(f"({cmd_name}) 未找到 'Options:' header。尝试 fallback 策略。")
            fallback_pattern = r"^(\s+(-|--)\S+.*)"
            first_option_match = re.search(fallback_pattern, output, re.MULTILINE)
            if first_option_match:
                options_section = output[first_option_match.start() :].strip()
                logger.info(f"({cmd_name}) Fallback 成功: 从第一个选项开始提取。")
                if verbose:
                    logger.debug(f"Fallback 提取到 Options section: {options_section[:150]}...")
            else:
                logger.warning(f"({cmd_name}) 无法提取 Options 部分。")
                # Add warning detail to the report
                check_result["details"].append("无法从帮助输出中解析 Options 部分（header 或 fallback 均失败）。")
                check_result["status"] = "warning"
                parsing_error = True  # Mark that options parsing failed

    except Exception as e:
        error_msg = f"解析帮助文本时发生意外错误: {e}"
        logger.error(f"({cmd_name}) {error_msg}", exc_info=verbose)
        check_result["status"] = "failed"
        check_result["details"].append(error_msg)
        check_result["suggestions"].append("检查日志以获取详细的回溯信息。")
        parsing_error = True
        # Sections might be partially populated, keep them as they are
        usage_section = usage_section or ""
        options_section = options_section or ""

    # Call parsing functions
    # Only parse if no fatal error occurred during section extraction
    help_args_parsed = []
    if usage_section:
        try:
            help_args_parsed = parse_usage_func(usage_section)
        except Exception as e:
            logger.error(f"({cmd_name}) 调用 parse_usage_func 时出错: {e}", exc_info=verbose)
            check_result["details"].append(f"解析Usage内容时出错: {e}")
            check_result["status"] = "failed"
            parsing_error = True

    help_opts_parsed = {}
    if options_section:
        try:
            help_opts_parsed = parse_options_func(options_section)
        except Exception as e:
            logger.error(f"({cmd_name}) 调用 parse_options_func 时出错: {e}", exc_info=verbose)
            check_result["details"].append(f"解析Options内容时出错: {e}")
            check_result["status"] = "failed"
            parsing_error = True

    # --- Comparisons --- (Skip if parsing failed catastrophically)
    if not parsing_error:
        # 1. Compare Arguments (YAML vs Help Usage) - SKIPPING THIS CHECK AS REQUESTED
        # yaml_arg_names = set(yaml_args.keys())
        # help_arg_names = set(help_args_parsed)
        # missing_in_help_args = yaml_arg_names - help_arg_names
        # missing_in_yaml_args = help_arg_names - yaml_arg_names
        #
        # if missing_in_help_args:
        #     if check_result["status"] == "passed": check_result["status"] = "warning"
        #     check_result["details"].append(f"参数不匹配: YAML中的 {missing_in_help_args} 未在帮助Usage中找到。")
        #     check_result["suggestions"].append("检查命令实现或更新YAML中的 arguments.")
        # if missing_in_yaml_args:
        #     if check_result["status"] == "passed": check_result["status"] = "warning"
        #     check_result["details"].append(f"参数不匹配: 帮助Usage中的 {missing_in_yaml_args} 未在YAML中定义。")
        #     check_result["suggestions"].append("在YAML的 arguments 中添加缺失的参数定义.")

        # 2. Compare Options (YAML vs Help Options)
        yaml_opt_names = set(yaml_opts.keys())
        help_opt_names = set(help_opts_parsed.keys()) - {"--help"}
        missing_in_help_opts = yaml_opt_names - help_opt_names
        missing_in_yaml_opts = help_opt_names - yaml_opt_names

        if missing_in_help_opts:
            if check_result["status"] == "passed":
                check_result["status"] = "warning"
            # --- REVERTED REPORTING to simple warning ---
            check_result["details"].append(f"选项不匹配(传统方法): YAML中的 {missing_in_help_opts} 未在帮助Options中找到。")
            # Keep original suggestion about checking implementation/YAML
            check_result["suggestions"].append("检查命令实现或更新YAML中的 options.")

        # Keep the check for options present in help but missing in YAML
        if missing_in_yaml_opts:
            if check_result["status"] == "passed":
                check_result["status"] = "warning"
            check_result["details"].append(f"选项不匹配: 帮助Options中的 {missing_in_yaml_opts} 未在YAML中定义。")
            check_result["suggestions"].append("在YAML的 options 中添加缺失的选项定义.")

        # 3. Compare Option Short Names
        short_name_mismatches = []
        for opt_name, opt_config in yaml_opts.items():
            yaml_short = opt_config.get("short")
            if opt_name in help_opts_parsed:
                help_short = help_opts_parsed[opt_name]
                if yaml_short != help_short:
                    if yaml_short or help_short:
                        short_name_mismatches.append(f"{opt_name} (YAML: '{yaml_short}', Help: '{help_short}')")
            elif opt_name not in help_opt_names and yaml_short:
                pass  # Already covered by missing_in_help_opts

        if short_name_mismatches:
            if check_result["status"] == "passed":
                check_result["status"] = "warning"
            check_result["details"].append(f"选项简写不匹配: {short_name_mismatches}")
            check_result["suggestions"].append("统一YAML和命令实现中的选项简写.")

    # Final status adjustment - if details were added but status remained 'passed', set to 'warning'
    # This handles cases where only parsing warnings occurred without mismatches
    if check_result["details"] and check_result["status"] == "passed":
        check_result["status"] = "warning"

    return check_result
