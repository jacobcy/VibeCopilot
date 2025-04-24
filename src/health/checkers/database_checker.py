"""数据库健康检查器"""
import logging  # Added import
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import inspect, text

# Removed import of setup_logger
from src.db.connection_manager import get_engine, get_session

from .base_checker import BaseChecker, CheckResult

logger = logging.getLogger(__name__)


class DatabaseChecker(BaseChecker):
    """数据库检查器类"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db_config = config.get("database", {})
        self.file_config = config.get("files", {})
        self.check_config = config.get("check_config", {})

    def check(self) -> CheckResult:
        """执行数据库健康检查"""
        try:
            # 检查数据库连接
            engine = get_engine()
            session = get_session()

            # 初始化结果
            self.result.status = "passed"
            self.result.details = []
            self.result.suggestions = []
            self.result.metrics = {
                "tables_checked": 0,
                "tables_missing": 0,
                "files_checked": 0,
                "files_missing": 0,
                "p0_issues": 0,
                "p1_issues": 0,
                "p2_issues": 0,
            }

            # 按优先级和分类检查表
            categories = [
                ("core_tables", "核心系统表"),
                ("workflow_tables", "工作流引擎表"),
                ("session_tables", "会话管理表"),
                ("task_tables", "任务管理表"),
                ("roadmap_tables", "路线图管理表"),
            ]

            for category_key, category_name in categories:
                tables = self.db_config.get(category_key, [])
                if tables:
                    category_result = self._check_table_category(engine, tables, category_name)
                    self._update_result(category_result)

            # 检查必要文件
            files_result = self._check_required_files()
            self._update_result(files_result)

            session.close()

            # 根据优先级确定最终状态
            if self.result.metrics["p0_issues"] > 0:
                self.result.status = "failed"
            elif self.result.metrics["p1_issues"] > 0:
                self.result.status = "warning"

        except Exception as e:
            self.result.status = "failed"
            self.result.details.append(f"数据库检查错误: {str(e)}")
            self.result.suggestions.append("检查数据库配置和连接")
            logger.error(f"数据库检查失败: {str(e)}")

        return self.result

    def _check_table_category(self, engine, tables: List[Dict], category_name: str) -> Tuple[str, List[str], List[str]]:
        """检查特定分类的表"""
        details = []
        suggestions = []
        status = "passed"

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        details.append(f"\n{category_name}检查结果:")

        with engine.connect() as connection:
            for table_config in tables:
                table_name = table_config["name"]
                priority = table_config["priority"]
                description = table_config["description"]
                min_records = table_config.get("min_records", 0)

                self.result.metrics["tables_checked"] += 1

                if table_name not in existing_tables:
                    status = "failed" if priority == 0 else "warning"
                    self.result.metrics["tables_missing"] += 1
                    self.result.metrics[f"p{priority}_issues"] += 1
                    details.append(f"- 缺失{description}: {table_name} (P{priority})")
                    suggestions.append(f"运行数据库初始化命令创建表 {table_name} (优先级: P{priority})")
                    continue

                # 检查记录数
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                details.append(f"- 表 {table_name}: {count} 条记录 (P{priority})")

                if count < min_records:
                    if priority == 0:
                        status = "failed"
                        self.result.metrics["p0_issues"] += 1
                    else:
                        status = "warning"
                        self.result.metrics[f"p{priority}_issues"] += 1
                    suggestions.append(f"表 {table_name} 记录数({count})小于要求的最小记录数({min_records}) (优先级: P{priority})")

        return status, details, suggestions

    def _check_required_files(self) -> Tuple[str, List[str], List[str]]:
        """检查必要的数据库相关文件"""
        details = []
        suggestions = []
        status = "passed"

        details.append("\n文件检查结果:")
        required_files = self.file_config.get("required", [])

        for file_config in required_files:
            file_path = file_config["path"]
            priority = file_config.get("priority", 0)
            description = file_config["description"]

            self.result.metrics["files_checked"] += 1

            if not os.path.exists(file_path):
                self.result.metrics["files_missing"] += 1
                self.result.metrics[f"p{priority}_issues"] += 1

                if priority == 0:
                    status = "failed"
                else:
                    status = "warning"

                details.append(f"- 缺失文件: {file_path} (P{priority})")
                suggestions.append(f"创建必要的数据库文件: {file_path} ({description}) (优先级: P{priority})")
            else:
                details.append(f"- 文件存在: {file_path} (P{priority})")

        return status, details, suggestions

    def _update_result(self, check_result: Tuple[str, List[str], List[str]]):
        """更新检查结果"""
        status, details, suggestions = check_result

        # 更新状态（failed > warning > passed）
        if status == "failed" or self.result.status == "failed":
            self.result.status = "failed"
        elif status == "warning" or self.result.status == "warning":
            self.result.status = "warning"

        self.result.details.extend(details)
        self.result.suggestions.extend(suggestions)
