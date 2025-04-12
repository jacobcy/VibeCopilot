"""
工作流会话命令行接口命令定义

提供工作流会话管理的命令行接口定义。
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Union

import click

from src.flow_session.cli.handlers import (
    handle_close_session,
    handle_create_session,
    handle_delete_session,
    handle_list_sessions,
    handle_show_session,
)


# 通用选项装饰器
def common_options(function):
    """添加通用命令选项的装饰器"""
    function = click.option("--verbose", "-v", is_flag=True, help="显示详细信息")(function)

    function = click.option("--agent-mode", is_flag=True, help="启用程序处理模式，输出标准化JSON格式")(function)

    return function


def format_option(function):
    """添加格式选项的装饰器"""
    function = click.option(
        "--format",
        "-f",
        type=click.Choice(["text", "json"], case_sensitive=False),
        default="text",
        help="输出格式，支持text和json",
    )(function)

    return function


# 命令函数接口，作为外部调用的入口点
def list_sessions(
    status: Optional[str] = None,
    workflow: Optional[str] = None,
    format: str = "text",
    verbose: bool = False,
    agent_mode: bool = False,
):
    """列出所有活动会话"""
    return handle_list_sessions(status, workflow, format, verbose, agent_mode)


def show_session(session_id: str, format: str = "text", verbose: bool = False, agent_mode: bool = False):
    """显示会话详情"""
    return handle_show_session(session_id, format, verbose, agent_mode)


def create_session(workflow_id: str, name: Optional[str] = None, task_id: Optional[str] = None, verbose: bool = False, agent_mode: bool = False):
    """创建新会话"""
    return handle_create_session(workflow_id, name, task_id, verbose, agent_mode)


def close_session(session_id: str, reason: Optional[str] = None, force: bool = False, verbose: bool = False, agent_mode: bool = False):
    """结束会话"""
    return handle_close_session(session_id, reason, force, verbose, agent_mode)


def delete_session(session_id: str, force: bool = False, verbose: bool = False, agent_mode: bool = False):
    """删除会话"""
    return handle_delete_session(session_id, force, verbose, agent_mode)


# 命令行接口定义
@click.group(name="session")
def session_group():
    """工作流会话管理命令"""
    pass


@session_group.command(name="list")
@click.option("--status", "-s", type=str, help="按状态过滤(ACTIVE/PAUSED/COMPLETED/CLOSED)")
@click.option("--workflow", "-w", type=str, help="按工作流ID过滤")
@format_option
@common_options
def list_sessions_cmd(status, workflow, format, verbose, agent_mode):
    """列出所有工作流会话

    查看系统中所有的工作流会话，可以按状态和工作流ID进行过滤。
    """
    return list_sessions(status, workflow, format, verbose, agent_mode)


@session_group.command(name="show")
@click.argument("session_id", type=str)
@format_option
@common_options
def show_session_cmd(session_id, format, verbose, agent_mode):
    """显示指定会话的详细信息

    SESSION_ID: 会话ID
    """
    return show_session(session_id, format, verbose, agent_mode)


@session_group.command(name="create")
@click.argument("workflow_id", type=str)
@click.option("--name", "-n", type=str, help="会话名称")
@click.option("--task", "-t", type=str, help="关联的任务ID (会话将专注于此任务)")
@common_options
def create_session_cmd(workflow_id, name, task, verbose, agent_mode):
    """创建新的工作流会话

    WORKFLOW_ID: 工作流ID
    """
    return create_session(workflow_id, name, task, verbose, agent_mode)


@session_group.command(name="close")
@click.argument("session_id", type=str)
@click.option("--reason", help="结束原因")
@click.option("--force", "-f", is_flag=True, help="强制结束，不提示确认")
@common_options
def close_session_cmd(session_id, reason, force, verbose, agent_mode):
    """结束指定的工作流会话

    SESSION_ID: 会话ID
    """
    return close_session(session_id, reason, force, verbose, agent_mode)


@session_group.command(name="delete")
@click.argument("session_id", type=str)
@click.option("--force", "-f", is_flag=True, help="强制删除，不提示确认")
@common_options
def delete_session_cmd(session_id, force, verbose, agent_mode):
    """删除指定的工作流会话

    SESSION_ID: 会话ID
    """
    return delete_session(session_id, force, verbose, agent_mode)


def register_commands(parser):
    """
    注册会话管理命令

    Args:
        parser: 命令解析器或命令组

    Returns:
        注册后的解析器或None
    """
    # 检测是否是argparse子解析器
    if isinstance(parser, argparse.ArgumentParser):
        # 创建session子命令的子解析器
        session_subparsers = parser.add_subparsers(dest="action", help="会话操作")

        # 创建list子命令
        list_parser = session_subparsers.add_parser("list", help="列出所有会话")
        list_parser.add_argument("--status", "-s", help="按状态筛选(ACTIVE/PAUSED/COMPLETED/CLOSED)")
        list_parser.add_argument("--workflow", "-w", help="按工作流ID筛选")
        list_parser.add_argument("--format", "-f", choices=["json", "text"], default="text", help="输出格式")
        list_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
        list_parser.add_argument("--agent-mode", action="store_true", help="程序处理模式，输出JSON格式")

        # 创建show子命令
        show_parser = session_subparsers.add_parser("show", help="显示会话详情")
        show_parser.add_argument("session_id", help="会话ID")
        show_parser.add_argument("--format", "-f", choices=["json", "text"], default="text", help="输出格式")
        show_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
        show_parser.add_argument("--agent-mode", action="store_true", help="程序处理模式，输出JSON格式")

        # 创建create子命令
        create_parser = session_subparsers.add_parser("create", help="创建新会话")
        create_parser.add_argument("workflow_id", help="工作流ID")
        create_parser.add_argument("--name", "-n", help="会话名称")
        create_parser.add_argument("--task", "-t", help="关联的任务ID (会话将专注于此任务)")
        create_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
        create_parser.add_argument("--agent-mode", action="store_true", help="程序处理模式，输出JSON格式")

        # 创建close子命令
        close_parser = session_subparsers.add_parser("close", help="结束会话")
        close_parser.add_argument("session_id", help="会话ID")
        close_parser.add_argument("--reason", help="结束原因")
        close_parser.add_argument("--force", "-f", action="store_true", help="强制结束，不提示确认")
        close_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
        close_parser.add_argument("--agent-mode", action="store_true", help="程序处理模式，输出JSON格式")

        # 创建delete子命令
        delete_parser = session_subparsers.add_parser("delete", help="删除会话")
        delete_parser.add_argument("session_id", help="会话ID")
        delete_parser.add_argument("--force", "-f", action="store_true", help="强制删除，不提示确认")
        delete_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
        delete_parser.add_argument("--agent-mode", action="store_true", help="程序处理模式，输出JSON格式")

        return parser
    else:
        # 如果是click组，直接添加命令组
        parser.add_command(session_group)


if __name__ == "__main__":
    """命令行入口点"""
    session_group()
