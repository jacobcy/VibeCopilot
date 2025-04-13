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
            # 统一命令前缀 - 不要替换，保持使用配置的前缀
            # 注释掉原来的替换逻辑
            # if command.startswith("vibecopilot "):
            #     command = command.replace("vibecopilot ", "vc ")

            if self.verbose:
                print(f"执行命令: {command}")

            # 使用shell=True确保命令能在当前环境中正确执行
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=self.config["performance"]["max_response_time"])
            stdout_text = stdout.decode()
            stderr_text = stderr.decode()

            if self.verbose:
                print(f"命令返回码: {process.returncode}")
                if stdout_text:
                    print(f"标准输出: {stdout_text[:100]}...")
                if stderr_text:
                    print(f"错误输出: {stderr_text[:100]}...")

            return process.returncode, stdout_text, stderr_text
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)

    def check_command_help(self, cmd_name: str, cmd_config: Dict) -> Dict:
        """检查命令的帮助信息"""
        check_result = {"name": f"命令帮助检查: {cmd_name}", "status": "passed", "details": [], "suggestions": []}

        # 构建帮助命令 - 使用配置中的命令前缀
        cmd_prefix = self.config["common_config"].get("command_prefix", "vibecopilot")
        help_cmd = f"{cmd_prefix} {cmd_name} --help"

        # 运行帮助命令
        code, stdout, stderr = self.run_command(help_cmd)

        # 获取完整输出（包括stdout和stderr）
        output = stdout + stderr

        if self.verbose:
            print(f"检查命令 '{cmd_name}' 的帮助信息")
            print(f"命令前缀: {cmd_prefix}")
            print(f"完整命令: {help_cmd}")
            print(f"输出长度: {len(output)} 字符")

        # 检查输出是否为空
        if not output.strip():
            check_result["status"] = "failed"
            check_result["details"].append("命令没有任何输出")
            check_result["suggestions"].append("确保命令实现了帮助信息输出")
            return check_result

        # 基础检查 - 只要有输出并且返回码为0就认为基本通过
        if code == 0 and len(output.strip()) > 0:
            # 进行推荐检查

            # 帮助信息关键词检查 - 使用更灵活的匹配
            english_keywords = ["usage", "option", "command", "argument", "example", "help"]
            chinese_keywords = ["用法", "选项", "命令", "参数", "示例", "帮助"]

            # 检查是否包含基础帮助格式
            has_format = False
            for keyword in english_keywords + chinese_keywords:
                if keyword.lower() in output.lower():
                    has_format = True
                    break

            if not has_format:
                check_result["status"] = "warning"
                check_result["details"].append("帮助信息格式可能不标准")
                check_result["suggestions"].append("建议使用标准的帮助信息格式")

            # 检查子命令说明
            if cmd_config.get("subcommands"):
                for subcmd, subcmd_config in cmd_config["subcommands"].items():
                    if subcmd_config.get("required", False) and subcmd.lower() not in output.lower():
                        check_result["status"] = "warning"
                        check_result["details"].append(f"帮助信息缺少必要子命令说明: {subcmd}")
                        check_result["suggestions"].append(f"添加 {subcmd} 的说明")

            return check_result
        else:
            # 命令执行失败
            check_result["status"] = "failed"
            check_result["details"].append(f"命令执行失败，返回码: {code}")
            if stderr:
                check_result["details"].append(f"错误信息: {stderr[:200]}")
            check_result["suggestions"].append("检查命令实现，确保可以正常执行")
            return check_result

    def check_command_output(self, cmd_name: str, subcmd_name: str, subcmd_config: Dict) -> Dict:
        """检查命令的输出内容"""
        check_result = {"name": f"命令输出检查: {cmd_name} {subcmd_name}", "status": "passed", "details": [], "suggestions": []}

        # 获取验证配置
        validation = subcmd_config.get("validation", {})

        # 如果没有验证配置，直接返回通过
        if not validation:
            return check_result

        # 构建命令 - 使用配置中的命令前缀
        cmd_prefix = self.config["common_config"].get("command_prefix", "vibecopilot")

        # 构建基本命令
        test_cmd = f"{cmd_prefix} {cmd_name} {subcmd_name}"

        # 添加必要参数
        if validation.get("required_parameters"):
            for param in validation["required_parameters"]:
                param_config = subcmd_config["parameters"].get(param, {})
                # 如果参数有选项，使用第一个选项作为测试值
                if param_config.get("options"):
                    test_cmd += f" {param}={param_config['options'][0]}"
                # 否则使用一个默认测试值
                else:
                    test_cmd += f" {param}=test"

        # 运行命令
        code, stdout, stderr = self.run_command(test_cmd)
        output = stdout + stderr

        if self.verbose:
            print(f"检查命令 '{cmd_name} {subcmd_name}' 的输出")
            print(f"完整命令: {test_cmd}")
            print(f"返回码: {code}")
            print(f"输出长度: {len(output)} 字符")

        # 检查返回码
        if code != 0:
            check_result["status"] = "failed"
            check_result["details"].append(f"命令执行失败，返回码: {code}")
            if stderr:
                check_result["details"].append(f"错误信息: {stderr[:200]}")
            check_result["suggestions"].append("检查命令实现，确保可以正常执行")
            return check_result

        # 检查输出是否为空
        if not output.strip():
            check_result["status"] = "warning"
            check_result["details"].append("命令输出为空")
            check_result["suggestions"].append("检查命令实现，确保命令有有效输出")
            return check_result

        # 检查必须包含的输出关键词
        if validation.get("required_output"):
            for keyword in validation["required_output"]:
                if keyword.lower() not in output.lower():
                    check_result["status"] = "warning"
                    check_result["details"].append(f"命令输出缺少关键信息: {keyword}")
                    check_result["suggestions"].append(f"确保命令输出包含关键词: {keyword}")

        # 检查输出最小长度
        min_length = validation.get("min_output_length", 0)
        if len(output) < min_length:
            check_result["status"] = "warning"
            check_result["details"].append(f"命令输出过短，长度为{len(output)}，要求最小长度为{min_length}")
            check_result["suggestions"].append(f"确保命令输出内容足够丰富，至少达到{min_length}字符")

        return check_result

    def check_command(self, cmd_name: str, cmd_config: Dict) -> List[Dict]:
        """检查单个命令"""
        results = []

        # 首先检查帮助信息
        help_result = self.check_command_help(cmd_name, cmd_config)
        results.append(help_result)

        # 检查子命令
        for subcmd_name, subcmd_config in cmd_config.get("subcommands", {}).items():
            # 只检查标记为required的子命令
            if subcmd_config.get("required", False):
                # 检查子命令输出
                output_result = self.check_command_output(cmd_name, subcmd_name, subcmd_config)
                results.append(output_result)

                # 更新统计
                self.summary["total"] += 1
                if output_result["status"] == "passed":
                    self.summary["passed"] += 1
                elif output_result["status"] == "failed":
                    self.summary["failed"] += 1
                elif output_result["status"] == "warning":
                    self.summary["warnings"] += 1

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
            command_results = {}  # 存储每个命令组的检查结果

            # 确定要检查的命令组
            groups_to_check = []
            for group in self.config["command_groups"]:
                if self.category is None or group["name"] == self.category:
                    groups_to_check.append(group)

            # 检查每个命令组
            for group in groups_to_check:
                group_name = group["name"]
                if group_name in self.command_configs:
                    group_config = self.command_configs[group_name]
                    group_result = {"status": "passed", "commands": {}, "errors": [], "warnings": []}

                    try:
                        # 检查每个命令
                        for cmd_name, cmd_config in group_config.get("commands", {}).items():
                            cmd_results = self.check_command(cmd_name, cmd_config)
                            cmd_status = "passed"
                            cmd_errors = []
                            cmd_warnings = []

                            for result in cmd_results:
                                if result["status"] == "failed":
                                    cmd_status = "failed"
                                    cmd_errors.extend(result["details"])
                                elif result["status"] == "warning" and cmd_status != "failed":
                                    cmd_status = "warning"
                                    cmd_warnings.extend(result["details"])

                            group_result["commands"][cmd_name] = {"status": cmd_status, "errors": cmd_errors, "warnings": cmd_warnings}

                            # 更新组状态
                            if cmd_status == "failed":
                                group_result["status"] = "failed"
                                group_result["errors"].extend(cmd_errors)
                            elif cmd_status == "warning" and group_result["status"] != "failed":
                                group_result["status"] = "warning"
                                group_result["warnings"].extend(cmd_warnings)

                    except Exception as e:
                        group_result["status"] = "failed"
                        group_result["errors"].append(f"命令组 {group_name} 检查失败: {str(e)}")

                    command_results[group_name] = group_result

            # 根据检查结果确定状态
            if self.summary["failed"] > 0:
                status = "failed"
            elif self.summary["warnings"] > 0:
                status = "warning"
            else:
                status = "passed"

            return CheckResult(
                status=status,
                details=[f"命令组 {group_name}: {result['status'].upper()}" for group_name, result in command_results.items()],
                suggestions=["检查失败的命令组和命令的具体错误信息"] if status != "passed" else [],
                metrics=self.summary,
                command_results=command_results,  # 添加命令检查的详细结果
            )

        except Exception as e:
            return CheckResult(status="failed", details=[f"检查过程出错: {str(e)}"], suggestions=["检查命令检查器配置和实现"], metrics=self.summary, command_results={})
