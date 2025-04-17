"""
用于执行外部命令并处理超时的工具函数。
"""

import logging
import subprocess
from typing import Tuple


def run_command_with_timeout(command: str, timeout: int, logger: logging.Logger, verbose: bool = False) -> Tuple[int, str, str]:
    """运行命令并返回结果，包含超时处理。

    Args:
        command: 要执行的命令字符串。
        timeout: 超时时间（秒）。
        logger: 日志记录器实例。
        verbose: 是否启用详细输出。

    Returns:
        一个元组 (return_code, stdout_text, stderr_text)。
        如果超时，return_code 为 -1，stderr_text 为超时信息。
        如果发生其他异常，return_code 为 -1，stderr_text 为异常信息。
    """
    stdout_text = ""
    stderr_text = ""
    try:
        if verbose:
            logger.debug(f"执行命令: {command}")

        # 使用 shell=True 确保命令能在当前环境中正确执行
        # 注意：如果命令来自不可信来源，shell=True 可能有安全风险
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Decode stdout/stderr as text using default encoding
            errors="replace",  # Replace decoding errors
        )

        stdout_text, stderr_text = process.communicate(timeout=timeout)
        return_code = process.returncode

        if verbose:
            logger.debug(f"命令返回码: {return_code}")
            if stdout_text:
                # 使用日志截断，避免过长输出 (保持与CommandChecker一致)
                logger.debug(f"标准输出: {stdout_text[:150].rstrip()}...")
            if stderr_text:
                logger.debug(f"错误输出: {stderr_text[:150].rstrip()}...")

        return return_code, stdout_text, stderr_text

    except subprocess.TimeoutExpired:
        error_msg = f"命令执行超时 (>{timeout}s): {command}"
        logger.warning(error_msg)
        # 确保在超时时返回错误信息
        if process:  # type: ignore
            process.kill()  # 尝试终止进程
            # 读取残留的输出（可能不完整）
            try:
                stdout_text, stderr_text = process.communicate()
            except:  # Ignore further errors during cleanup
                pass
        return -1, stdout_text, error_msg  # 返回超时信息到 stderr

    except Exception as e:
        error_msg = f"执行命令时出错 '{command}': {e}"
        logger.error(error_msg, exc_info=verbose)  # Log traceback if verbose
        return -1, stdout_text, str(e)  # 返回异常信息到 stderr
