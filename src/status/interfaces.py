"""
状态接口定义模块

定义各种状态提供者必须实现的接口，确保统一的状态查询和管理。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IStatusProvider(ABC):
    """状态提供者接口

    所有提供状态信息的组件都应实现此接口。
    """

    @property
    @abstractmethod
    def domain(self) -> str:
        """获取状态提供者的领域名称

        Returns:
            str: 领域名称，如 'roadmap', 'workflow' 等
        """
        pass

    @abstractmethod
    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取状态信息

        Args:
            entity_id: 可选，实体ID。不提供则获取整个领域的状态概览。

        Returns:
            Dict[str, Any]: 状态信息，应包含"domain"字段
        """
        pass

    @abstractmethod
    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新状态

        Args:
            entity_id: 实体ID
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果，应包含"updated"字段表示是否成功
        """
        pass

    @abstractmethod
    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出领域中的实体

        Args:
            status: 可选，筛选特定状态的实体

        Returns:
            List[Dict[str, Any]]: 实体列表
        """
        pass


class IStatusSubscriber(ABC):
    """状态订阅者接口

    需要监听状态变化的组件实现此接口。
    """

    @abstractmethod
    def on_status_changed(self, domain: str, entity_id: str, old_status: str, new_status: str, data: Dict[str, Any]) -> None:
        """状态变更回调

        Args:
            domain: 领域名称
            entity_id: 实体ID
            old_status: 旧状态
            new_status: 新状态
            data: 附加数据
        """
        pass
