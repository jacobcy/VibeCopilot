"""
Chroma 向量存储

提供向量存储功能，使用 Chroma 作为底层存储。
"""

from typing import Any, Dict, Optional

class ChromaVectorStore:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config
        self.client = None
        self.collection = None

