"""
控制台输出工具函数

提供终端彩色输出和格式化消息显示。
"""

import traceback

# Import the standardized console utility functions
from src.utils.console_utils import print_error as standard_print_error
from src.utils.console_utils import print_success as standard_print_success

# The colorize function is no longer needed as rich handles styling
# def colorize(text, color="red", style="bold"):
#     ...


def print_error(message, error=None, show_traceback=False):
    """以醒目的方式显示错误信息 (兼容层)

    现在调用 src.utils.console_utils.print_error
    """
    error_details = f"{message}"
    if error:
        error_details += f"\n详细信息: {str(error)}"

    if show_traceback and error:
        tb_string = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        error_details += f"\n\n错误追踪:\n{tb_string}"

    standard_print_error(error_details)


def print_success(message):
    """以醒目的方式显示成功信息 (兼容层)

    现在调用 src.utils.console_utils.print_success
    """
    standard_print_success(message)


# Remove the old colorize function definition
