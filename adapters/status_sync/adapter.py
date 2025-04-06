"""
状态同步适配器模块 (兼容层)

此文件为兼容层，提供与原始 StatusSyncAdapter 类相同的接口，
但将实际同步工作委托给重构后的各个服务类。
新代码应直接使用 adapters.status_sync.services 包中的相应服务。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from adapters.n8n.adapter import N8nAdapter
from adapters.status_sync.services.execution_sync import ExecutionSync
from adapters.status_sync.services.n8n_sync import N8nSync
from adapters.status_sync.services.workflow_sync import WorkflowSync

logger = logging.getLogger(__name__)


class StatusSyncAdapter:
    """状态同步适配器"""

    def __init__(self, db_session: Session, n8n_adapter: Optional[N8nAdapter] = None):
        """初始化状态同步适配器

        Args:
            db_session: 数据库会话
            n8n_adapter: n8n适配器实例
        """
        self.db_session = db_session
        self.n8n_adapter = n8n_adapter

        # 初始化各个服务
        self.workflow_sync = WorkflowSync(db_session, n8n_adapter)
        self.execution_sync = ExecutionSync(db_session, n8n_adapter)
        self.n8n_sync = N8nSync(db_session, n8n_adapter)

        logger.info("状态同步适配器已初始化")

    # 工作流相关方法委托给 WorkflowSync 服务

    def sync_workflow_status(self, workflow_id: str) -> bool:
        """同步工作流状态到n8n (兼容方法)

        Args:
            workflow_id: 工作流ID

        Returns:
            是否同步成功
        """
        return self.workflow_sync.sync_workflow_status(workflow_id)

    def create_n8n_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> bool:
        """在n8n中创建工作流 (兼容方法)

        Args:
            workflow_id: 本地工作流ID
            workflow_data: n8n工作流数据

        Returns:
            是否创建成功
        """
        return self.workflow_sync.create_n8n_workflow(workflow_id, workflow_data)

    def import_n8n_workflows(self) -> int:
        """从n8n导入所有工作流 (兼容方法)

        Returns:
            导入的工作流数量
        """
        return self.workflow_sync.import_n8n_workflows()

    # 执行相关方法委托给 ExecutionSync 服务

    def sync_execution_status(self, execution_id: str) -> bool:
        """同步执行状态 (兼容方法)

        Args:
            execution_id: 执行ID

        Returns:
            是否同步成功
        """
        return self.execution_sync.sync_execution_status(execution_id)

    def sync_all_pending_executions(self) -> int:
        """同步所有待处理的执行 (兼容方法)

        Returns:
            同步的执行数量
        """
        return self.execution_sync.sync_all_pending_executions()

    def create_execution(self, workflow_id: str, params: Dict[str, Any] = None) -> Optional[str]:
        """创建执行记录并启动n8n工作流 (兼容方法)

        Args:
            workflow_id: 工作流ID
            params: 执行参数

        Returns:
            执行ID，如果失败则返回None
        """
        return self.execution_sync.create_execution(workflow_id, params)

    def get_executions_by_workflow(self, workflow_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取工作流的执行记录 (兼容方法)

        Args:
            workflow_id: 工作流ID
            limit: 限制数量

        Returns:
            执行记录列表
        """
        return self.execution_sync.get_executions_by_workflow(workflow_id, limit)

    # N8n相关方法委托给 N8nSync 服务

    def sync_variable(self, key: str, value: Any) -> bool:
        """同步变量到n8n (兼容方法)

        Args:
            key: 变量名
            value: 变量值

        Returns:
            是否同步成功
        """
        return self.n8n_sync.sync_variable(key, value)

    def sync_credentials(self, credential_type: str, credential_data: Dict[str, Any]) -> bool:
        """同步凭证到n8n (兼容方法)

        Args:
            credential_type: 凭证类型
            credential_data: 凭证数据

        Returns:
            是否同步成功
        """
        return self.n8n_sync.sync_credentials(credential_type, credential_data)

    def get_all_variables(self) -> List[Dict[str, Any]]:
        """获取所有n8n变量 (兼容方法)

        Returns:
            变量列表
        """
        return self.n8n_sync.get_all_variables()

    def get_all_credentials(self) -> List[Dict[str, Any]]:
        """获取所有n8n凭证 (兼容方法)

        Returns:
            凭证列表
        """
        return self.n8n_sync.get_all_credentials()

    def test_connection(self) -> bool:
        """测试n8n连接 (兼容方法)

        Returns:
            是否连接成功
        """
        return self.n8n_sync.test_connection()

    def update_system_variables(self, variables: Dict[str, Any]) -> Dict[str, bool]:
        """批量更新系统变量 (兼容方法)

        Args:
            variables: 变量字典

        Returns:
            各变量更新结果
        """
        return self.n8n_sync.update_system_variables(variables)
