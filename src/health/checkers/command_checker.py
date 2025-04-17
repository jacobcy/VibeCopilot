#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import re
import subprocess
import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

from .base_checker import BaseChecker, CheckResult
from .utils.command_parser import parse_help_options, parse_help_usage

# Import the new processor conditionally later if needed
# from src.parsing.processors.command_help_processor import CommandHelpProcessor
# Import the new command runner function
from .utils.command_runner import run_command_with_timeout
from .utils.help_checker import check_basic_help_format, perform_help_check

# Import the new output checker function
from .utils.output_checker import perform_output_check

logger = logging.getLogger(__name__)


class CommandChecker(BaseChecker):
    def __init__(
        self,
        config: Dict[str, Any],  # This is module_config for 'command'
        # Rename parameter for clarity to indicate it holds the loaded group configs
        loaded_group_configs: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        verbose: bool = False,
    ):
        super().__init__(config)
        self.category = category
        self.verbose = verbose
        self.summary = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}

        # Compatibility handling...
        if not hasattr(self, "config"):
            self.config = config  # module_config
        if "performance" not in self.config:
            self.config["performance"] = {"max_response_time": 30}
        if "common_config" not in self.config:
            self.config["common_config"] = {"command_prefix": "vibecopilot"}

        self.use_llm_comparison = self.config.get("use_llm_comparison", False)
        logger.info(f"CommandChecker initialized. LLM comparison enabled: {self.use_llm_comparison}")
        self.llm_config = self.config.get("llm_config", None)

        # --- CORRECTED LOGIC ---
        # Directly use the loaded group configs passed from HealthCheck._get_checker
        # Ensure it's a dictionary, default to empty dict if None or incorrect type passed
        if isinstance(loaded_group_configs, dict):
            self.command_configs = loaded_group_configs
            logger.debug(f"CommandChecker received command groups: {list(self.command_configs.keys())}")
        else:
            logger.warning("CommandChecker did not receive a valid dictionary of loaded command group configs. Command checks may be skipped.")
            self.command_configs = {}  # Set to empty dict to avoid downstream errors

        # --- REMOVE OLD LOGIC ---
        # if isinstance(command_configs, dict) and "command_groups" in config:
        #     self.command_configs = command_configs
        # elif isinstance(command_configs, list):
        #     self.command_configs = command_configs
        # else:
        #     self.command_configs = config.get("required_commands", [])

    def run_command(self, command: str) -> Tuple[int, str, str]:
        """运行命令并返回结果，委托给 run_command_with_timeout 函数。"""
        timeout = self.config.get("performance", {}).get("max_response_time", 30)
        # Call the external helper function
        return run_command_with_timeout(command=command, timeout=timeout, logger=logger, verbose=self.verbose)  # Pass the logger instance

    def check_command_help(self, cmd_name: str, cmd_config: Dict) -> Dict:
        """检查命令的帮助信息，先进行基础格式检查，然后根据配置选择详细检查方法。"""
        cmd_prefix = self.config["common_config"].get("command_prefix", "vibecopilot")
        help_cmd = f"{cmd_prefix} {cmd_name} --help"

        logger.debug(f"获取帮助信息: {help_cmd}")
        code, stdout, stderr = self.run_command(help_cmd)
        help_text = stdout + stderr

        # --- 1. 基本执行和输出检查 ---
        if code != 0 or not help_text.strip():
            status = "failed"
            details = [f"执行 '{help_cmd}' 失败或无输出。"]
            details.append(f"返回码: {code}")
            if not help_text.strip():
                details.append("命令无输出。")
            if stderr:
                details.append(f"错误输出(前200字符): {stderr[:200]}")
            suggestions = ["检查命令实现和其 --help 输出。"]
            logger.warning(f"命令 '{cmd_name}' --help 执行失败或无输出 (code: {code})。")
            return {"name": f"命令帮助检查: {cmd_name}", "status": status, "details": details, "suggestions": suggestions}

        # --- 2. 基础格式规范检查 ---
        logger.debug(f"执行基础帮助格式检查: {cmd_name}")
        is_format_valid, format_errors = check_basic_help_format(help_text)
        if not is_format_valid:
            status = "failed"  # Basic format failure is a hard fail
            details = [f"命令 '{cmd_name}' 的 --help 输出不符合基本格式规范:"] + format_errors
            suggestions = ["请修复帮助信息格式，确保包含有效的'Usage:'和'Options:'部分。"]
            logger.warning(f"命令 '{cmd_name}' --help 输出格式检查失败: {format_errors}")
            return {"name": f"命令帮助检查: {cmd_name}", "status": status, "details": details, "suggestions": suggestions}
        else:
            logger.debug(f"基础帮助格式检查通过: {cmd_name}")

        # --- 3. 详细对比检查 (LLM 或 传统) ---
        if self.use_llm_comparison:
            # --- 3a. LLM 对比 ---
            logger.info(f"使用 LLM 对比帮助信息: {cmd_name}")
            try:
                # Conditional import to avoid dependency if not used
                from src.parsing.processors.command_help_processor import CommandHelpProcessor

                processor = CommandHelpProcessor(self.llm_config)
                comparison_result = processor.compare(help_text, cmd_config)

                # Convert LLM comparison result to CheckResult format
                check_result = {"name": f"命令帮助检查 (LLM): {cmd_name}", "status": "passed", "details": [], "suggestions": []}

                if comparison_result.get("success"):
                    diffs = comparison_result.get("differences", {})
                    details_list = []
                    suggestions_list = []
                    has_diff = False

                    # --- SKIP ARGUMENT CHECKS FOR LLM ---
                    # if diffs.get("missing_in_help_args"):
                    #     details_list.append(f"参数不匹配(LLM): YAML中的 {diffs['missing_in_help_args']} 未在帮助Usage中找到。")
                    #     suggestions_list.append("检查命令实现或更新YAML中的 arguments.")
                    #     has_diff = True
                    # if diffs.get("missing_in_yaml_args"):
                    #     details_list.append(f"参数不匹配(LLM): 帮助Usage中的 {diffs['missing_in_yaml_args']} 未在YAML中定义。")
                    #     suggestions_list.append("在YAML的 arguments 中添加缺失的参数定义.")
                    #     has_diff = True

                    # --- Keep Option Checks ---
                    if diffs.get("missing_in_help_opts"):
                        details_list.append(f"选项不匹配(LLM): YAML中的 {diffs['missing_in_help_opts']} 未在帮助Options中找到。")
                        suggestions_list.append("检查命令实现或更新YAML中的 options.")
                        has_diff = True
                    if diffs.get("missing_in_yaml_opts"):
                        details_list.append(f"选项不匹配(LLM): 帮助Options中的 {diffs['missing_in_yaml_opts']} 未在YAML中定义。")
                        suggestions_list.append("在YAML的 options 中添加缺失的选项定义.")
                        has_diff = True

                    # --- Format Short Name Mismatches ---
                    if diffs.get("short_name_mismatches"):
                        mismatches = diffs["short_name_mismatches"]
                        # Format the mismatch report for better readability
                        formatted_mismatches = []
                        if isinstance(mismatches, list):
                            for mismatch in mismatches:
                                if isinstance(mismatch, dict):
                                    opt = mismatch.get("option")
                                    yaml_s = mismatch.get("yaml_short")
                                    help_s = mismatch.get("help_short")
                                    formatted_mismatches.append(f"{opt} (YAML short: {yaml_s or 'None'}, Help short: {help_s or 'None'})")
                                else:
                                    formatted_mismatches.append(str(mismatch))  # Fallback
                        else:
                            formatted_mismatches.append(str(mismatches))  # Fallback

                        details_list.append(f"选项简写不匹配(LLM): {'; '.join(formatted_mismatches)}")
                        suggestions_list.append("统一YAML和命令实现中的选项简写.")
                        has_diff = True

                    if has_diff:
                        check_result["status"] = "warning"
                        check_result["details"] = details_list
                        check_result["suggestions"] = suggestions_list
                    else:
                        check_result["details"].append("LLM分析未发现配置与帮助信息之间存在差异。")

                    # Log raw LLM response if verbose
                    if self.verbose and comparison_result.get("raw_llm_response"):
                        logger.debug(f"LLM Raw Response for {cmd_name}:\n{comparison_result['raw_llm_response']}")

                else:
                    # LLM comparison itself failed
                    check_result["status"] = "failed"
                    check_result["details"].append(f"LLM 对比失败: {comparison_result.get('error')}")
                    check_result["suggestions"].append("检查 LLM 配置和日志以获取详细信息。")
                    # Log raw response if available
                    if self.verbose and comparison_result.get("raw_llm_response"):
                        logger.debug(f"LLM Raw Response (Failure) for {cmd_name}:\n{comparison_result['raw_llm_response']}")

                return check_result

            except ImportError:
                logger.error("无法导入 CommandHelpProcessor。请确保 src.parsing.processors 存在且路径正确。将回退到传统方法。")
                # Fallback to traditional method if import fails
                pass  # Let the code proceed to the traditional method below
            except Exception as e:
                logger.error(f"执行 LLM 对比时出错: {e}", exc_info=True)
                return {
                    "name": f"命令帮助检查 (LLM): {cmd_name}",
                    "status": "failed",
                    "details": [f"执行 LLM 对比时发生内部错误: {e}"],
                    "suggestions": ["检查日志以获取详细的回溯信息。"],
                }

        # --- Traditional Method (if LLM is not used or import failed) ---
        logger.info(f"使用传统方法检查帮助信息: {cmd_name}")
        # Call the external helper function for traditional checks
        return perform_help_check(
            run_command_func=self.run_command,
            parse_usage_func=parse_help_usage,
            parse_options_func=parse_help_options,
            cmd_name=cmd_name,
            cmd_config=cmd_config,
            cmd_prefix=cmd_prefix,
            logger=logger,
            verbose=self.verbose,
        )

    def check_command_output(self, cmd_name: str, subcmd_name: str, subcmd_config: Dict) -> Dict:
        """检查命令的输出内容，委托给 perform_output_check 函数。"""
        # Get command prefix from common config
        cmd_prefix = self.config.get("common_config", {}).get("command_prefix", "vibecopilot")

        # Call the external helper function
        return perform_output_check(
            run_command_func=self.run_command,
            cmd_name=cmd_name,
            subcmd_name=subcmd_name,
            subcmd_config=subcmd_config,
            cmd_prefix=cmd_prefix,
            logger=logger,  # Pass the logger instance
            verbose=self.verbose,
        )

    def check_command(self, cmd_name: str, cmd_config: Dict) -> List[Dict]:
        """检查单个命令"""
        results = []

        # 首先检查帮助信息
        help_result = self.check_command_help(cmd_name, cmd_config)
        results.append(help_result)

        # 只基于帮助信息的检查结果更新统计
        self.summary["total"] += 1  # 每个命令算一次检查
        if help_result["status"] == "passed":
            self.summary["passed"] += 1
        elif help_result["status"] == "failed":
            # 如果帮助检查失败，则命令检查整体失败
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
        logger.info(f"开始 CommandChecker.check，类别: {self.category}")  # Log entry
        try:
            command_results = {}  # 存储每个命令组的检查结果

            # 兼容处理：根据数据结构选择不同的检查路径
            if isinstance(self.command_configs, dict):
                logger.debug("命令配置为字典 (旧版/期望的格式)")
                # 旧版调用方式 - 使用字典格式的command_configs
                # 获取所有可用的命令组名称
                available_groups = [group["name"] for group in self.config.get("command_groups", [])]
                logger.debug(f"可用命令组: {available_groups}")

                # 检查指定的category是否有效
                if self.category is not None and self.category not in available_groups:
                    logger.error(f"指定的命令组类别 '{self.category}' 无效。可用: {available_groups}")
                    return CheckResult(
                        status="failed",
                        details=[f"错误: 无效的命令组类别 '{self.category}'"],
                        suggestions=[f"有效的命令组类别有: {', '.join(available_groups)}"],
                        metrics={"total": 0, "passed": 0, "failed": 0, "warnings": 0},
                        command_results={},
                    )

                # 确定要检查的命令组
                groups_to_check = []
                for group in self.config.get("command_groups", []):
                    if self.category is None or group["name"] == self.category:
                        groups_to_check.append(group)
                logger.info(f"将要检查的命令组: {[g['name'] for g in groups_to_check]}")

                # 检查每个命令组
                if not groups_to_check and self.category:
                    logger.warning(f"类别 '{self.category}' 没有找到匹配的命令组进行检查。")

                for group in groups_to_check:
                    group_name = group["name"]
                    logger.info(f"开始处理命令组: {group_name}")

                    if group_name in self.command_configs:
                        logger.debug(f"命令组 '{group_name}' 的配置已加载。")
                        group_config = self.command_configs[group_name]
                        group_result = {"status": "passed", "commands": {}, "errors": [], "warnings": []}

                        try:
                            # 检查每个命令
                            commands_in_group = list(group_config.get("commands", {}).keys())
                            logger.debug(f"命令组 '{group_name}' 中的命令: {commands_in_group}")
                            if not commands_in_group:
                                logger.warning(f"命令组 '{group_name}' 的配置中未找到 'commands' 或为空。")

                            for cmd_name, cmd_config in group_config.get("commands", {}).items():
                                logger.info(f"开始检查命令: {cmd_name}")
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
                            # Add detailed error logging
                            error_msg = f"命令组 {group_name} 检查失败: {str(e)}"
                            logger.error(error_msg)
                            # Also log traceback if verbose mode is enabled or for critical errors
                            logger.debug(traceback.format_exc())
                            group_result["errors"].append(error_msg)

                        command_results[group_name] = group_result
                    else:
                        logger.error(f"命令组 '{group_name}' 在主配置中定义，但未能从文件加载其配置。跳过检查。")
                        # Optionally create a failed result for this group
                        command_results[group_name] = {"status": "failed", "errors": [f"未能加载组 '{group_name}' 的配置"], "warnings": [], "commands": {}}
                        self.summary["failed"] += 1  # Count this loading failure
                        self.summary["total"] += 1

            else:
                # 新版调用方式 - 使用列表格式的command_configs
                logger.warning("命令配置为列表 (新版/非期望的格式?)，将执行简化检查。")
                # 直接检查命令列表
                if self.category:
                    filtered_commands = [cmd for cmd in self.command_configs if cmd.get("category") == self.category]
                else:
                    filtered_commands = self.command_configs

                status = "passed"
                for cmd_config in filtered_commands:
                    cmd_name = cmd_config.get("name")
                    if not cmd_name:
                        continue

                    # 简化的命令检查，仅验证命令是否可执行
                    cmd_type = cmd_config.get("type", "command")  # 命令类型：rule或command
                    expected_output = cmd_config.get("expected_output", [])

                    result = self._check_simple_command(cmd_name, cmd_type, expected_output)
                    command_results[cmd_name] = result

                    if result.get("status") == "failed":
                        status = "failed"

                self.summary["total"] = len(filtered_commands)

            # 根据检查结果确定状态
            if self.summary["failed"] > 0:
                status = "failed"
            elif self.summary["warnings"] > 0:
                status = "warning"
            else:
                status = "passed"

            # 构建适用于展示的格式化结果
            details = []
            suggestions = []

            # 更新汇总信息
            if status != "passed":
                failed_commands = []
                for group_name, group_result in command_results.items():
                    if isinstance(group_result, dict) and group_result.get("status") != "passed":
                        failed_commands.append(group_name)

                if failed_commands:
                    details.append(f"以下命令组检查失败: {', '.join(failed_commands)}")
                    suggestions.append("检查命令组配置和实现")

            # --- ADD CONSOLIDATED SUGGESTION for traditional check limitations ---
            found_traditional_mismatch_warning = False
            traditional_warning_pattern = "选项不匹配(传统方法): YAML中的"
            for group_name, group_result in command_results.items():
                if isinstance(group_result, dict) and "commands" in group_result:
                    for cmd_name, cmd_result_data in group_result.get("commands", {}).items():
                        if isinstance(cmd_result_data, dict):
                            # Check within the command's direct results (e.g., from help_result)
                            for detail in cmd_result_data.get("details", []) + cmd_result_data.get("warnings", []):
                                if isinstance(detail, str) and traditional_warning_pattern in detail:
                                    found_traditional_mismatch_warning = True
                                    break  # Found one, no need to check further details for this command
                            # Check within the nested results list if structure is different
                            nested_results = cmd_result_data.get("results", [])  # Assuming results might be nested
                            if not found_traditional_mismatch_warning and isinstance(nested_results, list):
                                for nested_res in nested_results:
                                    if isinstance(nested_res, dict):
                                        for detail in nested_res.get("details", []):
                                            if isinstance(detail, str) and traditional_warning_pattern in detail:
                                                found_traditional_mismatch_warning = True
                                                break
                                if found_traditional_mismatch_warning:
                                    break
                        if found_traditional_mismatch_warning:
                            break  # Found one in this command group
                if found_traditional_mismatch_warning:
                    break  # Found one, exit outer loop

            if found_traditional_mismatch_warning:
                consolidated_suggestion = "建议: 传统帮助检查方法可能因格式复杂而不准确，可使用 '--use-llm' 标志进行更精确的复查。"
                if consolidated_suggestion not in suggestions:
                    suggestions.append(consolidated_suggestion)
            # --- END ADD CONSOLIDATED SUGGESTION ---

            # 设置检查结果
            metrics = {
                "total": self.summary["total"],
                "passed": self.summary["passed"],
                "failed": self.summary["failed"],
                "warnings": self.summary["warnings"],
            }
            result = CheckResult(
                status=status,
                details=details if details else [f"命令组检查: {status.upper()}"],
                suggestions=suggestions if suggestions else [],
                metrics=metrics,
                command_results=command_results,  # 添加命令检查的详细结果
            )

            # 发布结果
            if hasattr(self, "_publish_result"):
                self._publish_result("command", result)

            return result

        except Exception as e:
            # Log exception from the top-level try block
            logger.error(f"CommandChecker.check 方法顶层捕获到异常: {str(e)}")
            logger.debug(traceback.format_exc())
            # 根据检查结果确定状态
            if self.summary["failed"] > 0:
                status = "failed"
            elif self.summary["warnings"] > 0:
                status = "warning"
            else:
                status = "passed"

            # 构建适用于展示的格式化结果
            details = [f"检查过程出错: {str(e)}"]
            suggestions = ["检查命令检查器配置和实现"]

            # 设置检查结果
            metrics = {
                "total": self.summary["total"],
                "passed": self.summary["passed"],
                "failed": self.summary["failed"],
                "warnings": self.summary["warnings"],
            }
            command_results = getattr(self, "command_results", {})  # Use existing if available
            result = CheckResult(
                status="failed",
                details=details,
                suggestions=suggestions,
                metrics=metrics,
                command_results=command_results,
            )

            # 发布结果
            if hasattr(self, "_publish_result"):
                self._publish_result("command", result)

            return result

    def _check_simple_command(self, cmd_name: str, cmd_type: str, expected_output: List[str]) -> Dict:
        """简化的命令检查，适用于没有完整配置的情况"""
        result = {"name": cmd_name, "status": "passed", "details": [], "errors": [], "warnings": []}

        try:
            # 构建命令
            cmd = cmd_name
            if cmd_type == "rule":
                # 规则命令不需要前缀
                pass
            else:
                # 命令类型，添加前缀
                cmd_prefix = self.config.get("common_config", {}).get("command_prefix", "vibecopilot")
                cmd = f"{cmd_prefix} {cmd}"

            # 运行命令
            code, stdout, stderr = self.run_command(cmd)
            output = stdout + stderr

            # 检查返回码
            if code != 0:
                result["status"] = "failed"
                result["errors"].append(f"命令执行失败，返回码: {code}")
                if stderr:
                    result["errors"].append(f"错误信息: {stderr[:200]}")
                return result

            # 检查期望输出
            if expected_output:
                for expected in expected_output:
                    if expected.lower() not in output.lower():
                        result["status"] = "failed"
                        result["errors"].append(f"输出缺少期望内容: {expected}")

            # 更新统计
            self.summary["total"] += 1
            if result["status"] == "passed":
                self.summary["passed"] += 1
            else:
                self.summary["failed"] += 1

            return result
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"命令检查异常: {str(e)}")
            self.summary["total"] += 1
            self.summary["failed"] += 1
            return result
