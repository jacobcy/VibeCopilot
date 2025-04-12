#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

from .base_checker import BaseChecker, CheckResult


class CommandChecker(BaseChecker):
    def __init__(self, main_config: Dict, command_configs: Dict, category: Optional[str] = None, verbose: bool = False):
        super().__init__(main_config)
        self.command_configs = command_configs
        self.category = category
        self.verbose = verbose
        self.summary = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}

    def run_command(self, command: str) -> Tuple[int, str, str]:
        """运行命令并返回结果"""
        try:
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=self.config["performance"]["max_response_time"])
            return process.returncode, stdout.decode(), stderr.decode()
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)

    def check_command_help(self, cmd_name: str, cmd_config: Dict) -> Dict:
        """检查命令的帮助信息"""
        check_result = {"name": f"命令帮助检查: {cmd_name}", "status": "passed", "details": [], "suggestions": []}

        # 构建帮助命令
        cmd_prefix = self.config["common_config"].get("command_prefix", "vibecopilot")
        help_cmd = f"{cmd_prefix} {cmd_name} --help"

        # 运行帮助命令
        code, stdout, stderr = self.run_command(help_cmd)

        # 检查帮助命令是否成功
        if code != 0 or not stdout:
            check_result["status"] = "failed"
            check_result["details"].append("帮助命令执行失败")
            check_result["details"].append(f"错误信息: {stderr}")
            check_result["suggestions"].append("确保命令支持--help选项")
            return check_result

        # 检查帮助信息是否包含必要内容
        required_help_content = ["Usage:", "Options:"]
        for content in required_help_content:
            if content not in stdout:
                check_result["status"] = "warning"
                check_result["details"].append(f"帮助信息缺少: {content}")
                check_result["suggestions"].append(f"在帮助信息中添加 {content} 部分")

        # 检查子命令说明
        if cmd_config.get("subcommands"):
            for subcmd, subcmd_config in cmd_config["subcommands"].items():
                if subcmd_config.get("required", False) and subcmd not in stdout:
                    check_result["status"] = "warning"
                    check_result["details"].append(f"帮助信息缺少必要子命令说明: {subcmd}")
                    check_result["suggestions"].append(f"添加 {subcmd} 的说明")

        return check_result

    def check_command(self, cmd_name: str, cmd_config: Dict) -> List[Dict]:
        """检查单个命令"""
        results = []

        # 首先检查帮助信息
        help_result = self.check_command_help(cmd_name, cmd_config)
        results.append(help_result)

        # 更新统计
        self.summary["total"] += 1
        if help_result["status"] == "passed":
            self.summary["passed"] += 1
        elif help_result["status"] == "failed":
            self.summary["failed"] += 1
        elif help_result["status"] == "warning":
            self.summary["warnings"] += 1

        return results

    def check_command_group(self, group_name: str, group_config: Dict) -> List[Dict]:
        """检查命令组"""
        results = []

        for cmd_name, cmd_config in group_config["commands"].items():
            # 检查命令
            check_results = self.check_command(cmd_name, cmd_config)
            results.extend(check_results)

        return results

    def check(self) -> CheckResult:
        """运行所有命令检查"""
        try:
            all_checks = []
            # 确定要检查的命令组
            groups_to_check = []
            for group in self.config["command_groups"]:
                if self.category is None or group["name"] == self.category:
                    groups_to_check.append(group)

            # 检查每个命令组
            for group in groups_to_check:
                group_name = group["name"]
                if group_name in self.command_configs:
                    group_results = self.check_command_group(group_name, self.command_configs[group_name])
                    all_checks.extend(group_results)

            # 根据检查结果确定状态
            if self.summary["failed"] > 0:
                status = "failed"
            elif self.summary["warnings"] > 0:
                status = "warning"
            else:
                status = "passed"

            return CheckResult(
                status=status,
                details=[check["details"] for check in all_checks],
                suggestions=[check["suggestions"] for check in all_checks],
                metrics=self.summary,
            )

        except Exception as e:
            return CheckResult(status="failed", details=[f"检查过程出错: {str(e)}"], suggestions=["检查命令检查器配置和实现"], metrics=self.summary)
