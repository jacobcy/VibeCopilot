"""
命令处理器基类

提供命令处理的基础功能和接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseCommand(ABC):
    """命令处理器基类"""

    def __init__(self, name: str, description: str):
        """初始化命令

        Args:
            name: 命令名称
            description: 命令描述
        """
        self.name = name
        self.description = description
        self.required_args = []  # 必需参数列表
        self.optional_args = {}  # 可选参数和默认值

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行命令

        Args:
            args: 命令参数字典

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 验证参数
            if not self.validate_args(args):
                missing = [arg for arg in self.required_args if arg not in args]
                return {
                    "success": False,
                    "error": f"缺少必需参数: {', '.join(missing)}",
                    "help": self.get_usage(),
                }

            # 处理默认参数
            for arg, default in self.optional_args.items():
                if arg not in args:
                    args[arg] = default

            # 执行具体命令逻辑
            result = self._execute_impl(args)
            return self.format_response(result)
        except Exception as e:
            return {"success": False, "error": str(e), "error_type": type(e).__name__}

    @abstractmethod
    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """命令执行的具体实现

        Args:
            args: 命令参数字典

        Returns:
            Dict[str, Any]: 执行结果数据
        """
        pass

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """验证参数是否满足要求

        Args:
            args: 命令参数字典

        Returns:
            bool: 验证结果
        """
        # 检查必需参数是否都存在
        for required_arg in self.required_args:
            if required_arg not in args:
                return False
        return True

    def format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化响应

        Args:
            data: 执行结果数据

        Returns:
            Dict[str, Any]: 格式化后的响应
        """
        return {"success": True, "command": self.name, "data": data}

    def get_usage(self) -> str:
        """获取命令用法

        Returns:
            str: 命令用法字符串
        """
        usage = f"/{self.name}"

        # 添加必需参数
        for arg in self.required_args:
            usage += f" --{arg}=<{arg}>"

        # 添加可选参数
        for arg, default in self.optional_args.items():
            if isinstance(default, bool) and default is False:
                usage += f" [--{arg}]"
            else:
                usage += f" [--{arg}=<{arg}>]"

        return usage

    def get_examples(self) -> List[Dict[str, str]]:
        """获取命令示例

        Returns:
            List[Dict[str, str]]: 命令示例列表
        """
        # 基类提供一个简单的示例，子类可以覆盖此方法提供更具体的示例
        return [{"description": "基本用法", "command": self.get_usage()}]

    def register_args(self, required: List[str] = None, optional: Dict[str, Any] = None):
        """注册命令参数

        Args:
            required: 必需参数列表
            optional: 可选参数及其默认值
        """
        if required:
            self.required_args = required
        if optional:
            self.optional_args = optional
