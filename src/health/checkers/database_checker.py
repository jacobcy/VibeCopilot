"""数据库健康检查器"""
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.db.connection_manager import get_engine, get_session
from src.utils.logger import setup_logger

from .base_checker import BaseChecker, CheckResult

logger = setup_logger(__name__)


class DatabaseChecker(BaseChecker):
    """数据库检查器类"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db_config = config.get("database", {})

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
            self.result.metrics = {"tables_checked": 0, "tables_missing": 0, "files_checked": 0, "files_missing": 0}

            # 检查核心表
            core_tables_result = self._check_core_tables(engine)
            self._update_result(core_tables_result)

            # 检查工作流相关表
            workflow_tables_result = self._check_workflow_tables(engine)
            self._update_result(workflow_tables_result)

            # 检查任务和会话相关表
            task_tables_result = self._check_task_tables(engine)
            self._update_result(task_tables_result)

            # 检查必要文件
            files_result = self._check_required_files()
            self._update_result(files_result)

            session.close()

        except Exception as e:
            self.result.status = "failed"
            self.result.details.append(f"数据库检查错误: {str(e)}")
            self.result.suggestions.append("检查数据库配置和连接")
            logger.error(f"数据库检查失败: {str(e)}")

        return self.result

    def _check_core_tables(self, engine) -> Tuple[str, List[str], List[str]]:
        """检查核心数据表"""
        required_tables = {
            "rules": 1,  # 规则表
            "templates": 0,  # 模板表
            "memory_items": 0,  # 记忆项表
        }

        return self._check_tables(engine, required_tables, "核心表")

    def _check_workflow_tables(self, engine) -> Tuple[str, List[str], List[str]]:
        """检查工作流相关表"""
        required_tables = {
            "workflows": 0,  # 工作流表
            "stages": 0,  # 阶段表
            "transitions": 0,  # 转换表
            "workflow_definitions": 0,  # 工作流定义表
            "flow_sessions": 0,  # 工作流会话表
            "stage_instances": 0,  # 阶段实例表
        }

        return self._check_tables(engine, required_tables, "工作流表")

    def _check_task_tables(self, engine) -> Tuple[str, List[str], List[str]]:
        """检查任务和会话相关表"""
        required_tables = {
            "stories": 0,  # 故事表
            "tasks": 0,  # 任务表
            "epics": 0,  # Epic表
            "roadmaps": 0,  # 路线图表
            "milestones": 0,  # 里程碑表
        }

        return self._check_tables(engine, required_tables, "任务表")

    def _check_tables(self, engine, required_tables: Dict[str, int], category: str) -> Tuple[str, List[str], List[str]]:
        """检查数据表是否存在并符合要求"""
        details = []
        suggestions = []
        status = "passed"

        inspector = engine.dialect.inspector(engine)
        existing_tables = inspector.get_table_names()

        for table, min_records in required_tables.items():
            self.result.metrics["tables_checked"] += 1

            if table not in existing_tables:
                status = "failed"
                self.result.metrics["tables_missing"] += 1
                details.append(f"缺失{category}: {table}")
                suggestions.append(f"运行数据库初始化命令创建表 {table}")
                continue

            # 检查记录数
            result = engine.execute(f"SELECT COUNT(*) FROM {table}")
            count = result.scalar()
            details.append(f"表 {table}: {count} 条记录")

            if count < min_records:
                status = "warning"
                suggestions.append(f"表 {table} 记录数({count})小于要求的最小记录数({min_records})")

        return status, details, suggestions

    def _check_required_files(self) -> Tuple[str, List[str], List[str]]:
        """检查必要的数据库相关文件"""
        details = []
        suggestions = []
        status = "passed"

        required_files = [
            "src/db/connection_manager.py",
            "src/db/repository.py",
            "src/db/service.py",
            "src/db/README.md",
            "src/db/models/__init__.py",
            "src/db/repositories/__init__.py",
        ]

        for file_path in required_files:
            self.result.metrics["files_checked"] += 1

            if not os.path.exists(file_path):
                status = "failed"
                self.result.metrics["files_missing"] += 1
                details.append(f"缺失文件: {file_path}")
                suggestions.append(f"创建必要的数据库文件: {file_path}")
            else:
                details.append(f"文件存在: {file_path}")

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
