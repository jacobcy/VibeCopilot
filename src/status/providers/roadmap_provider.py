"""
路线图状态提供者模块

实现路线图的状态提供者接口，适配 RoadmapStatus。
"""

import json  # 需要 json 模块
import logging
import os  # 需要 os 模块
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# 导入 get_config
from src.core.config import get_config
from src.db.session_manager import session_scope  # 需要 session_scope

# 移除 RoadmapService 的直接导入
# from src.roadmap.service.roadmap_service import RoadmapService
# --- 移除对已删除的 RoadmapStatus 的导入 ---
# from src.roadmap.service.roadmap_status import RoadmapStatus
# ------------------------------------------
from src.status.interfaces import IStatusProvider

# 处理循环导入的类型提示
if TYPE_CHECKING:
    from src.roadmap.service.roadmap_service import RoadmapService

logger = logging.getLogger(__name__)


class RoadmapStatusProvider(IStatusProvider):
    """路线图状态提供者

    现在也负责管理活动路线图ID的持久化状态。
    """

    def __init__(self):
        """初始化路线图状态提供者 (不再接收 roadmap_service)

        Raises:
            ValueError: 如果无法从配置确定 current_roadmap.json 的路径。
            OSError: 如果无法创建状态目录。
        """
        # 初始化服务和检查器为 None，等待 set_service 调用
        self.roadmap_service: Optional["RoadmapService"] = None
        # --- 移除 roadmap_status_checker ---
        # self.roadmap_status_checker: Optional[RoadmapStatus] = None
        # ----------------------------------

        self._active_roadmap_id: Optional[str] = None

        # 获取活动路线图状态文件路径
        try:
            config = get_config()
            data_dir = config.get("paths.data_dir")
            if not data_dir:
                raise ValueError("配置键 'paths.data_dir' 未设置或无效。")
            self.CURRENT_ROADMAP_FILE = os.path.join(data_dir, "status", "current_roadmap.json")
            logger.debug(f"当前路线图文件路径设置为: {self.CURRENT_ROADMAP_FILE}")
        except Exception as e:
            logger.error(f"无法从配置确定 current_roadmap.json 路径: {e}", exc_info=True)
            raise ValueError(f"无法从配置确定 current_roadmap.json 路径: {e}") from e

        # 确保目录存在
        try:
            status_dir = os.path.dirname(self.CURRENT_ROADMAP_FILE)
            os.makedirs(status_dir, exist_ok=True)
            logger.debug(f"确保状态目录存在: {status_dir}")
        except OSError as e:
            logger.error(f"无法创建状态目录 {status_dir}: {e}")
            raise

        # 加载活动路线图ID (需要修改 _validate_roadmap_exists 的调用方式)
        # 推迟验证到 set_service 之后，或者让 _load_active_roadmap_id 接收 repo
        # 暂时先只加载 ID，在 get_active_roadmap_id 时再验证可能更安全
        self._load_active_roadmap_id_from_file()  # 重命名以示区分

    def set_service(self, roadmap_service: "RoadmapService"):
        """注入 RoadmapService 实例并完成初始化。"""
        if self.roadmap_service:
            logger.warning("RoadmapService 已被设置，将被覆盖。")
        self.roadmap_service = roadmap_service
        # --- 移除 roadmap_status_checker 初始化 ---
        # # 在这里初始化依赖 roadmap_service 的组件
        # # self.roadmap_status_checker = RoadmapStatus(roadmap_service)
        # -----------------------------------------
        logger.info("RoadmapStatusProvider 已成功注入 RoadmapService。")
        # 可以在这里触发一次加载时验证（如果需要）
        self._validate_loaded_active_id()

    def _ensure_service_set(self):
        """确保 roadmap_service 已被注入。"""
        if not self.roadmap_service:
            raise RuntimeError("RoadmapService 尚未在 RoadmapStatusProvider 上设置。")

    # --- 活动路线图 ID 管理 ---

    def _load_active_roadmap_id_from_file(self) -> None:
        """仅从文件加载活动ID，不进行验证。"""
        try:
            if os.path.exists(self.CURRENT_ROADMAP_FILE):
                with open(self.CURRENT_ROADMAP_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._active_roadmap_id = data.get("active_roadmap_id")
                    logger.debug(f"从文件加载活动路线图ID (待验证): {self._active_roadmap_id}")
            else:
                self._active_roadmap_id = None
                logger.info(f"活动路线图状态文件不存在 ({self.CURRENT_ROADMAP_FILE})。")
        except json.JSONDecodeError as e:
            logger.error(f"解析活动路线图状态文件失败 ({self.CURRENT_ROADMAP_FILE}): {e}. 活动ID将为 None。")
            self._active_roadmap_id = None
        except Exception as e:
            logger.error(f"加载活动路线图ID时出错: {e}", exc_info=True)
            self._active_roadmap_id = None

    def _validate_loaded_active_id(self):
        """验证内存中的活动ID是否有效，通常在 set_service 后调用。"""
        self._ensure_service_set()
        loaded_id = self._active_roadmap_id
        if loaded_id and not self._validate_roadmap_exists(loaded_id):
            logger.warning(f"先前加载的活动路线图ID {loaded_id} 无效，将清除。")
            self._active_roadmap_id = None
            self._save_active_roadmap_id()  # 保存清除状态
        elif loaded_id:
            logger.info(f"先前加载的活动路线图ID {loaded_id} 验证通过。")

    def _save_active_roadmap_id(self) -> None:
        """保存当前活动路线图ID到文件"""
        try:
            with open(self.CURRENT_ROADMAP_FILE, "w", encoding="utf-8") as f:
                json.dump({"active_roadmap_id": self._active_roadmap_id}, f, indent=2)
                logger.debug(f"保存活动路线图ID到文件: {self._active_roadmap_id}")
        except Exception as e:
            logger.error(f"保存活动路线图ID失败: {e}", exc_info=True)
            # 这里不应重置内存状态，只是保存失败

    def _validate_roadmap_exists(self, roadmap_id: str) -> bool:
        """验证给定的 roadmap_id 是否在数据库中存在"""
        self._ensure_service_set()  # 确保服务已设置
        if not roadmap_id:
            return False
        try:
            with session_scope() as session:
                # 使用注入的 RoadmapService 里的 repo
                roadmap = self.roadmap_service.roadmap_repo.get_by_id(session, roadmap_id)
                return roadmap is not None
        except Exception as e:
            logger.error(f"验证路线图ID {roadmap_id} 存在性时出错: {e}", exc_info=True)
            return False  # 无法验证时视为不存在

    def set_active_roadmap_id(self, roadmap_id: Optional[str]) -> bool:
        """设置当前活动的路线图ID，并持久化到文件

        Args:
            roadmap_id: 路线图ID，或None来清除

        Returns:
            bool: 操作是否成功 (如果验证失败则返回 False)
        """
        self._ensure_service_set()  # 确保服务已设置才能验证
        if roadmap_id and not self._validate_roadmap_exists(roadmap_id):
            logger.error(f"尝试设置不存在的路线图 {roadmap_id} 为活动路线图。")
            return False

        self._active_roadmap_id = roadmap_id
        self._save_active_roadmap_id()
        logger.info(f"已设置并持久化活动路线图ID: {roadmap_id}")
        return True

    def get_active_roadmap_id(self) -> Optional[str]:
        """获取当前内存中的活动路线图ID (已从文件加载)"""
        return self._active_roadmap_id

    # --- 现有方法保持不变，但使用 self.roadmap_status_checker ---

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "roadmap"

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取路线图状态

        Args:
            entity_id: 可选的实体ID，格式为 'type:id' 或直接使用ID。
                      如果不提供，则返回整个路线图的状态。

        Returns:
            包含状态信息的字典
        """
        self._ensure_service_set()
        try:
            check_type = "roadmap"
            element_id_to_check = None

            if entity_id:
                if ":" in entity_id:
                    entity_type, real_id = entity_id.split(":", 1)
                elif entity_id.startswith("M"):
                    entity_type = "milestone"
                    real_id = entity_id
                elif entity_id.startswith("E"):
                    entity_type = "epic"
                    real_id = entity_id
                elif entity_id.startswith("S"):
                    entity_type = "story"
                    real_id = entity_id
                elif entity_id.startswith("T"):
                    entity_type = "task"
                    real_id = entity_id
                else:
                    return {"error": f"无法识别实体类型: {entity_id}"}

                if entity_type in ["milestone", "epic", "story", "task"]:
                    check_type = entity_type
                    element_id_to_check = real_id
                else:
                    return {"error": f"不支持的实体类型: {entity_type}"}

            # 使用 RoadmapService 的方法来获取状态
            # 确保 RoadmapService.check_roadmap_status 能处理这些类型
            result = self.roadmap_service.check_roadmap_status(check_type=check_type, element_id=element_id_to_check)

            if not result.get("success", False):
                return {"error": result.get("error", "获取路线图状态失败")}

            status_data = result.get("status", {})
            status_data["domain"] = self.domain
            return status_data

        except Exception as e:
            logger.error(f"获取路线图状态时出错: {e}", exc_info=True)
            return {"error": str(e)}

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新路线图实体状态

        Args:
            entity_id: 实体ID，格式为 "milestone:<id>" 或 "task:<id>"
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        self._ensure_service_set()
        try:
            if ":" in entity_id:
                entity_type, real_id = entity_id.split(":", 1)
            else:
                # 尝试猜测类型
                if entity_id.startswith("M"):
                    entity_type = "milestone"
                elif entity_id.startswith("E"):
                    entity_type = "epic"
                elif entity_id.startswith("S"):
                    entity_type = "story"
                elif entity_id.startswith("T"):
                    entity_type = "task"
                else:
                    return {"error": f"无法识别实体类型: {entity_id}", "updated": False}
                real_id = entity_id

            # 调用 RoadmapService 提供的更新器
            result = self.roadmap_service.updater.update_element_status(element_id=real_id, element_type=entity_type, status=status)

            # 假设 updater 返回类似 {success: bool, message?: str, error?: str} 的结构
            if result.get("success"):
                return {"updated": True, "entity_id": entity_id, "status": status, "message": result.get("message", "状态更新成功")}
            else:
                return {"updated": False, "error": result.get("error", "更新失败"), "entity_id": entity_id}

        except Exception as e:
            logger.error(f"更新路线图状态时出错: {e}", exc_info=True)
            return {"error": str(e), "updated": False}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出路线图中的实体

        Args:
            status: 可选，筛选特定状态的实体

        Returns:
            List[Dict[str, Any]]: 实体列表
        """
        self._ensure_service_set()
        try:
            # 直接调用 RoadmapService 的 list_elements 方法
            result = self.roadmap_service.list_elements(type="all", status=status or "all")
            if result.get("success"):
                # 可能需要调整返回格式以匹配 provider 接口预期
                entities = []
                for item in result.get("data", []):
                    entities.append(
                        {
                            "id": f"{item.get('type')}:{item.get('id')}",
                            "name": item.get("title"),
                            "type": item.get("type"),
                            "status": item.get("status")
                            # 可以根据需要添加其他字段
                        }
                    )
                return entities
            else:
                logger.warning(f"列出实体失败: {result.get('message')}")
                return []
        except Exception as e:
            logger.error(f"列出路线图实体时出错: {e}", exc_info=True)
            return []
