"""
控制台输出工具函数

提供终端彩色输出和格式化消息显示。
"""

import traceback


def colorize(text, color="red", style="bold"):
    """为终端输出添加颜色

    颜色选项: red, green, yellow, blue, magenta, cyan, white
    样式选项: bold, dim, italic, underline, blink, reverse
    """
    colors = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
    }

    styles = {"bold": "\033[1m", "dim": "\033[2m", "italic": "\033[3m", "underline": "\033[4m", "blink": "\033[5m", "reverse": "\033[7m"}

    reset = "\033[0m"

    color_code = colors.get(color, "")
    style_code = styles.get(style, "")

    return f"{style_code}{color_code}{text}{reset}"


def print_error(message, error=None, show_traceback=False):
    """以醒目的方式显示错误信息"""
    print("\n" + colorize("❌ 错误", "red", "bold") + colorize(f": {message}", "red"))

    if error:
        print(colorize(f"  详细信息: {str(error)}", "red"))

    if show_traceback and error:
        print(colorize("\n错误追踪:", "yellow", "bold"))
        print(colorize("".join(traceback.format_exception(type(error), error, error.__traceback__)), "yellow"))


def print_success(message):
    """以醒目的方式显示成功信息"""
    print(colorize("✅ ", "green") + colorize(message, "green"))
