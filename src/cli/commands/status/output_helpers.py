"""
状态命令输出助手模块

提供命令输出格式化功能
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def output_result(result: Dict[str, Any], output_format: str, result_type: str, verbose: bool = False) -> None:
    """输出结果

    Args:
        result: 结果数据
        output_format: 输出格式 (text或json)
        result_type: 结果类型
        verbose: 是否显示详细信息
    """
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 文本格式
        # Check for actual error value before printing as an error
        if result and result.get("error"):
            # Assuming a convention that if 'error' key has a truthy value, it's an error message to print.
            # If 'error' is present but None or empty, it might not be an error to display this way.
            print(f"❌ 错误: {result['error']}")
            # Optionally, if there are suggestions and it's an error, print them
            if isinstance(result.get("suggestions"), list) and result["suggestions"]:
                print("💡 建议:")
                for suggestion in result["suggestions"]:
                    print(f"  - {suggestion}")
            return  # Stop further processing if an error was handled

        if result_type == "system":
            print_system_status(result, verbose)
        elif result_type == "domain":
            # Pass along the result, print_domain_status will also need to handle 'error': None correctly
            print_domain_status(result, verbose)
        else:
            print_generic_status(result, verbose)


def print_system_status(status: Dict[str, Any], verbose: bool = False) -> None:
    """打印系统状态

    Args:
        status: 系统状态数据
        verbose: 是否显示详细信息
    """
    # Check for actual error value
    if status and status.get("error"):
        print(f"❌ 错误: {status['error']}")
        return

    # 打印总体健康状态
    health = status.get("health", {})
    health_score = health.get("score", 0)
    health_status = health.get("status", "未知")
    health_color = _get_health_color(health_status)

    print(f"{health_color}系统健康度: {health_score}% ({health_status})\033[0m")

    # 打印项目状态
    project = status.get("project", {})
    print(f"\n📊 项目状态:")
    print(f"  名称: {project.get('name', '未设置')}")
    print(f"  阶段: {project.get('phase', '未设置')}")
    print(f"  进度: {project.get('progress', 0)}%")

    # 打印域状态
    domains = status.get("domains", [])
    if domains:
        print("\n📌 各域状态:")
        for domain in domains:
            domain_name = domain.get("name", "未知")
            domain_health = domain.get("health", {})
            domain_status = domain_health.get("status", "未知")
            domain_color = _get_health_color(domain_status)

            print(f"  {domain_color}{domain_name}: {domain_health.get('score', 0)}% ({domain_status})\033[0m")

            # 如果是详细模式，显示更多信息
            if verbose:
                issues = domain.get("issues", [])
                if issues:
                    print("    问题:")
                    for issue in issues[:3]:  # 仅显示前3个问题
                        print(f"      - {issue.get('message', '')}")

                    if len(issues) > 3:
                        print(f"      ... 还有 {len(issues) - 3} 个问题")


def print_domain_status(status: Dict[str, Any], verbose: bool = False) -> None:
    """打印域状态

    Args:
        status: 域状态数据
        verbose: 是否显示详细信息
    """
    # Check for actual error value. If 'error' key exists AND has a truthy value, it's an error.
    # If 'error' key exists but its value is None or empty string, it implies no error.
    if status and status.get("error"):
        print(f"❌ 错误: {status['error']}")
        return

    # If we are here, status_data['error'] was None or not present, so proceed with normal printing.
    # ... (the rest of your existing print_domain_status logic for successful cases)
    # Example snippet of how it might continue:
    name = status.get("domain", status.get("name", "未知领域"))  # Try 'domain' key first for consistency
    active_id = status.get("active_roadmap_id", "未设置")
    current_status = status.get("status", "未知")
    health_score = status.get("health", "未知")  # Assuming health might be a string like 'good'

    print(f"✅ {name} 状态:")
    print(f"  当前活动路线图 ID: {active_id}")
    print(f"  整体状态: {current_status}")
    print(f"  健康度: {health_score}")

    entity_data = status.get("entity_data")
    if entity_data and isinstance(entity_data, dict):
        print(
            f"  当前查看: {entity_data.get('title', entity_data.get('id', 'N/A'))} ({status.get('check_type', 'N/A')}:{status.get('element_id', active_id)})"
        )
        print(f"    详细状态: {entity_data.get('status', 'N/A')}")
        if verbose:
            print(f"    描述: {entity_data.get('description', 'N/A')}")
            print(f"    创建于: {entity_data.get('created_at', 'N/A')}")
            print(f"    更新于: {entity_data.get('updated_at', 'N/A')}")

    children = status.get("children")
    if children and isinstance(children, list):
        child_type_name = "史诗" if status.get("check_type") == "roadmap" else "故事"
        print(f"  包含的 {child_type_name}:")
        for child in children:
            print(f"    - {child.get('title', child.get('id', 'N/A'))} (状态: {child.get('status', 'N/A')})")

    # 打印问题
    issues = status.get("issues", [])
    if issues:
        print("\n⚠️ 检测到的问题:")
        for issue in issues:
            issue_level = issue.get("level", "info").upper()
            issue_color = _get_level_color(issue_level)
            print(f"  {issue_color}{issue_level}\033[0m: {issue.get('message', '')}")

            # 如果是详细模式，显示更多信息
            if verbose and "details" in issue:
                print(f"    详情: {issue['details']}")

    # 如果是详细模式，显示更多信息
    if verbose:
        metrics = status.get("metrics", {})
        if metrics:
            print("\n📈 指标:")
            for key, value in metrics.items():
                print(f"  {key}: {value}")

        recommendations = status.get("recommendations", [])
        if recommendations:
            print("\n💡 建议:")
            for recommendation in recommendations:
                print(f"  - {recommendation}")


def print_generic_status(status: Dict[str, Any], verbose: bool = False) -> None:
    """打印通用状态

    Args:
        status: 状态数据
        verbose: 是否显示详细信息
    """
    # Check for actual error value
    if status and status.get("error"):
        print(f"❌ 错误: {status['error']}")
        return

    # 打印状态名称
    name = status.get("name", "状态")
    print(f"📊 {name}:")

    # 打印状态数据
    for key, value in status.items():
        if key in ["name", "error"]:
            continue

        if isinstance(value, dict):
            print(f"\n  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        elif isinstance(value, list):
            print(f"\n  {key}:")
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        print(f"    {k}: {v}")
                    print("")
                else:
                    print(f"    - {item}")
        else:
            print(f"  {key}: {value}")


def _get_health_color(status: str) -> str:
    """获取健康状态颜色

    Args:
        status: 健康状态

    Returns:
        str: ANSI颜色代码
    """
    status = status.lower() if status else ""
    if status in ["good", "health", "健康"]:
        return "\033[92m"  # 绿色
    elif status in ["warning", "warn", "警告"]:
        return "\033[93m"  # 黄色
    elif status in ["error", "bad", "critical", "错误", "严重"]:
        return "\033[91m"  # 红色
    else:
        return "\033[94m"  # 蓝色


def _get_level_color(level: str) -> str:
    """获取级别颜色

    Args:
        level: 级别名称

    Returns:
        str: ANSI颜色代码
    """
    level = level.lower() if level else ""
    if level in ["info", "信息"]:
        return "\033[94m"  # 蓝色
    elif level in ["warning", "warn", "警告"]:
        return "\033[93m"  # 黄色
    elif level in ["error", "错误"]:
        return "\033[91m"  # 红色
    elif level in ["critical", "严重"]:
        return "\033[95m"  # 紫色
    else:
        return "\033[0m"  # 默认
