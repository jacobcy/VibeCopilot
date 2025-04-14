"""
工作流会话上下文管理

提供工作流会话上下文数据的获取和更新功能。
"""

import json
from typing import Any, Dict, List, Optional

from src.models.db import FlowSession


class SessionContextMixin:
    """会话上下文管理混入类"""

    def get_session_context(self, id_or_name: str) -> Dict[str, Any]:
        """获取会话上下文数据

        Args:
            id_or_name: 会话ID或名称

        Returns:
            会话上下文数据字典

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 获取会话上下文
        context = {}
        if session.context:
            try:
                context = json.loads(session.context)
            except Exception as e:
                self._log("log_error", f"解析会话上下文失败: {str(e)}")
                context = {}

        return context

    def update_session_context(self, id_or_name: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新会话上下文数据

        Args:
            id_or_name: 会话ID或名称
            context_data: 要更新的上下文数据

        Returns:
            更新后的完整上下文数据字典

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 获取当前上下文并合并新数据
        current_context = self.get_session_context(id_or_name)
        current_context.update(context_data)

        # 保存更新后的上下文
        try:
            context_json = json.dumps(current_context)
            self.session_repo.update(session.id, {"context": context_json})
            session.context = context_json
        except Exception as e:
            self._log("log_error", f"更新会话上下文失败: {str(e)}")
            raise ValueError(f"更新会话上下文失败: {str(e)}")

        return current_context

    def clear_session_context(self, id_or_name: str) -> bool:
        """清除会话上下文数据

        Args:
            id_or_name: 会话ID或名称

        Returns:
            是否成功清除

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        try:
            self.session_repo.update(session.id, {"context": "{}"})
            session.context = "{}"
            return True
        except Exception as e:
            self._log("log_error", f"清除会话上下文失败: {str(e)}")
            return False

    def get_session_stages(self, id_or_name: str) -> List[Any]:
        """获取会话的所有阶段

        Args:
            id_or_name: 会话ID或名称

        Returns:
            阶段列表

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 从阶段管理器获取阶段列表
        # 暂时提供一个基本实现，后续可扩展
        try:
            from src.flow_session.stage.manager import get_stages_for_session

            return get_stages_for_session(session.id)
        except ImportError:
            # 如果阶段管理器不可用，返回空列表
            self._log("log_warning", "阶段管理器不可用，无法获取阶段列表")
            return []

    def get_session_progress(self, id_or_name: str) -> Dict[str, Any]:
        """获取会话进度信息

        Args:
            id_or_name: 会话ID或名称

        Returns:
            进度信息字典，包含当前阶段、完成进度等

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 获取会话上下文中的进度信息
        context = self.get_session_context(id_or_name)
        progress = context.get("progress", {})

        # 获取阶段信息
        stages = self.get_session_stages(id_or_name)

        # 计算进度百分比
        total_stages = len(stages)
        completed_stages_count = sum(1 for stage in stages if stage.get("status") == "COMPLETED")

        # 分类阶段
        completed_stages_list = []
        pending_stages_list = []
        current_stage_info = None

        # 为了确保返回的数据格式正确，显式构建各个阶段列表
        for stage in stages:
            stage_status = stage.get("status", "")
            if stage_status == "COMPLETED":
                completed_stages_list.append(stage)
            elif stage_status == "ACTIVE" or (context.get("current_stage") and stage.get("id") == context.get("current_stage")):
                current_stage_info = stage
            else:
                pending_stages_list.append(stage)

        progress_info = {
            "current_stage": current_stage_info,
            "total_stages": total_stages,
            "completed_count": completed_stages_count,
            "completed_stages": completed_stages_list,  # 确保是列表
            "pending_stages": pending_stages_list,  # 确保是列表
            "progress_percentage": (completed_stages_count / total_stages * 100) if total_stages > 0 else 0,
        }

        return progress_info

    def set_current_stage(self, id_or_name: str, stage_id: str) -> bool:
        """设置会话当前阶段

        Args:
            id_or_name: 会话ID或名称
            stage_id: 阶段ID

        Returns:
            是否成功设置

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        try:
            # 1. 更新上下文中的当前阶段
            self.update_session_context(id_or_name, {"current_stage": stage_id})

            # 2. 更新会话的 current_stage_id 字段
            self.session_repo.update(session.id, {"current_stage_id": stage_id})

            # 3. 记录日志
            self._log("log_stage_changed", session.id, stage_id)
            self._log("log_info", f"已将会话 {session.id} 的当前阶段设置为 {stage_id}")
            return True
        except Exception as e:
            self._log("log_error", f"设置当前阶段失败: {str(e)}")
            return False

    def get_next_stages(self, id_or_name: str, current_stage_id: Optional[str] = None) -> List[Any]:
        """获取会话可能的下一阶段

        Args:
            id_or_name: 会话ID或名称
            current_stage_id: 当前阶段ID，如果不提供则使用会话当前阶段

        Returns:
            可能的下一阶段列表

        Raises:
            ValueError: 如果找不到指定的会话或阶段
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 如果没有提供当前阶段ID，使用会话当前阶段
        if not current_stage_id:
            context = self.get_session_context(id_or_name)
            current_stage_id = context.get("current_stage")
            if not current_stage_id:
                raise ValueError("无法确定当前阶段")

        # 获取工作流定义
        workflow = self.workflow_repo.get_by_id(session.workflow_id)
        if not workflow:
            raise ValueError(f"找不到工作流定义: {session.workflow_id}")

        # 获取当前阶段
        from src.db.repositories.stage_repository import StageRepository

        stage_repo = StageRepository(self.session)
        current_stage = stage_repo.get_by_id(current_stage_id)
        if not current_stage:
            raise ValueError(f"找不到阶段: {current_stage_id}")

        # 获取所有阶段
        all_stages = stage_repo.get_by_workflow_id(workflow.id)
        all_stages_dict = {stage.id: stage for stage in all_stages}

        # 计算下一阶段
        next_stages = []
        completed_stages = session.completed_stages or []

        # 遍历所有阶段，找出满足条件的下一阶段
        for stage_id, stage in all_stages_dict.items():
            # 跳过当前阶段和已完成阶段
            if stage_id == current_stage_id or stage_id in completed_stages:
                continue

            # 检查依赖关系
            if stage.depends_on:
                depends_satisfied = True
                for dep_id in stage.depends_on:
                    if dep_id not in completed_stages and dep_id != current_stage_id:
                        depends_satisfied = False
                        break

                if not depends_satisfied:
                    continue

            # 检查阶段是否可访问（有些阶段可能有额外条件）
            session_context = self.get_session_context(id_or_name)
            if stage.prerequisites and not self._check_prerequisites(stage.prerequisites, session_context):
                continue

            next_stages.append(stage)

        # 根据权重排序
        next_stages.sort(key=lambda s: s.weight if s.weight is not None else 999)

        return next_stages

    def _check_prerequisites(self, prerequisites: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """检查阶段先决条件是否满足

        Args:
            prerequisites: 先决条件字典
            context: 会话上下文

        Returns:
            是否满足先决条件
        """
        if not prerequisites:
            return True

        if not context:
            return False

        for key, value in prerequisites.items():
            if key not in context:
                return False

            if context[key] != value:
                return False

        return True

    def get_session_first_stage(self, id_or_name: str) -> Optional[str]:
        """获取会话的第一个阶段ID

        当会话没有当前阶段时，可用此方法获取第一个可用阶段。
        在解释会话场景特别有用。

        Args:
            id_or_name: 会话ID或名称

        Returns:
            第一个阶段ID，如果找不到则返回None
        """
        session = self.get_session(id_or_name)
        if not session:
            self._log("log_error", f"找不到会话: {id_or_name}")
            return None

        self._log("log_info", f"获取会话 {session.id} 的第一个阶段")

        # 获取工作流定义
        workflow = self.workflow_repo.get_by_id(session.workflow_id)
        if not workflow:
            self._log("log_error", f"找不到工作流定义: {session.workflow_id}")
            return None

        if not workflow.stages or len(workflow.stages) == 0:
            self._log("log_error", f"工作流定义 {session.workflow_id} 没有定义阶段")
            return None

        # 获取第一个阶段的ID
        first_stage_id = workflow.stages[0].get("id")
        if not first_stage_id:
            self._log("log_error", f"工作流定义 {session.workflow_id} 的第一个阶段没有ID")
            return None

        self._log("log_info", f"工作流 {session.workflow_id} 的第一个阶段ID是 {first_stage_id}")

        try:
            # 检查是否已存在该阶段的实例
            from src.db.repositories.stage_instance_repository import StageInstanceRepository

            stage_instance_repo = StageInstanceRepository(self.session)
            existing_instance = stage_instance_repo.get_by_session_and_stage(session.id, first_stage_id)

            # 如果没有现有实例，创建一个
            if not existing_instance:
                self._log("log_info", f"为会话 {session.id} 创建阶段实例 {first_stage_id}")
                # 导入阶段实例管理器
                from src.flow_session.stage.manager import StageInstanceManager

                stage_manager = StageInstanceManager(self.session)

                # 创建阶段实例
                stage_data = {"stage_id": first_stage_id, "name": workflow.stages[0].get("name", f"阶段-{first_stage_id}")}
                new_instance = stage_manager.create_instance(session.id, stage_data)
                self._log("log_info", f"为会话 {session.id} 创建了阶段实例 {first_stage_id} -> {new_instance.id if new_instance else 'Failed'}")
            else:
                self._log("log_info", f"会话 {session.id} 已存在阶段实例 {first_stage_id} -> {existing_instance.id}")

            # 无论是否新创建，都确保设置为当前阶段
            success = self.set_current_stage(session.id, first_stage_id)
            self._log("log_info", f"设置会话 {session.id} 的当前阶段为 {first_stage_id}: {'成功' if success else '失败'}")

            # 额外检查：验证会话的current_stage_id是否已更新
            updated_session = self.get_session(session.id)
            if updated_session and updated_session.current_stage_id == first_stage_id:
                self._log("log_info", f"验证成功: 会话 {session.id} 的current_stage_id已更新为 {first_stage_id}")
            else:
                current_id = updated_session.current_stage_id if updated_session else None
                self._log("log_warning", f"验证失败: 会话 {session.id} 的current_stage_id为 {current_id}")

            return first_stage_id

        except Exception as e:
            self._log("log_error", f"创建或设置首个阶段实例失败: {str(e)}")
            # 即使创建实例失败，仍然返回阶段ID，以维持原有行为
            return first_stage_id
