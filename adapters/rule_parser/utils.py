"""
工具函数
提供规则解析的工具函数
"""

import logging
import os
from typing import Any, Dict, Optional

from adapters.rule_parser.parser_factory import create_parser, get_default_parser

# 创建日志记录器
logger = logging.getLogger(__name__)


def parse_rule_file(
    file_path: str, parser_type: Optional[str] = None, model: Optional[str] = None
) -> Dict[str, Any]:
    """解析规则文件

    Args:
        file_path: 规则文件路径
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的规则结构
    """
    logger.info(f"开始解析规则文件: {file_path}")
    logger.info(f"使用解析器: {parser_type or '默认'}, 模型: {model or '默认'}")

    try:
        # 获取解析器
        if parser_type:
            parser = create_parser(parser_type, model)
        else:
            parser = get_default_parser()

        logger.info(f"使用解析器类型: {parser.__class__.__name__}")

        # 解析规则文件
        result = parser.parse_rule_file(file_path)
        logger.info(f"规则文件解析成功: {file_path}")
        return result
    except Exception as e:
        logger.error(f"规则文件解析失败: {file_path}, 错误: {str(e)}", exc_info=True)
        raise


def parse_rule_content(
    content: str, context: str = "", parser_type: Optional[str] = None, model: Optional[str] = None
) -> Dict[str, Any]:
    """解析规则内容

    Args:
        content: 规则文本内容
        context: 上下文信息(文件路径等)
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的规则结构
    """
    logger.info(f"开始解析规则内容, 上下文: {context}")
    logger.info(f"使用解析器: {parser_type or '默认'}, 模型: {model or '默认'}")

    try:
        # 获取解析器
        if parser_type:
            parser = create_parser(parser_type, model)
        else:
            parser = get_default_parser()

        logger.info(f"使用解析器类型: {parser.__class__.__name__}")

        # 解析规则内容
        result = parser.parse_rule_content(content, context)
        logger.info("规则内容解析成功")
        return result
    except Exception as e:
        logger.error(f"规则内容解析失败, 错误: {str(e)}", exc_info=True)
        raise


