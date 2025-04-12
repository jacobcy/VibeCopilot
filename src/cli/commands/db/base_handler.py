"""
基础Handler类，提供Click命令处理的基础结构
"""
from typing import Any, Dict, Optional

import click


class ClickBaseHandler:
    """Click命令处理器基类"""

    def __init__(self):
        """初始化基础处理器"""
        self.service = None

    def handle(self, **kwargs: Dict[str, Any]) -> Any:
        """
        处理命令的主要方法

        Args:
            **kwargs: 命令参数

        Returns:
            Any: 处理结果

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现handle方法")

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证命令参数

        Args:
            **kwargs: 待验证的参数

        Returns:
            bool: 验证是否通过

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现validate方法")

    def pre_process(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理命令参数

        Args:
            **kwargs: 待处理的参数

        Returns:
            Dict[str, Any]: 处理后的参数
        """
        return kwargs

    def post_process(self, result: Any) -> Any:
        """
        后处理命令结果

        Args:
            result: 处理结果

        Returns:
            Any: 后处理的结果
        """
        return result

    def error_handler(self, error: Exception) -> None:
        """
        统一错误处理

        Args:
            error: 捕获的异常
        """
        click.echo(f"错误: {str(error)}", err=True)

    def execute(self, **kwargs: Dict[str, Any]) -> Any:
        """
        执行命令的主流程

        Args:
            **kwargs: 命令参数

        Returns:
            Any: 执行结果
        """
        try:
            # 参数预处理
            processed_args = self.pre_process(**kwargs)

            # 参数验证
            if not self.validate(**processed_args):
                raise ValueError("参数验证失败")

            # 执行处理
            result = self.handle(**processed_args)

            # 结果后处理
            return self.post_process(result)

        except Exception as e:
            self.error_handler(e)
            raise
