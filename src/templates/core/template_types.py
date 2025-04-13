"""
模板系统类型定义
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union


@dataclass
class TemplateData:
    """模板数据类型"""

    name: str
    path: str
    type: str  # 'file' or 'directory'
    metadata: Optional[Dict] = None
    variables: Optional[Dict] = None


@dataclass
class TemplateConfig:
    """模板配置类型"""

    name: str
    description: str
    version: str
    author: Optional[str] = None
    variables: Optional[Dict] = None
    dependencies: Optional[List[str]] = None
    tags: Optional[List[str]] = None
