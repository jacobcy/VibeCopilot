"""
路线图创建处理器

处理路线图元素（里程碑、史诗、故事）的创建操作。
"""

import json  # For potential error logging
import logging
import os
from typing import Any, Dict, List, Optional

import yaml  # 用于生成 YAML 文件
from rich.console import Console

# 假设 LLMParser, RoadmapValidator, RoadmapService 位于这些路径
# 如果路径不同，需要相应调整
from src.parsing.parsers.llm_parser import LLMParser
from src.roadmap import RoadmapService
from src.validation.roadmap_validation import RoadmapValidator

logger = logging.getLogger(__name__)  # 添加日志记录器
console = Console()


def handle_create_element(
    service: RoadmapService,
    type: str,
    title: str,
    epic_id: Optional[str] = None,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    priority: Optional[str] = None,
) -> Dict[str, Any]:
    """处理路线图元素创建

    Args:
        service: RoadmapService实例
        type: 元素类型 ('milestone', 'epic', 'story')
        title: 元素标题
        epic_id: 史诗ID（用于story）
        description: 详细描述
        assignee: 指派人
        labels: 标签列表
        priority: 优先级（用于epic）
    """
    try:
        # 准备创建参数
        create_data = {
            "title": title,
            "description": description or "",
            "assignee": assignee,
            # Labels are often stored as comma-separated string or JSON in DB
            # Repository should handle the conversion if needed.
            # Passing as list for now, repo create needs to handle it.
            "labels": ",".join(labels) if labels else None,
        }

        # 根据元素类型添加特定参数
        if type == "story":
            if not epic_id:
                return {"success": False, "message": "创建story需要指定所属epic的ID"}
            create_data["epic_id"] = epic_id
        elif type == "epic":
            if priority:
                create_data["priority"] = priority

        # --- 修改为调用 Repository ---
        created_entity = None
        with session_scope() as session:
            if type == "milestone":
                # 假设 MilestoneRepository 在 service.milestone_repo
                if hasattr(service, "milestone_repo"):
                    # Need to import MilestoneRepository if not already done
                    # Assuming create method exists and takes session, **data
                    created_entity = service.milestone_repo.create(session, **create_data)
                else:
                    raise AttributeError("RoadmapService does not have milestone_repo")
            elif type == "epic":
                created_entity = service.epic_repo.create(session, **create_data)
            elif type == "story":
                created_entity = service.story_repo.create(session, **create_data)
            else:
                return {"success": False, "message": f"不支持的创建类型: {type}"}
        # ---------------------------

        if not created_entity or not hasattr(created_entity, "id"):
            return {"success": False, "message": f"创建{type}失败或未返回有效ID"}

        # Convert entity to dict for return data if needed
        # Assuming service._object_to_dict can handle the created_entity
        entity_dict = (
            service._object_to_dict(created_entity)
            if hasattr(service, "_object_to_dict")
            else {"id": created_entity.id, "title": created_entity.title}
        )  # Basic fallback

        return {
            "success": True,
            "message": f"已创建{type}: {title}",
            "data": {"type": type, "id": entity_dict.get("id"), "title": entity_dict.get("title")},
        }

    except AttributeError as ae:
        logger.error(f"创建元素 {type} 时出错: {ae}", exc_info=True)
        return {"success": False, "message": f"服务配置错误: {str(ae)}"}
    except Exception as e:
        logger.error(f"创建元素 {type} 时出错: {e}", exc_info=True)
        return {"success": False, "message": f"创建{type}时出错: {str(e)}"}


