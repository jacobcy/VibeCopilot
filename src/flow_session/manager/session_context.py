"""
工作流会话上下文管理

提供工作流会话上下文数据的获取和更新功能。
"""

import json
import logging
from typing import Any, Dict, List, Optional

from src.models.db import FlowSession

logger = logging.getLogger(__name__)


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

            return get_stages_for_session(self.session, session.id)
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
        """获取会话可能的下一阶段，基于嵌入在 stages_data 字典中的 stages 和 transitions 列表

        Args:
            id_or_name: 会话ID或名称
            current_stage_id: 当前阶段ID，如果不提供则使用会话当前阶段

        Returns:
            可能的下一阶段定义列表 (字典)

        Raises:
            ValueError: 如果找不到指定的会话或阶段
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 确定当前阶段 ID
        effective_current_stage_id = current_stage_id
        if not effective_current_stage_id:
            effective_current_stage_id = session.current_stage_id
            if not effective_current_stage_id:
                context = self.get_session_context(id_or_name)
                effective_current_stage_id = context.get("current_stage")
                if not effective_current_stage_id:
                    logger.error(f"无法确定会话 {id_or_name} 的当前阶段ID")  # Use logger
                    raise ValueError(f"无法确定会话 {id_or_name} 的当前阶段")

        logger.info(f"查找会话 {id_or_name} 从阶段 {effective_current_stage_id} 出发的下一阶段")  # Use logger

        # 获取工作流定义
        workflow = self.workflow_repo.get_by_id(self.session, session.workflow_id)
        if not workflow:
            raise ValueError(f"找不到工作流定义: {session.workflow_id}")

        # 解析 stages_data (现在期望它是包含 'stages' 和 'transitions' 的字典)
        workflow_definition_data = workflow.stages_data
        if isinstance(workflow_definition_data, str):
            try:
                workflow_definition_data = json.loads(workflow_definition_data)
                logger.debug("Parsed workflow_definition_data from JSON string.")
            except json.JSONDecodeError:
                logger.error(f"无法解析工作流 {workflow.id} 的 workflow_definition_data (stages_data) JSON")
                workflow_definition_data = None

        if not isinstance(workflow_definition_data, dict):
            logger.error(f"工作流 {workflow.id} 的 workflow_definition_data (stages_data) 不是预期的字典格式。类型: {type(workflow_definition_data)}")
            return []

        # --- 添加这行日志 ---
        logger.debug(f"完整的 workflow_definition_data 内容: {json.dumps(workflow_definition_data, indent=2, ensure_ascii=False)}")
        # --- 添加结束 ---

        # 从字典中提取 stages 和 transitions 列表
        stages_list = workflow_definition_data.get("stages", [])
        transitions_list = workflow_definition_data.get("transitions", [])

        if not isinstance(stages_list, list):
            logger.error(f"从 workflow_definition_data 提取的 'stages' 不是列表。类型: {type(stages_list)}")
            return []
        if not isinstance(transitions_list, list):
            logger.error(f"从 workflow_definition_data 提取的 'transitions' 不是列表。类型: {type(transitions_list)}")
            # It might be valid to have no transitions, so don't return here, just log.
            logger.warning(f"工作流 {workflow.id} 的定义中没有找到有效的 transitions 列表。")
            transitions_list = []  # Ensure it's a list for iteration

        logger.debug(f"提取到 {len(stages_list)} 个阶段定义和 {len(transitions_list)} 个转换规则。")

        # 将 stages_list 转换为 ID 到定义的映射，方便查找目标阶段
        stage_defs_map = {}
        for stage_def in stages_list:
            if isinstance(stage_def, dict):
                stage_id = stage_def.get("id")
                if stage_id:
                    stage_defs_map[stage_id] = stage_def
            else:
                logger.warning(f"stages_list 中包含非字典项: {stage_def}")

        # 查找当前阶段是否存在 (主要用于日志记录和健壮性)
        if effective_current_stage_id not in stage_defs_map:
            logger.warning(f"当前阶段 {effective_current_stage_id} 未在提取的 stages_list 中找到定义。")
            # Depending on requirements, might want to raise ValueError here

        next_stages_defs = []
        # 遍历提取的转换规则列表
        for transition in transitions_list:
            if not isinstance(transition, dict):
                logger.warning(f"transitions_list 中包含非字典项: {transition}")
                continue

            # 使用正确的键名 'from_stage' 和 'to_stage'
            source_id = transition.get("from_stage")
            target_id = transition.get("to_stage")

            if source_id == effective_current_stage_id:
                logger.debug(f"找到匹配的转换规则: from={source_id}, to={target_id}")
                if target_id:
                    # (可选) 在这里检查转换条件 transition.get('condition')
                    # condition_met = self._check_transition_condition(transition.get('condition'), session_context)
                    # if not condition_met: continue

                    # 根据 target_id 查找目标阶段定义
                    target_stage_def = stage_defs_map.get(target_id)
                    if target_stage_def:
                        if target_stage_def not in next_stages_defs:
                            next_stages_defs.append(target_stage_def)
                            logger.info(f"找到可能的下一阶段: {target_id} ({target_stage_def.get('name', '?')})")
                        else:
                            logger.debug(f"目标阶段 {target_id} 已在列表中")
                    else:
                        logger.warning(f"转换规则指向了未在 stages_list 中定义的阶段ID: {target_id}")
                else:
                    logger.warning(f"找到从 {source_id} 出发的转换规则，但缺少 'to' 目标ID: {transition}")

        if not next_stages_defs:
            logger.info(f"结论: 没有为阶段 {effective_current_stage_id} 找到有效的下一阶段定义。")

        # (可选) 根据权重排序
        # next_stages_defs.sort(key=lambda s: s.get("weight", 999))

        return next_stages_defs

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
        workflow = self.workflow_repo.get_by_id(self.session, session.workflow_id)
        if not workflow:
            self._log("log_error", f"找不到工作流定义: {session.workflow_id}")
            return None

        # 从 stages_data 获取阶段信息
        stages_data = workflow.stages_data
        if not stages_data:
            self._log("log_error", f"工作流定义 {session.workflow_id} 没有阶段数据")
            return None

        # 确保 stages_data 是列表或字典
        if isinstance(stages_data, str):
            try:
                stages_data = json.loads(stages_data)
            except json.JSONDecodeError:
                self._log("log_error", f"无法解析工作流 {workflow.id} 的阶段数据")
                return None

        # 处理不同格式的 stages_data
        stages_list = []
        if isinstance(stages_data, list):
            stages_list = stages_data
        elif isinstance(stages_data, dict):
            stages_list = list(stages_data.values())
        else:
            self._log("log_error", f"工作流 {workflow.id} 的阶段数据格式不支持: {type(stages_data)}")
            return None

        if not stages_list:
            self._log("log_error", f"工作流定义 {session.workflow_id} 没有定义阶段")
            return None

        # 获取第一个阶段的ID
        first_stage = None
        for stage in stages_list:
            if isinstance(stage, dict):
                first_stage = stage
                break

        if not first_stage:
            self._log("log_error", f"工作流定义 {session.workflow_id} 没有有效的阶段")
            return None

        first_stage_id = first_stage.get("id")
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
                stage_data = {"stage_id": first_stage_id, "name": first_stage.get("name", f"阶段-{first_stage_id}")}
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
