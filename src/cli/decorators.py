#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI装饰器模块

提供用于CLI命令的装饰器工具，主要用于依赖注入和服务管理。
"""

from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

import click
from rich.console import Console
from typing_extensions import ParamSpec

from src.services.service_factory import ServiceFactory

P = ParamSpec("P")
R = TypeVar("R")

console = Console()


def friendly_error_handling(f: Callable[P, R]) -> Callable[P, R]:
    """
    装饰器: 友好的错误处理

    捕获命令执行过程中的异常，并以友好的方式展示给用户。
    支持以下功能：
    1. 捕获常见异常并转换为友好消息
    2. 使用rich库美化输出
    3. 在verbose模式下显示详细错误信息

    Args:
        f: 被装饰的函数

    Returns:
        装饰后的函数，提供友好的错误处理

    Examples:
        ```python
        @click.command()
        @friendly_error_handling
        def some_command():
            # 可能抛出异常的代码
            do_something_risky()
        ```
    """

    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return f(*args, **kwargs)
        except click.ClickException:
            # Click的异常直接抛出，因为它们已经格式化好了
            raise
        except Exception as e:
            # 获取verbose参数，如果存在的话
            verbose = kwargs.get("verbose", False)

            # 错误消息
            error_msg = str(e)

            # 在verbose模式下显示更多信息
            if verbose:
                import traceback

                console.print("[bold red]错误详情:[/bold red]")
                console.print(traceback.format_exc())
            else:
                console.print(f"[red]错误: {error_msg}[/red]")
                console.print("[blue]提示: 使用 --verbose 参数查看详细错误信息[/blue]")

            # 返回错误状态码
            return 1

    return cast(Callable[P, R], wrapper)


def pass_service(f: Optional[Callable[P, R]] = None, *, service_type: str = "roadmap") -> Callable[P, R]:
    """
    装饰器: 注入服务实例到CLI命令

    此装饰器会自动创建并注入指定类型的服务实例到命令函数中。
    服务实例通过ServiceFactory创建，并存储在Click的上下文中以便重用。

    Args:
        f: 被装饰的函数
        service_type: 服务类型，默认为"roadmap"

    Returns:
        装饰后的函数，其service参数会被自动注入服务实例

    Examples:
        ```python
        @click.command()
        @pass_service(service_type="db")
        def db_command(service: DatabaseService):
            service.do_something()

        # 也可以不指定service_type，使用默认值
        @click.command()
        @pass_service
        def roadmap_command(service: RoadmapService):
            service.do_something()
        ```
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            ctx = click.get_current_context()
            if not hasattr(ctx, "service_factory"):
                ctx.service_factory = ServiceFactory()

            # 获取verbose参数值，如果存在的话
            verbose = kwargs.get("verbose", False)

            # 创建服务实例并注入
            service = ctx.service_factory.create_service(service_type, verbose=verbose)
            return func(*args, service=service, **kwargs)

        return cast(Callable[P, R], wrapper)

    # 支持@pass_service和@pass_service(service_type="db")两种用法
    if f is None:
        return decorator
    return decorator(f)
