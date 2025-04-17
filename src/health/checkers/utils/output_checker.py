"""
用于执行命令输出内容检查的核心逻辑。
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

# Define the signature for the command execution function
RunCommandFunc = Callable[[str], Tuple[int, str, str]]


def perform_output_check(
    run_command_func: RunCommandFunc,
    cmd_name: str,
    subcmd_name: str,
    subcmd_config: Dict[str, Any],
    cmd_prefix: str,
    logger: logging.Logger,
    verbose: bool = False,
) -> Dict:
    """检查命令的输出内容。

    Args:
        run_command_func: 用于执行命令的函数。
        cmd_name: 主命令名称。
        subcmd_name: 子命令名称。
        subcmd_config: 子命令的YAML配置。
        cmd_prefix: 命令前缀。
        logger: 日志记录器实例。
        verbose: 是否启用详细输出。

    Returns:
        一个包含检查结果的字典。
    """
    check_result = {"name": f"命令输出检查: {cmd_name} {subcmd_name}", "status": "passed", "details": [], "suggestions": []}

    # 获取验证配置
    validation = subcmd_config.get("validation", {})

    # 如果没有验证配置，直接返回通过
    if not validation:
        logger.debug(f"命令 '{cmd_name} {subcmd_name}' 无输出验证配置，跳过检查。")
        return check_result

    # 构建基本命令
    test_cmd = f"{cmd_prefix} {cmd_name} {subcmd_name}"

    # 添加必要参数 (根据 validation 配置)
    if validation.get("required_parameters"):
        parameters_config = subcmd_config.get("parameters", {})  # Get parameters from subcmd_config
        for param_name in validation["required_parameters"]:
            param_config = parameters_config.get(param_name, {})  # Get specific param config
            # 如果参数有选项，使用第一个选项作为测试值
            if param_config.get("options"):
                test_cmd += f" {param_name}={param_config['options'][0]}"
            # 否则使用一个默认测试值
            else:
                # Need a better default based on type, but 'test' is placeholder
                test_cmd += f" {param_name}=test"

    # 运行命令
    logger.debug(f"执行输出检查命令: {test_cmd}")
    code, stdout, stderr = run_command_func(test_cmd)
    output = stdout + stderr

    if verbose:
        logger.debug(f"检查命令 '{cmd_name} {subcmd_name}' 的输出")
        logger.debug(f"完整命令: {test_cmd}")
        logger.debug(f"返回码: {code}")
        logger.debug(f"输出长度: {len(output)} 字符")

    # 检查返回码
    if code != 0:
        check_result["status"] = "failed"
        check_result["details"].append(f"命令 '{test_cmd}' 执行失败，返回码: {code}")
        if stderr:
            check_result["details"].append(f"错误输出(前200字符): {stderr[:200]}")
        check_result["suggestions"].append("检查命令实现，确保可以正常执行")
        return check_result

    # 检查输出是否为空
    if not output.strip():
        check_result["status"] = "warning"  # Or failed, depending on strictness needed
        check_result["details"].append(f"命令 '{test_cmd}' 输出为空。")
        check_result["suggestions"].append("检查命令实现，确保命令有有效输出（如果预期有输出）。")
        # Decide if empty output should stop further checks
        # return check_result # Uncomment if empty output is a hard fail

    # 检查必须包含的输出关键词
    if validation.get("required_output"):
        for keyword in validation["required_output"]:
            if keyword.lower() not in output.lower():
                if check_result["status"] == "passed":
                    check_result["status"] = "warning"
                check_result["details"].append(f"命令 '{test_cmd}' 输出缺少关键信息: {keyword}")
                check_result["suggestions"].append(f"确保命令输出包含关键词: {keyword}")

    # 检查输出最小长度
    min_length = validation.get("min_output_length", 0)
    if len(output) < min_length:
        if check_result["status"] == "passed":
            check_result["status"] = "warning"
        check_result["details"].append(f"命令 '{test_cmd}' 输出过短 (长度 {len(output)}，要求最小 {min_length})。")
        check_result["suggestions"].append(f"确保命令输出内容足够丰富，至少达到{min_length}字符。")

    # Final status adjustment (already handled by setting status above)
    # if check_result["details"] and check_result["status"] == "passed":
    #      check_result["status"] = "warning"

    return check_result
