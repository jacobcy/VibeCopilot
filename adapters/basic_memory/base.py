"""
Basic Memory基础类定义
包含解析器、导出器的基类和接口
"""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Union

from adapters.basic_memory.config import get_config


class BaseParser(ABC):
    """基础解析器抽象类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化解析器

        Args:
            config: 解析器配置
        """
        self.config = get_config("parser", config)

    @abstractmethod
    def parse(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """解析文本内容

        Args:
            content: 要解析的文本内容
            metadata: 文档元数据

        Returns:
            Dict: 解析结果
        """
        pass

    @abstractmethod
    def parse_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """解析文件

        Args:
            file_path: 文件路径

        Returns:
            Dict: 解析结果
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取基本元数据
        metadata = {
            "filename": path.name,
            "file_path": str(path.absolute()),
            "file_size": path.stat().st_size,
            "file_type": path.suffix.lower(),
            "created_at": path.stat().st_ctime,
            "modified_at": path.stat().st_mtime,
        }

        return self.parse(content, metadata)


class BaseExporter(ABC):
    """基础导出器抽象类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化导出器

        Args:
            config: 导出器配置
        """
        self.config = get_config("obsidian", config)

    @abstractmethod
    def export(self, data: Dict[str, Any], output_path: Union[str, Path, TextIO]) -> None:
        """导出数据

        Args:
            data: 要导出的数据
            output_path: 输出路径或文件对象
        """
        pass

    def save_json(self, data: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """保存数据为JSON文件

        Args:
            data: 要保存的数据
            output_path: 输出路径
        """
        path = Path(output_path) if isinstance(output_path, str) else output_path

        # 确保父目录存在
        os.makedirs(path.parent, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_json(self, input_path: Union[str, Path]) -> Dict[str, Any]:
        """从JSON文件加载数据

        Args:
            input_path: 输入文件路径

        Returns:
            Dict: 加载的数据
        """
        path = Path(input_path) if isinstance(input_path, str) else input_path

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
