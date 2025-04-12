"""基础检查器类"""
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CheckResult:
    """检查结果数据类"""

    status: str  # passed/failed/warning
    details: List[str]
    suggestions: List[str]
    metrics: Dict[str, Any]


class BaseChecker:
    """检查器基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.result = CheckResult(status="unknown", details=[], suggestions=[], metrics={})

    def check(self) -> CheckResult:
        """执行检查"""
        raise NotImplementedError("子类必须实现check方法")

    def get_suggestions(self) -> List[str]:
        """获取改进建议"""
        return self.result.suggestions
