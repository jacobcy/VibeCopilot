"""
内存适配器

提供内存存储和检索功能。
"""

from typing import Any, Dict, Optional

class BasicMemoryAdapter:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config
        self.client = None
        self.collection = None

