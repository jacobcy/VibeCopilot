"""健康检查主类"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .checkers.base_checker import CheckResult


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

    def check_module(self, module: str) -> CheckResult:
        """检查特定模块"""
        checker = self._get_checker(module)
        if not checker:
            return CheckResult(status="failed", details=[f"未知的模块: {module}"], suggestions=["请使用有效的模块名"], metrics={})

        result = checker.check()
        self._update_results(module, result)
        return result

    def check_all(self) -> CheckResult:
        """检查所有模块"""
        for module in self.config.keys():
            self.check_module(module)

        # 计算总体状态
        if self.results["summary"]["failed"] > 0:
            overall_status = "failed"
        elif self.results["summary"]["warnings"] > 0:
            overall_status = "warning"
        else:
            overall_status = "passed"

        return CheckResult(status=overall_status, details=[], suggestions=[], metrics=self.results["summary"])

    def generate_report(self, format: str = "markdown", verbose: bool = False) -> str:
        """生成检查报告"""
        if format == "markdown":
            return self._generate_markdown_report(verbose)
        else:
            return self._generate_json_report(verbose)

    def _get_checker(self, module: str) -> Optional[Any]:
        """获取特定模块的检查器"""
        # TODO: 实现检查器加载逻辑
        return None

    def _update_results(self, module: str, result: CheckResult):
        """更新检查结果"""
        self.results["checks"].append({"module": module, "result": result})

        self.results["summary"]["total"] += 1
        if result.status == "passed":
            self.results["summary"]["passed"] += 1
        elif result.status == "failed":
            self.results["summary"]["failed"] += 1
        elif result.status == "warning":
            self.results["summary"]["warnings"] += 1

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
                report.append(f"\n### {check['module']}")
                report.append(f"状态: {check['result'].status.upper()}")

                if check["result"].details:
                    report.append("\n详细信息:")
                    for detail in check["result"].details:
                        report.append(f"- {detail}")

                if check["result"].suggestions:
                    report.append("\n建议:")
                    for suggestion in check["result"].suggestions:
                        report.append(f"- {suggestion}")

        return "\n".join(report)

    def _generate_json_report(self, verbose: bool) -> str:
        """生成JSON格式报告"""
        import json

        return json.dumps(self.results, indent=2, ensure_ascii=False)
