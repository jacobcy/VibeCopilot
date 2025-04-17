"""
任务参考资料显示工具模块
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console

from src.memory import get_memory_service
from src.utils.file_utils import get_relative_path

logger = logging.getLogger(__name__)
console = Console()


async def get_memory_entity(permalink: str) -> Optional[Dict[str, Any]]:
    """获取Memory实体信息

    Args:
        permalink: Memory链接

    Returns:
        实体信息字典，如果获取失败则返回None
    """
    try:
        # 获取MemoryService实例
        memory_service = get_memory_service()

        # 读取笔记内容
        success, message, result = memory_service.read_note(path=permalink)
        if success and result:
            return result
        else:
            logger.warning(f"获取Memory实体失败: {message}")
            return None

    except Exception as e:
        logger.error(f"获取Memory实体时出错: {e}", exc_info=True)
        return None


def show_task_references(task_id: str, task_title: str, memory_link: Optional[str] = None) -> Dict[str, Any]:
    """显示任务参考资料

    Args:
        task_id: 任务ID
        task_title: 任务标题
        memory_link: Memory链接（可选）

    Returns:
        包含操作结果的字典
    """
    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
    }

    try:
        # 准备参考资料信息
        ref_info = {"任务ID": task_id, "任务标题": task_title, "参考资料": []}

        if memory_link:
            # 获取Memory实体信息
            entity = asyncio.run(get_memory_entity(memory_link))

            if entity:
                # 获取文件路径
                file_path = entity.get("file_path", "未知路径")
                title = entity.get("title", "未知标题")
                created_at = entity.get("created_at", "未记录时间")

                ref_info["参考资料"].append(
                    {
                        "标题": title,
                        "相对路径": get_relative_path(file_path) if file_path else "未知路径",
                        "添加时间": created_at,
                        "Memory链接": memory_link,
                        "内容": entity.get("content", ""),
                    }
                )
            else:
                ref_info["参考资料"].append({"Memory链接": memory_link, "状态": "不可访问或已删除"})
        else:
            ref_info["状态"] = "无参考资料"

        # 输出参考资料信息
        console.print(yaml.dump(ref_info, allow_unicode=True, sort_keys=False))
        results["data"] = ref_info
        results["message"] = "成功获取参考资料信息"

    except Exception as e:
        logger.error(f"显示参考资料时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"显示参考资料时出错: {e}"
        console.print(f"[bold red]错误:[/bold red] {e}")

    return results
