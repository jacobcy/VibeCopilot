"""基础检查器类"""
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class CheckResult:
    """检查结果数据类"""

    status: str  # passed/failed/warning
    details: List[str]
    suggestions: List[str]
    metrics: Dict[str, Any]
    command_results: Dict[str, Any] = None  # 命令检查的详细结果

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于JSON序列化

        Returns:
            Dict[str, Any]: 可序列化的字典
        """
        return asdict(self)


class BaseChecker:
    """检查器基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.result = CheckResult(status="unknown", details=[], suggestions=[], metrics={})
        self.should_publish = config.get("result_publishing", {}).get("enabled", True)

    def check(self) -> CheckResult:
        """执行检查"""
        raise NotImplementedError("子类必须实现check方法")

    def get_suggestions(self) -> List[str]:
        """获取改进建议"""
        return self.result.suggestions

    def _publish_result(self, checker_name: str, result: CheckResult):
        """发布检查结果到状态系统

        Args:
            checker_name: 检查器名称
            result: 检查结果
        """
        if not self.should_publish:
            return

        try:
            from src.health.result_publisher import publish_health_check_result

            publish_health_check_result(checker_name, result)
        except ImportError:
            # 日志导入会在子类中处理
            pass
        except Exception as e:
            # 日志记录会在子类中处理
            pass
