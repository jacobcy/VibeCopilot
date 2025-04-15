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

# 这里不再直接导入，改为动态导入以避免循环依赖
# from src.db.repositories.task_repository import TaskRepository
# from src.db import get_session_factory

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
    metadata = {
        "name": file_name,
        "tags": f"reference,task:{task_id}",
        "related_task": task_id,
        "file_path": file_path,
        "type": "reference",  # 确保类型信息正确
        "title": file_name,  # 确保标题信息正确
    }

    # 使用Memory系统存储
    memory_module = safe_import("src.memory")
    if not memory_module:
        return {"success": False, "error": "导入Memory模块失败"}

    try:
        # 使用特定的配置初始化实体管理器
        entity_manager_config = {
            "vector_store": {
                "default_folder": "references",
                "default_tags": "reference,task",
            }
        }
        entity_manager = memory_module.EntityManager(entity_manager_config)
    except Exception as e:
        detailed_error = f"初始化EntityManager失败: {type(e).__name__}: {str(e)}"
        logger.error(detailed_error, exc_info=True)
        return {"success": False, "error": detailed_error}

    try:
        # 存储到references文件夹
        logger.info(f"开始存储文件到Memory: {file_name}")

        # 查找任务相关的现有引用
        db_module = safe_import("src.db")
        repo_module = safe_import("src.db.repositories.task_repository")

        if not db_module or not repo_module:
            logger.warning("导入数据库模块失败，将创建新的引用而非更新")
        else:
            try:
                session_factory = db_module.get_session_factory()
                with session_factory() as session:
                    task_repo = repo_module.TaskRepository(session)
                    task = task_repo.get_by_id(task_id)

                    # 如果任务存在且有相同文件路径的引用，获取其permalink用于更新
                    if task and task.memory_references:
                        existing_permalink = None
                        for ref in task.memory_references:
                            # 尝试从permalink中提取实体属性
                            try:
                                # 获取实体内容，检查文件路径是否匹配
                                entity_result = await entity_manager.get_entity(ref.memory_permalink)
                                if entity_result and entity_result.get("properties", {}).get("file_path") == file_path:
                                    existing_permalink = ref.memory_permalink
                                    logger.info(f"找到现有引用，将进行更新: {existing_permalink}")
                                    break
                            except Exception as e:
                                logger.warning(f"获取实体内容失败: {e}")

                        # 如果找到现有引用，进行更新
                        if existing_permalink:
                            logger.info(f"更新现有引用: {existing_permalink}")
                            result = await entity_manager.update_entity(permalink=existing_permalink, properties=metadata, content=content)
                            logger.info(f"成功更新引用: {result.get('permalink', '未获取到permalink')}")

                            # 更新成功，直接返回结果
                            append_to_task_log(task_id, "更新参考文档", {"文档路径": file_path, "Memory链接": result["permalink"]})

                            return {"success": True, "permalink": result["permalink"], "updated": True}
            except Exception as e:
                logger.warning(f"查找现有引用失败: {e}")

        # 如果没有找到现有引用或者查找失败，创建新的引用
        result = await entity_manager.create_entity(entity_type="reference", properties=metadata, content=content)

        logger.info(f"文件已存储到Memory，获取到permalink: {result.get('permalink', '未获取到permalink')}")

        if not result.get("permalink"):
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
                add_result = task_repo.add_memory_reference(task_id, result["permalink"], metadata["name"])

                if add_result:
                    # 记录到任务日志
                    append_to_task_log(task_id, "添加参考文档", {"文档路径": file_path, "Memory链接": result["permalink"]})

                    return {"success": True, "permalink": result["permalink"]}
                else:
                    error_msg = "文档可能已存在或任务不存在"
                    logger.warning(error_msg)
                    return {"success": False, "error": error_msg, "permalink": result["permalink"]}
        except Exception as e:
            logger.error(f"添加Memory引用失败: {e}")
            return {"success": False, "error": f"添加Memory引用失败: {e}", "permalink": result.get("permalink")}

    except Exception as e:
        detailed_error = f"存储到Memory失败: {type(e).__name__}: {str(e)}"
        logger.error(detailed_error, exc_info=True)
        # 仍然记录到任务日志，但标记为失败
        append_to_task_log(task_id, "添加参考文档失败", {"文档路径": file_path, "错误": detailed_error})
        return {"success": False, "error": detailed_error}


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

        # 检查MCP工具是否可用，增加对工具可用性的明确检查
        try:
            # 尝试导入MCP工具
            from mcp_basic_memory_write_note import mcp_basic_memory_write_note

            MCP_TOOLS_AVAILABLE = True
        except ImportError:
            MCP_TOOLS_AVAILABLE = False
            warning_msg = "MCP Basic Memory工具在命令行环境中不可用，将生成模拟数据"
            logger.warning(warning_msg)
            console.print(f"[bold yellow]警告:[/bold yellow] {warning_msg}")
            console.print("[bold yellow]注意:[/bold yellow] 文档未真正存储到Memory，只生成了模拟链接")
            console.print("[bold yellow]建议:[/bold yellow] 在Cursor IDE环境中执行此操作以实际存储文档")

            # 生成模拟数据，但明确标记为模拟
            file_name = os.path.basename(ref_path)
            simulated_permalink = f"memory://references/{file_name.replace(' ', '_').lower()}"
            return {"success": True, "permalink": simulated_permalink, "simulated": True, "warning": "仅生成模拟链接，文档未实际存储"}

        # 读取文件内容
        try:
            with open(ref_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试以二进制方式读取
            logger.warning(f"无法以UTF-8编码读取文件，尝试二进制方式")
            with open(ref_path, "rb") as f:
                content = f"无法显示二进制内容。文件路径: {ref_path}"
        except Exception as e:
            error_msg = f"读取文件失败: {e}"
            logger.error(error_msg)
            console.print(f"[bold red]错误:[/bold red] {error_msg}")
            return {"success": False, "error": error_msg}

        # 提取文件名和类型
        file_name = os.path.basename(ref_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # 准备元数据
        metadata = {
            "file_path": ref_path,
            "file_name": file_name,
            "file_type": file_ext,
            "task_id": task_id,
            "added_at": datetime.now().isoformat(),
        }

        # 添加文件类型特定元数据
        if file_ext in [".md", ".txt", ".rst"]:
            # 文本文件
            metadata["content_type"] = "text"
        elif file_ext in [".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rust"]:
            # 代码文件
            metadata["content_type"] = "code"
            metadata["language"] = file_ext[1:]  # 去掉前面的点
        elif file_ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
            # 图像文件
            metadata["content_type"] = "image"
            content = f"图像文件，无法直接显示内容。文件路径: {ref_path}"
        elif file_ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]:
            # 文档文件
            metadata["content_type"] = "document"
            metadata["format"] = file_ext[1:]
            content = f"文档文件，无法直接显示内容。文件路径: {ref_path}"
        else:
            # 其他文件
            metadata["content_type"] = "unknown"

        # 获取文件的基本信息
        try:
            stat_info = os.stat(ref_path)
            metadata["file_size"] = stat_info.st_size
            metadata["modified_time"] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            metadata["created_time"] = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
        except Exception as e:
            logger.warning(f"获取文件信息失败: {e}")

        # 处理标题
        if metadata["content_type"] == "code" or metadata["content_type"] == "text":
            # 尝试从内容的第一行提取标题
            first_line = content.strip().split("\n")[0].strip()
            if first_line.startswith("# "):
                title = first_line[2:].strip()  # Markdown标题
            elif first_line.startswith('"""') or first_line.startswith("'''"):
                # Python文档字符串
                title = first_line.strip("\"'").strip()
            elif len(first_line) <= 100 and not first_line.startswith("import ") and not first_line.startswith("from "):
                title = first_line
            else:
                title = file_name
        else:
            title = file_name

        # 设置元数据标题
        metadata["title"] = title

        # 根据文件内容设置标签
        tags = ["reference", task_id]
        if metadata["content_type"]:
            tags.append(metadata["content_type"])
        if file_ext and file_ext[1:]:  # 去掉前面的点
            tags.append(file_ext[1:])
        metadata["tags"] = ",".join(tags)

        # 创建EntitiyManager并存储实体
        from src.memory import EntityManager

        entity_manager = EntityManager()

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
                        task_repo.add_memory_reference(task_id, result["permalink"], metadata["title"], metadata["added_at"])
                        logger.info(f"已更新任务 {task_id} 的Memory引用")
                else:
                    logger.warning("无法获取数据库模块，跳过更新任务引用")
            except Exception as e:
                logger.error(f"更新任务引用失败: {e}", exc_info=True)

            # 记录到任务日志
            append_to_task_log(task_id, "添加参考文档", {"文档路径": ref_path, "Memory链接": result["permalink"]})

            # 如果有模拟标记，添加警告信息
            if result.get("simulated", False):
                console.print("[bold yellow]注意:[/bold yellow] 只生成了模拟链接，文档未实际存储到Memory")
                console.print("[bold yellow]建议:[/bold yellow] 在Cursor IDE环境中执行此操作以实际存储文档")

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