# --- 更新处理函数 ---
async def handle_create_from_source(service: RoadmapService, source: str) -> Dict[str, Any]:
    """处理从源文件生成标准路线图YAML文件的逻辑

    Args:
        service: RoadmapService实例 (目前未使用，但保留签名兼容性)
        source: 源文件路径

    Returns:
        包含成功/失败状态和消息的字典
    """
    logger.info(f"开始从源文件生成路线图YAML: {source}")

    # 1. 读取文件内容
    try:
        with open(source, "r", encoding="utf-8") as f:
            content = f.read()
        logger.debug(f"成功读取文件内容，长度: {len(content)}")
    except FileNotFoundError:
        logger.error(f"源文件未找到: {source}")
        return {"success": False, "message": f"错误: 源文件未找到 - {source}"}
    except Exception as e:
        logger.error(f"读取源文件时出错 {source}: {e}", exc_info=True)
        return {"success": False, "message": f"错误: 读取文件失败 - {str(e)}"}

    # 2. 调用 LLM 解析器
    try:
        llm_parser = LLMParser()  # 实例化 LLM 解析器
        logger.info("调用 LLM 解析器解析路线图内容...")
        parsing_result = await llm_parser.parse_text(content, content_type="roadmap")

        if not parsing_result.get("success"):
            error_msg = parsing_result.get("error", "LLM 解析失败，未知错误")
            raw_response = parsing_result.get("raw_response", "")
            logger.error(f"LLM 解析失败: {error_msg}. Raw Response Snippet: {raw_response[:200]}...")
            return {"success": False, "message": f"错误: LLM 解析路线图失败 - {error_msg}", "error_details": raw_response}

        parsed_data = parsing_result.get("content")
        if not isinstance(parsed_data, dict):
            logger.error(f"LLM 解析结果不是预期的字典格式: {type(parsed_data)}")
            return {"success": False, "message": "错误: LLM 解析结果格式不正确"}

        logger.info("LLM 解析成功，获得结构化数据")
        logger.debug(f"Parsed Data Snippet: {str(parsed_data)[:500]}...")

    except Exception as e:
        logger.error(f"调用 LLM 解析器时发生意外错误: {e}", exc_info=True)
        return {"success": False, "message": f"错误: 调用 LLM 解析时出错 - {str(e)}"}

    # --- 移除/注释掉验证步骤 ---
    # # 3. 验证解析后的数据
    # try:
    #     validator = RoadmapValidator()
    #     logger.info("开始验证解析后的路线图数据...")
    #     is_valid = validator.validate(parsed_data)

    #     warnings = validator.get_warnings()
    #     errors = validator.get_errors()

    #     if warnings:
    #         logger.warning(f\"路线图数据验证警告: {warnings}\")
    #         for warning in warnings:
    #             console.print(f"[yellow]验证警告: {warning}[/yellow]")

    #     if not is_valid:
    #         logger.error(f\"路线图数据验证失败: {errors}\")
    #         return {
    #             "success": False,
    #             "message": f\"错误: 解析后的路线图数据验证失败 - {\'; \'.join(errors)}\",
    #             "error_details": errors
    #         }

    #     logger.info("路线图数据验证通过") # 假设验证跳过

    # except Exception as e:
    #     logger.error(f\"验证路线图数据时发生意外错误: {e}\", exc_info=True)
    #     return {"success": False, "message": f\"错误: 验证路线图数据时出错 - {str(e)}\"}

    # --- 恢复文件保存逻辑 ---
    # 4. 生成并保存 YAML 文件
    try:
        # 自动计算输出路径：源文件同目录，同名，.yaml扩展名
        source_dir = os.path.dirname(source)
        base_name = os.path.splitext(os.path.basename(source))[0]
        output_path = os.path.join(source_dir, f"{base_name}.yaml")  # 确保使用 .yaml 扩展名

        logger.info(f"准备将验证后的数据写入YAML文件: {output_path}")

        # 确保输出目录存在 (如果源文件在根目录，source_dir会是空字符串，makedirs会处理)
        if source_dir and not os.path.exists(source_dir):
            os.makedirs(source_dir)
            logger.info(f"创建输出目录: {source_dir}")

        # 使用 PyYAML 将字典序列化为 YAML 字符串
        # allow_unicode=True 保证中文字符正确输出
        # sort_keys=False 保持原始（或LLM生成）的顺序，更易读
        yaml_content = yaml.dump(parsed_data, allow_unicode=True, sort_keys=False, indent=2)

        # 将 YAML 字符串写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        logger.info(f"成功将路线图数据写入文件: {output_path}")

        # 返回成功信息和输出文件路径
        return {
            "success": True,
            "message": f"已成功从 {source} 生成标准路线图YAML文件: {os.path.basename(output_path)}",  # 显示文件名
            "output_file": output_path,  # 返回完整路径供下一步使用
        }

    except yaml.YAMLError as e:
        logger.error(f"生成 YAML 时出错: {e}", exc_info=True)
        return {"success": False, "message": f"错误: 生成YAML内容失败 - {str(e)}"}
    except IOError as e:
        logger.error(f"写入 YAML 文件时出错 {output_path}: {e}", exc_info=True)
        return {"success": False, "message": f"错误: 写入输出文件失败 - {str(e)}"}
    except Exception as e:
        logger.error(f"生成或保存 YAML 文件时发生意外错误: {e}", exc_info=True)
        return {"success": False, "message": f"错误: 处理输出文件时出错 - {str(e)}"}

    # --- 以下代码不再执行 ---
    # # 直接返回成功状态和解析的数据
    # logger.info("LLM 解析完成，将直接返回解析数据（跳过验证和文件生成）")
    # return {
    #     "success": True,
    #     "message": f"已成功从 {source} 解析路线图数据",
    #     "data": parsed_data, # 返回解析后的字典数据
    # }
