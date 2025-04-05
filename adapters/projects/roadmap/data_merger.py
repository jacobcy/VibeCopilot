"""
路线图数据合并模块

提供合并多个路线图数据源的功能。
"""

import copy
from typing import Any, Dict, List, Optional


class RoadmapMerger:
    """路线图数据合并器"""

    @staticmethod
    def merge_roadmaps(
        roadmaps: List[Dict[str, Any]], merge_strategy: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        合并多个路线图数据

        Args:
            roadmaps: 多个路线图数据的列表
            merge_strategy: 可选的合并策略配置
                可用策略:
                    - "overwrite": 后面的数据覆盖前面的数据
                    - "append": 对于列表，追加非重复项
                    - "first": 只使用第一个有效值
                    - "last": 只使用最后一个有效值
                    - "combine": 合并所有值（用于对象）

        Returns:
            Dict[str, Any]: 合并后的路线图数据
        """
        if not roadmaps:
            return {}

        if len(roadmaps) == 1:
            return copy.deepcopy(roadmaps[0])

        # 默认合并策略
        default_strategy = {
            "title": "last",
            "description": "last",
            "version": "last",
            "milestones": "append",
            "tasks": "append",
            "team": "append",
            "metadata": "combine",
            "default": "last",  # 未指定字段的默认策略
        }

        # 使用用户提供的策略覆盖默认策略
        if merge_strategy:
            for key, value in merge_strategy.items():
                default_strategy[key] = value

        # 创建目标对象
        result = {}

        # 合并所有字段
        all_keys = set()
        for roadmap in roadmaps:
            all_keys.update(roadmap.keys())

        for key in all_keys:
            strategy = default_strategy.get(key, default_strategy["default"])
            values = [roadmap.get(key) for roadmap in roadmaps if key in roadmap]

            if not values:
                continue

            # 根据策略合并值
            if strategy == "overwrite":
                result[key] = copy.deepcopy(values[-1])
            elif strategy == "first":
                result[key] = copy.deepcopy(values[0])
            elif strategy == "last":
                result[key] = copy.deepcopy(values[-1])
            elif strategy == "append" and isinstance(values[0], list):
                result[key] = RoadmapMerger._merge_lists(values)
            elif strategy == "combine" and isinstance(values[0], dict):
                result[key] = RoadmapMerger._merge_dicts(values)
            else:
                # 默认使用最后一个值
                result[key] = copy.deepcopy(values[-1])

        # 确保合并后的路线图中包含关键字段
        if "milestones" in result:
            result["milestones"] = RoadmapMerger._deduplicate_items(result["milestones"], "id")

        if "tasks" in result:
            result["tasks"] = RoadmapMerger._deduplicate_items(result["tasks"], "id")

        return result

    @staticmethod
    def _merge_lists(lists: List[List]) -> List:
        """合并多个列表，保留唯一的项"""
        result = []
        for lst in lists:
            for item in lst:
                if item not in result:  # 这可能对复杂对象不起作用
                    result.append(copy.deepcopy(item))
        return result

    @staticmethod
    def _merge_dicts(dicts: List[Dict]) -> Dict:
        """递归合并多个字典"""
        result = {}
        for d in dicts:
            for key, value in d.items():
                if key not in result:
                    result[key] = copy.deepcopy(value)
                elif isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = RoadmapMerger._merge_dicts([result[key], value])
                elif isinstance(result[key], list) and isinstance(value, list):
                    result[key] = RoadmapMerger._merge_lists([result[key], value])
                else:
                    result[key] = copy.deepcopy(value)  # 覆盖现有值
        return result

    @staticmethod
    def _deduplicate_items(items: List[Dict[str, Any]], id_field: str) -> List[Dict[str, Any]]:
        """根据ID字段去除重复项，保留最后一个出现的项"""
        result = []
        seen_ids = set()

        # 按相反的顺序处理以保留最后出现的项
        for item in reversed(items):
            if id_field in item and item[id_field] not in seen_ids:
                seen_ids.add(item[id_field])
                result.insert(0, item)  # 插入到开头以保持原始顺序
            elif id_field not in item:
                result.insert(0, item)  # 没有ID的项总是被保留

        return result
