#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


class CommandChecker:
    def __init__(self, main_config: Dict, command_configs: Dict):
        self.main_config = main_config
        self.command_configs = command_configs
        self.results = {"checks": [], "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0}}

    def run_command(self, command: str) -> Tuple[int, str, str]:
        """运行命令并返回结果"""
        try:
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=self.main_config["performance"]["max_response_time"])
            return process.returncode, stdout.decode(), stderr.decode()
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)

    def check_command(self, cmd_name: str, cmd_config: Dict) -> Dict:
        """检查单个命令"""
        check_result = {"name": f"命令检查: {cmd_name}", "status": "passed", "details": [], "suggestions": []}

        # 构建完整命令
        cmd_prefix = self.main_config["common_config"].get("command_prefix", "vibecopilot")
        full_cmd = f"{cmd_prefix} {cmd_name}"

        # 运行命令
        code, stdout, stderr = self.run_command(full_cmd)

        # 检查返回码
        if code != 0:
            check_result["status"] = "failed"
            check_result["details"].append(f"命令返回错误码: {code}")
            check_result["details"].append(f"错误信息: {stderr}")
            check_result["suggestions"].append("检查命令实现和错误处理")
            return check_result

        # 检查预期输出
        for expected in cmd_config.get("expected_output", []):
            if expected not in stdout:
                check_result["status"] = "failed"
                check_result["details"].append(f"未找到预期输出: {expected}")
                check_result["suggestions"].append(f"确保命令输出包含: {expected}")

        # 检查响应时间
        if cmd_config.get("timeout"):
            # TODO: 实现响应时间检查
            pass

        # 检查输出格式
        if self.main_config["output_format"]["check_json_format"] and "--json" in cmd_name:
            try:
                import json

                json.loads(stdout)
            except json.JSONDecodeError:
                check_result["status"] = "failed"
                check_result["details"].append("JSON输出格式无效")
                check_result["suggestions"].append("检查JSON输出格式")

        # 检查帮助信息
        if self.main_config["output_format"]["check_help_format"]:
            help_cmd = f"{full_cmd} --help"
            help_code, help_stdout, help_stderr = self.run_command(help_cmd)
            if help_code != 0 or not help_stdout:
                check_result["status"] = "warning"
                check_result["details"].append("帮助信息检查失败")
                check_result["suggestions"].append("确保命令支持--help选项")

        # 添加成功信息
        if check_result["status"] == "passed":
            check_result["details"].append("命令执行成功")

        return check_result

    def check_command_group(self, group_name: str, group_config: Dict) -> List[Dict]:
        """检查命令组"""
        results = []

        for cmd_name, cmd_config in group_config["commands"].items():
            # 检查命令
            check_result = self.check_command(cmd_name, cmd_config)
            results.append(check_result)

            # 更新统计
            self.results["summary"]["total"] += 1
            if check_result["status"] == "passed":
                self.results["summary"]["passed"] += 1
            elif check_result["status"] == "failed":
                self.results["summary"]["failed"] += 1
            elif check_result["status"] == "warning":
                self.results["summary"]["warnings"] += 1

        return results

    def run_checks(self, category: Optional[str] = None, verbose: bool = False) -> Dict:
        """运行所有命令检查"""
        try:
            # 确定要检查的命令组
            groups_to_check = []
            for group in self.main_config["command_groups"]:
                if category is None or group["name"] == category:
                    groups_to_check.append(group)

            # 检查每个命令组
            for group in groups_to_check:
                group_name = group["name"]
                if group_name in self.command_configs:
                    group_results = self.check_command_group(group_name, self.command_configs[group_name])
                    self.results["checks"].extend(group_results)

            return self.results

        except Exception as e:
            self.results["checks"].append({"name": "命令检查", "status": "failed", "details": [f"检查过程出错: {str(e)}"], "suggestions": ["检查命令检查器配置和实现"]})
            return self.results