def detect_rule_conflicts(
    rule_a: Dict[str, Any], rule_b: Dict[str, Any], parser_type: Optional[str] = None
) -> Dict[str, Any]:
    """检测两个规则之间的冲突

    Args:
        rule_a: 第一个规则
        rule_b: 第二个规则
        parser_type: 解析器类型

    Returns:
        Dict: 冲突分析结果
    """
    logger.info(f"开始检测规则冲突: {rule_a.get('id', 'unknown')} 与 {rule_b.get('id', 'unknown')}")
    logger.info(f"使用解析器: {parser_type or '默认'}")

    try:
        # 与规则解析使用相同的解析器
        if parser_type:
            parser = create_parser(parser_type)
        else:
            parser = get_default_parser()

        # 如果是OpenAI解析器，使用OpenAI客户端分析冲突
        if parser_type == "openai" or (not parser_type and isinstance(parser, OpenAIRuleParser)):
            try:
                from adapters.rule_parser.lib.openai_api import OpenAIClient
                from adapters.rule_parser.openai_rule_parser import OpenAIRuleParser

                logger.info("使用OpenAI进行冲突分析")
                client = OpenAIClient()

                # 构建包含两个规则的提示词
                prompt = _build_conflict_prompt(rule_a, rule_b)

                # 这里需要实现使用OpenAI分析冲突的逻辑
                # 需要调用OpenAI API进行分析
                data = {
                    "model": client.model,
                    "messages": [
                        {"role": "system", "content": "您是一个规则冲突分析专家。您的任务是分析两个规则是否存在语义冲突。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                }

                try:
                    # 发送请求到OpenAI API
                    logger.info("向OpenAI API发送冲突分析请求")
                    response = client._call_api(data)

                    # 如果成功获取分析结果
                    if isinstance(response, dict) and "has_conflict" in response:
                        logger.info(f"OpenAI冲突分析完成: {response['has_conflict']}")
                        return response
                    else:
                        logger.warning(f"OpenAI返回的冲突分析结果格式不正确: {response}")
                        return {
                            "has_conflict": False,
                            "conflict_type": "analysis_invalid",
                            "conflict_description": "OpenAI返回的分析结果格式不正确",
                        }
                except Exception as api_err:
                    logger.error(f"调用OpenAI API失败: {str(api_err)}")
                    return {
                        "has_conflict": False,
                        "conflict_type": "api_error",
                        "conflict_description": f"OpenAI API调用失败: {str(api_err)}",
                    }
            except ImportError as e:
                logger.error(f"导入OpenAI分析模块失败: {str(e)}")
                print(f"警告: 无法使用OpenAI进行冲突分析，将回退到简单检查。错误: {e}")
                return _simple_conflict_check(rule_a, rule_b)
            except Exception as e:
                logger.error(f"使用OpenAI分析冲突失败: {str(e)}", exc_info=True)
                print(f"警告: OpenAI冲突分析失败，将回退到简单检查。错误: {e}")
                # 如果OpenAI分析失败，回退到简单检查
                return _simple_conflict_check(rule_a, rule_b)

        # 否则使用简单的规则比较
        logger.info("使用简单检查进行冲突分析")
        return _simple_conflict_check(rule_a, rule_b)
    except Exception as e:
        logger.error(f"规则冲突检测失败: {str(e)}", exc_info=True)
        print(f"错误: 规则冲突检测失败: {e}")
        raise


def _build_conflict_prompt(rule_a: Dict[str, Any], rule_b: Dict[str, Any]) -> str:
    """构建冲突检测的提示词

    Args:
        rule_a: 第一个规则
        rule_b: 第二个规则

    Returns:
        str: 提示词
    """
    return f"""
    分析以下两个规则之间的潜在冲突:

    规则1 (ID: {rule_a.get('id', 'unknown')}, 名称: {rule_a.get('name', 'unknown')}):
    {rule_a.get('content', '')}

    规则2 (ID: {rule_b.get('id', 'unknown')}, 名称: {rule_b.get('name', 'unknown')}):
    {rule_b.get('content', '')}

    规则2是否与规则1在行动、条件、要求或结果方面存在矛盾、覆盖或不一致？
    (例如，两者都定义了存储位置但指定了不同的路径，如'doc/'与'dev/')

    以JSON格式返回结果，应包含以下字段:
    - has_conflict: 布尔值，表示是否存在冲突
    - conflict_type: 冲突类型(如direct_contradiction, indirect_conflict, priority_conflict, overlap_conflict, terminology_conflict, none)
    - conflict_description: 详细描述冲突的具体内容，如果存在

    只返回JSON，不要有其他解释。
    """


def _simple_conflict_check(rule_a: Dict[str, Any], rule_b: Dict[str, Any]) -> Dict[str, Any]:
    """简单的规则冲突检查

    Args:
        rule_a: 第一个规则
        rule_b: 第二个规则

    Returns:
        Dict: 冲突检查结果
    """
    # 检查基本冲突：相同ID但内容不同
    if rule_a.get("id") == rule_b.get("id") and rule_a.get("content") != rule_b.get("content"):
        logger.info(f"检测到ID冲突: {rule_a.get('id')}")
        return {
            "has_conflict": True,
            "conflict_type": "duplicate_id",
            "conflict_description": f"规则ID '{rule_a.get('id')}' 相同但内容不同",
        }

    # 检查globs冲突
    a_globs = set(rule_a.get("globs", []))
    b_globs = set(rule_b.get("globs", []))

    if a_globs and b_globs and a_globs.intersection(b_globs):
        intersection = a_globs.intersection(b_globs)
        logger.info(f"检测到glob模式重叠: {intersection}")
        return {
            "has_conflict": True,
            "conflict_type": "glob_overlap",
            "conflict_description": f"规则glob模式重叠: {intersection}",
        }

    # 未检测到简单冲突
    logger.info("简单检查未发现冲突")
    return {"has_conflict": False, "conflict_type": "none", "conflict_description": "简单检查未发现冲突"}
