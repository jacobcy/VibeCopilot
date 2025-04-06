"""
模板仓库包

导出模板仓库接口和实现
"""

from .template_repository import (
    FileSystemTemplateRepository,
    SQLTemplateRepositoryAdapter,
    TemplateRepository,
)

__all__ = ["TemplateRepository", "FileSystemTemplateRepository", "SQLTemplateRepositoryAdapter"]
