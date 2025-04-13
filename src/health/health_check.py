"""健康检查主类"""
import importlib
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .checkers.base_checker import BaseChecker, CheckResult
from .checkers.command_checker import CommandChecker
from .checkers.database_checker import DatabaseChecker
from .checkers.status_checker import StatusChecker
from .checkers.system_checker import SystemChecker

logger = logging.getLogger(__name__)


class HealthCheck:
    """系统健康检查主类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "checks": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0},
        }
        # 检查配置中的已启用模块是否都有实现
        self._validate_enabled_modules()

    def _validate_enabled_modules(self):
        """验证启用的模块是否都有实现"""
        enabled_modules = self.config.get("enabled_modules", [])
        implemented_modules = ["system", "command", "database", "status", "enabled_modules"]

        for module in enabled_modules:
            if module not in implemented_modules:
                logger.warning(f"配置中启用了未实现的检查器模块: {module}，此模块将被跳过")

    def check_module(self, module: str) -> CheckResult:
        """检查指定模块并返回结果

        Args:
            module: 模块名称

        Returns:
            CheckResult: 包含模块健康状态、详情和建议的检查结果
        """
        logger.info(f"开始检查模块: {module}")

        if module not in self.config.get("modules", {}) and module not in self.config.get("enabled_modules", []):
            logger.error(f"未知模块: {module}")
            return CheckResult(status="unknown", details=[f"模块'{module}'未在配置中定义"], suggestions=["检查配置文件中的模块配置"], metrics={})

        try:
            # 插件系统支持
            if hasattr(self, "plugin_manager") and self.plugin_manager and module in self.plugin_manager.plugins:
                plugin = self.plugin_manager.plugins[module]
                result = plugin.check()
                self._update_results(module, result)
                logger.info(f"模块 {module} 检查完成，状态: {result.status}")
                return result
            else:
                # 使用内置检查器
                checker = self._get_checker(module)
                if not checker:
                    error_result = CheckResult(status="failed", details=[f"无法创建模块 {module} 的检查器"], suggestions=["检查模块配置", "确保检查器类已实现"], metrics={})
                    self._update_results(module, error_result)
                    logger.error(f"模块 {module} 检查失败: 无法创建检查器")
                    return error_result

                result = checker.check()
                self._update_results(module, result)
                logger.info(f"模块 {module} 检查完成，状态: {result.status}")
                return result
        except Exception as e:
            error_message = f"检查模块 {module} 失败: {str(e)}"
            logger.error(error_message)
            logger.debug(traceback.format_exc())

            # 捕获异常时返回失败状态
            error_result = CheckResult(status="failed", details=[error_message], suggestions=["检查日志获取详细信息", "验证模块配置是否正确"], metrics={})
            self._update_results(module, error_result)
            return error_result

    def check_all(self) -> CheckResult:
        """检查所有配置的模块

        Returns:
            包含所有模块检查结果的综合结果
        """
        logger.info("开始执行全面健康检查")

        enabled_modules = self.config.get("enabled_modules", [])
        if not enabled_modules:
            logger.warning("配置中未找到已启用的模块")
            enabled_modules = self.config.get("modules", [])
            if not enabled_modules:
                logger.error("配置中既没有enabled_modules也没有modules")
                return CheckResult(
                    status="failed",
                    details=["配置中未找到任何要检查的模块"],
                    suggestions=["检查配置文件，确保至少有一个启用的模块"],
                    metrics={"total": 0, "passed": 0, "failed": 1, "warnings": 0},
                )

        # 检查所有配置的模块
        for module in enabled_modules:
            self.check_module(module)

        # 添加status属性检查
        if not hasattr(self, "status"):
            self.status = self.results["overall_status"]

        # 健康检查完成时，记录总体状态
        logger.info(f"健康检查完成，总体状态: {self.status}")

        # 返回综合结果
        result_summary = {
            "status": self.status,
            "details": [f"{check['module']}: {check['result']['status']}" for check in self.results["checks"]],
            "suggestions": [],
            "metrics": {
                "total": self.results["summary"]["total"],
                "passed": self.results["summary"]["passed"],
                "failed": self.results["summary"]["failed"],
                "warnings": self.results["summary"]["warnings"],
            },
        }

        # 根据状态添加建议
        if self.status == "failed":
            result_summary["suggestions"].append("解决所有失败的模块检查")
        elif self.status == "warning":
            result_summary["suggestions"].append("检查所有警告状态的模块")

        return CheckResult(**result_summary)

    def generate_report(self, format: str = "markdown", verbose: bool = False) -> str:
        """生成检查报告"""
        if format == "markdown":
            return self._generate_markdown_report(verbose)
        elif format == "json":
            return self._generate_json_report(verbose)
        else:
            return self._generate_text_report(verbose)

    def _get_checker(self, module: str) -> Optional[BaseChecker]:
        """获取特定模块的检查器

        Args:
            module: 模块名称

        Returns:
            BaseChecker: 对应的检查器实例，如果不存在则返回None
        """
        if module not in self.config:
            logger.warning(f"未找到模块配置: {module}")
            return None

        try:
            module_config = self.config.get(module, {})

            # 根据模块名称返回对应检查器
            if module == "command":
                # 支持新版命令检查器格式
                command_configs = module_config.get("required_commands", [])
                try:
                    return CommandChecker(module_config, command_configs)
                except Exception as e:
                    logger.error(f"创建命令检查器时出错: {str(e)}")
                    return None
            elif module == "database":
                return DatabaseChecker(module_config)
            elif module == "system":
                return SystemChecker(module_config)
            elif module == "status":
                return StatusChecker(module_config)
            elif module == "enabled_modules":
                from .checkers.enabled_modules_checker import EnabledModulesChecker

                return EnabledModulesChecker(module_config)
            else:
                # 尝试动态加载检查器
                try:
                    checker_path = f".checkers.{module}_checker"
                    logger.debug(f"尝试动态加载检查器: {checker_path}")

                    checker_module = importlib.import_module(checker_path, package="src.health")
                    checker_class_name = f"{module.capitalize()}Checker"

                    if not hasattr(checker_module, checker_class_name):
                        logger.error(f"检查器模块 {checker_path} 中未找到类 {checker_class_name}")
                        return None

                    checker_class = getattr(checker_module, checker_class_name)
                    logger.info(f"成功加载检查器: {checker_class_name}")
                    return checker_class(module_config)
                except ImportError as e:
                    logger.error(f"检查器模块不存在: {module}_checker.py, 错误: {str(e)}")
                    return None
                except AttributeError as e:
                    logger.error(f"检查器类不存在: {module.capitalize()}Checker, 错误: {str(e)}")
                    return None
                except Exception as e:
                    logger.error(f"加载检查器时出现意外错误: {str(e)}")
                    return None
        except Exception as e:
            logger.exception(f"创建检查器时发生错误: {str(e)}")
            return None

    def _update_results(self, module: str, result: CheckResult):
        """更新检查结果"""
        result_dict = (
            result.to_dict()
            if hasattr(result, "to_dict")
            else {
                "status": result.status,
                "details": result.details,
                "suggestions": result.suggestions,
                "metrics": result.metrics,
                "command_results": result.command_results,
            }
        )

        self.results["checks"].append({"module": module, "result": result_dict})

        self.results["summary"]["total"] += 1
        if result.status == "passed":
            self.results["summary"]["passed"] += 1
        elif result.status == "failed":
            self.results["summary"]["failed"] += 1
        elif result.status == "warning":
            self.results["summary"]["warnings"] += 1

        # 每次更新模块结果后，立即更新整体状态
        if self.results["summary"]["failed"] > 0:
            self.results["overall_status"] = "failed"
        elif self.results["summary"]["warnings"] > 0:
            self.results["overall_status"] = "warning"
        else:
            self.results["overall_status"] = "passed"

    def _generate_markdown_report(self, verbose: bool) -> str:
        """生成Markdown格式报告"""
        report = []
        report.append("# VibeCopilot 系统健康检查报告")
        report.append(f"\n## 检查时间: {self.results['timestamp']}")
        report.append(f"## 整体状态: {self.results['overall_status'].upper()}")

        report.append("\n## 统计摘要")
        report.append(f"- 总检查项: {self.results['summary']['total']}")
        report.append(f"- 通过: {self.results['summary']['passed']}")
        report.append(f"- 失败: {self.results['summary']['failed']}")
        report.append(f"- 警告: {self.results['summary']['warnings']}")

        if verbose:
            report.append("\n## 详细检查结果")
            for check in self.results["checks"]:
                module_name = check["module"]
                report.append(f"\n### {module_name}")
                result = check["result"]
                report.append(f"状态: {result['status'].upper()}")

                # 处理命令检查器特有的结果格式
                if module_name == "command" and "command_results" in result:
                    command_results = result["command_results"]
                    report.append("\n命令检查详情:")

                    # 处理命令组或单个命令结果
                    for key, val in command_results.items():
                        if isinstance(val, dict) and "commands" in val:
                            # 命令组格式
                            report.append(f"\n#### 命令组: {key}")
                            status_icon = "✅" if val.get("status") == "passed" else "❌"
                            report.append(f"{status_icon} 状态: {val.get('status', 'unknown').upper()}")

                            # 显示组中的命令
                            if "commands" in val:
                                for cmd_name, cmd_result in val["commands"].items():
                                    cmd_status = cmd_result.get("status", "unknown")
                                    cmd_icon = "✅" if cmd_status == "passed" else "❌"
                                    report.append(f"{cmd_icon} {cmd_name}: {cmd_status.upper()}")

                                    # 显示错误和警告
                                    if "errors" in cmd_result and cmd_result["errors"]:
                                        for error in cmd_result["errors"]:
                                            report.append(f"    - 错误: {error}")
                                    if "warnings" in cmd_result and cmd_result["warnings"]:
                                        for warning in cmd_result["warnings"]:
                                            report.append(f"    - 警告: {warning}")
                        else:
                            # 单个命令格式
                            status = val.get("status", "unknown")
                            status_icon = "✅" if status == "passed" else "❌"
                            report.append(f"{status_icon} {key}: {status.upper()}")

                            # 显示错误和警告
                            if isinstance(val, dict):
                                if "errors" in val and val["errors"]:
                                    for error in val["errors"]:
                                        report.append(f"  - 错误: {error}")
                                if "warnings" in val and val["warnings"]:
                                    for warning in val["warnings"]:
                                        report.append(f"  - 警告: {warning}")

                if result["details"]:
                    report.append("\n详细信息:")
                    for detail in result["details"]:
                        report.append(f"- {detail}")

                if result["suggestions"]:
                    report.append("\n建议:")
                    for suggestion in result["suggestions"]:
                        report.append(f"- {suggestion}")

        return "\n".join(report)

    def _generate_text_report(self, verbose: bool) -> str:
        """生成文本格式报告"""
        report = []
        report.append("VibeCopilot 系统健康检查报告")
        report.append(f"检查时间: {self.results['timestamp']}")
        report.append(f"整体状态: {self.results['overall_status'].upper()}")
        report.append("")

        report.append("统计摘要")
        report.append(f"- 总检查项: {self.results['summary']['total']}")
        report.append(f"- 通过: {self.results['summary']['passed']}")
        report.append(f"- 失败: {self.results['summary']['failed']}")
        report.append(f"- 警告: {self.results['summary']['warnings']}")

        if verbose:
            report.append("")
            report.append("详细检查结果")
            for check in self.results["checks"]:
                report.append("")
                module_name = check["module"]
                report.append(f"{module_name}")
                report.append("-" * len(module_name))
                result = check["result"]
                report.append(f"状态: {result['status'].upper()}")

                # 处理命令检查器特有的结果格式
                if module_name == "command" and "command_results" in result:
                    command_results = result["command_results"]
                    report.append("\n命令检查详情:")

                    # 处理命令组或单个命令结果
                    for key, val in command_results.items():
                        if isinstance(val, dict) and "commands" in val:
                            # 命令组格式
                            report.append(f"\n命令组: {key}")
                            status_icon = "✓" if val.get("status") == "passed" else "✗"
                            report.append(f"{status_icon} 状态: {val.get('status', 'unknown').upper()}")

                            # 显示组中的命令
                            if "commands" in val:
                                for cmd_name, cmd_result in val["commands"].items():
                                    cmd_status = cmd_result.get("status", "unknown")
                                    cmd_icon = "✓" if cmd_status == "passed" else "✗"
                                    report.append(f"{cmd_icon} {cmd_name}: {cmd_status.upper()}")

                                    # 显示错误和警告
                                    if "errors" in cmd_result and cmd_result["errors"]:
                                        for error in cmd_result["errors"]:
                                            report.append(f"    - 错误: {error}")
                                    if "warnings" in cmd_result and cmd_result["warnings"]:
                                        for warning in cmd_result["warnings"]:
                                            report.append(f"    - 警告: {warning}")
                        else:
                            # 单个命令格式
                            status = val.get("status", "unknown")
                            status_icon = "✓" if status == "passed" else "✗"
                            report.append(f"{status_icon} {key}: {status.upper()}")

                            # 显示错误和警告
                            if isinstance(val, dict):
                                if "errors" in val and val["errors"]:
                                    for error in val["errors"]:
                                        report.append(f"  - 错误: {error}")
                                if "warnings" in val and val["warnings"]:
                                    for warning in val["warnings"]:
                                        report.append(f"  - 警告: {warning}")

                if result["details"]:
                    report.append("详细信息:")
                    for detail in result["details"]:
                        report.append(f"- {detail}")

                if result["suggestions"]:
                    report.append("建议:")
                    for suggestion in result["suggestions"]:
                        report.append(f"- {suggestion}")

        return "\n".join(report)

    def _generate_json_report(self, verbose: bool) -> str:
        """生成JSON格式报告"""
        if not verbose:
            simplified_results = self.results.copy()
            for check in simplified_results["checks"]:
                check["result"].pop("details", None)
                check["result"].pop("suggestions", None)
            return json.dumps(simplified_results, indent=2, ensure_ascii=False)
        return json.dumps(self.results, indent=2, ensure_ascii=False)
