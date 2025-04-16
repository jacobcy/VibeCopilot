"""
任务与Memory系统集成模块

提供任务与Memory系统集成的功能，包括存储参考文档到Memory系统。
"""

import asyncio
import importlib
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger
from rich.console import Console

# 导入统一的 MemoryService 接口
from src.memory import MemoryService

console = Console()
logger = logging.getLogger(__name__)


# 安全地导入模块，处理可能的错误
def safe_import(module_name: str):
    """安全地导入模块，返回导入的模块或None"""
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        logger.error(f"导入模块 {module_name} 失败: {e}")
        return None


# 将append_to_task_log函数直接实现在memory模块中，避免循环导入
def append_to_task_log(task_id: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """向任务日志添加新条目"""
    log_path = os.path.join(".ai", "tasks", task_id, "task.log")

    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, "a") as f:
        f.write(f"## {current_time} - {action}\n")
        if details:
            for key, value in details.items():
                f.write(f"- {key}: {value}\n")
        f.write("\n")


async def link_to_memory(task_id: str, file_path: str) -> Dict[str, Any]:
    """将文件存储到Memory并关联到任务

    Args:
        task_id: 任务ID
        file_path: 文件路径

    Returns:
        存储结果
    """
    # 验证任务ID
    if not task_id:
        logger.error("任务ID不能为空")
        return {"success": False, "error": "任务ID不能为空"}

    # 验证文件路径
    if not file_path:
        logger.error("文件路径不能为空")
        return {"success": False, "error": "文件路径不能为空"}

    # 确保文件存在
    file_path = os.path.abspath(os.path.expanduser(file_path))
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return {"success": False, "error": f"文件不存在: {file_path}"}

    if os.path.isdir(file_path):
        logger.error(f"路径指向目录而非文件: {file_path}")
        return {"success": False, "error": f"路径指向目录而非文件: {file_path}"}

    # 读取文件内容
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        logger.error(f"文件编码错误，尝试使用二进制模式读取: {file_path}")
        try:
            # 尝试以二进制模式读取
            with open(file_path, "rb") as f:
                content = f.read().decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"以二进制模式读取文件失败: {e}")
            return {"success": False, "error": f"文件编码错误: {e}"}
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return {"success": False, "error": f"读取文件失败: {e}"}

    # 准备元数据
    file_name = os.path.basename(file_path)
    folder = "references"  # 使用固定文件夹
    tags = f"reference,task:{task_id}"

    # 从文件内容中提取标题
    title = file_name
    lines = content.split("\n")
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()

    # 使用 MemoryService 存储
    memory_service = MemoryService()
    success, message, result = memory_service.create_note(content=content, title=title, folder=folder, tags=tags)

    if not success:
        logger.error(f"存储到Memory失败: {message}")
        return {"success": False, "error": message}

    permalink = result.get("permalink", "")
    if not permalink:
        logger.error("存储成功但未获取到permalink")
        return {"success": False, "error": "存储成功但未获取到permalink"}

    # 使用TaskRepository添加Memory引用
    db_module = safe_import("src.db")
    if not db_module:
        return {"success": False, "error": "导入数据库模块失败"}

    repo_module = safe_import("src.db.repositories.task_repository")
    if not repo_module:
        return {"success": False, "error": "导入任务仓库模块失败"}

    try:
        session_factory = db_module.get_session_factory()
        with session_factory() as session:
            task_repo = repo_module.TaskRepository(session)

            # 查询任务是否存在
            task = task_repo.get_by_id(task_id)
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return {"success": False, "error": f"任务不存在: {task_id}"}

            # 使用add_memory_reference方法添加引用
            add_result = task_repo.add_memory_reference(task_id, permalink, title)

            if add_result:
                # 记录到任务日志
                append_to_task_log(task_id, "添加参考文档", {"文档路径": file_path, "Memory链接": permalink})
                return {"success": True, "permalink": permalink}
            else:
                error_msg = "文档可能已存在或任务不存在"
                logger.warning(error_msg)
                return {"success": False, "error": error_msg, "permalink": permalink}
    except Exception as e:
        logger.error(f"添加Memory引用失败: {e}")
        return {"success": False, "error": f"添加Memory引用失败: {e}", "permalink": permalink}


def store_ref_to_memory(task_id: str, ref_path: str) -> Dict[str, Any]:
    """同步方法：将参考文档存储到Memory

    Args:
        task_id: 任务ID
        ref_path: 参考文档路径

    Returns:
        存储结果
    """
    try:
        logger.info(f"开始处理参考文档: {ref_path} 关联到任务: {task_id}")

        # 验证输入
        if not task_id:
            return {"success": False, "error": "任务ID不能为空"}
        if not ref_path:
            return {"success": False, "error": "参考文档路径不能为空"}

        # 转换相对路径为绝对路径
        ref_path = os.path.abspath(os.path.expanduser(ref_path))
        logger.info(f"转换后的绝对路径: {ref_path}")

        # 检查文件是否存在
        if not os.path.exists(ref_path):
            error_msg = f"参考文档不存在: {ref_path}"
            logger.error(error_msg)
            console.print(f"[bold red]错误:[/bold red] {error_msg}")
            return {"success": False, "error": error_msg}

        # 检查是否是目录
        if os.path.isdir(ref_path):
            error_msg = f"参考路径指向的是目录而非文件: {ref_path}"
            logger.error(error_msg)
            console.print(f"[bold red]错误:[/bold red] {error_msg}")
            return {"success": False, "error": error_msg}

        # 异步调用
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(link_to_memory(task_id, ref_path))
        loop.close()

        # 记录结果
        if "permalink" in result:
            logger.info(f"成功关联参考文档: {result['permalink']}")

            # 更新任务记录
            try:
                db_module = safe_import("src.db")
                repo_module = safe_import("src.db.repositories.task_repository")

                if db_module and repo_module:
                    session_factory = db_module.get_session_factory()
                    with session_factory() as session:
                        # 获取任务库
                        task_repo = repo_module.TaskRepository(session)
                        # 添加引用
                        add_time = datetime.now().isoformat()
                        file_name = os.path.basename(ref_path)
                        task_repo.add_memory_reference(task_id, result["permalink"], file_name, add_time)
                        logger.info(f"已更新任务 {task_id} 的Memory引用")
                else:
                    logger.warning("无法获取数据库模块，跳过更新任务引用")
            except Exception as e:
                logger.error(f"更新任务引用失败: {e}", exc_info=True)

            # 记录到任务日志
            append_to_task_log(task_id, "添加参考文档", {"文档路径": ref_path, "Memory链接": result["permalink"]})

            return result
        else:
            error_msg = result.get("error", "未知错误")
            logger.error(f"存储到Memory失败: {error_msg}")

            # 记录到任务日志
            append_to_task_log(task_id, "添加参考文档失败", {"文档路径": ref_path, "错误": error_msg})

            return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"处理参考文档时出错: {e}"
        logger.error(error_msg, exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {error_msg}")
        return {"success": False, "error": error_msg}
