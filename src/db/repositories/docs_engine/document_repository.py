"""
文档仓库模块

提供文档数据的数据库访问方法
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db.docs_engine import Document, DocumentStatus


class DocumentRepository(Repository[Document]):
    """文档仓库"""

    def __init__(self, session: Session):
        super().__init__(session, Document)

    def create(self, **kwargs) -> Document:
        """创建文档"""
        data = {}

        # 处理所有参数
        for key, value in kwargs.items():
            if key == "metadata":
                data["doc_metadata"] = value
            else:
                data[key] = value

        # 设置默认状态
        if "status" not in data:
            data["status"] = DocumentStatus.DRAFT

        return super().create(data)

    def find_by_path(self, path: str) -> Optional[Document]:
        """通过路径查找文档

        Args:
            path: 文档路径

        Returns:
            文档对象，如果不存在则返回None
        """
        return self.session.query(Document).filter(Document.path == path).first()

    def find_by_title(self, title: str) -> List[Document]:
        """通过标题查找文档，支持模糊匹配

        Args:
            title: 文档标题

        Returns:
            匹配的文档列表
        """
        return self.session.query(Document).filter(Document.title.like(f"%{title}%")).all()

    def find_recent(self, limit: int = 10) -> List[Document]:
        """查找最近更新的文档

        Args:
            limit: 返回数量限制

        Returns:
            最近更新的文档列表
        """
        return self.session.query(Document).order_by(Document.updated_at.desc()).limit(limit).all()

    def update_status(self, document_id: str, status: DocumentStatus) -> bool:
        """更新文档状态

        Args:
            document_id: 文档ID
            status: 新状态

        Returns:
            是否更新成功
        """
        document = self.find_by_id(document_id)
        if not document:
            return False

        document.status = status
        self.session.commit()
        return True

    def find_all_in_folder(self, folder_path: str) -> List[Document]:
        """查找指定文件夹中的所有文档

        Args:
            folder_path: 文件夹路径，例如 "/docs/"

        Returns:
            文档列表
        """
        # 确保文件夹路径以/结尾
        if not folder_path.endswith("/"):
            folder_path += "/"

        return self.session.query(Document).filter(Document.path.like(f"{folder_path}%")).all()
