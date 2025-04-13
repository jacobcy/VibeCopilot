"""
健康检查报告命令模块
"""
from collections import namedtuple

import click

from src.health.checkers.base_checker import CheckResult
from src.health.cli_tools import HealthCheckCLI


@click.command(name="report-help")
@click.option("--format", type=click.Choice(["text", "markdown"]), default="text", help="输出格式")
def report_help(format: str):
    """显示健康检查报告格式说明"""
    if format == "text":
        click.echo(
            """
健康检查报告格式说明:

1. 报告头部
   - 检查时间
   - 整体状态 (PASSED/WARNING/FAILED)

2. 统计摘要
   - 总检查项数量
   - 通过的检查项数量
   - 失败的检查项数量
   - 警告的检查项数量

3. 详细检查结果
   - 系统检查结果
   - 命令检查结果
   - 数据库检查结果

4. 每个检查项包含
   - 状态图标 (✅ 通过, ❌ 失败, ⚠️ 警告)
   - 详细信息
   - 错误信息（如果有）
   - 警告信息（如果有）
   - 建议（如果有）

使用示例:
python -m src.health.cli check --module all --format markdown --output health_report.md
python -m src.health.cli report-example --format text
        """
        )
    else:
        click.echo(
            """
# 健康检查报告格式说明

## 报告结构

### 1. 报告头部
- 检查时间
- 整体状态 (PASSED/WARNING/FAILED)

### 2. 统计摘要
- 总检查项数量
- 通过的检查项数量
- 失败的检查项数量
- 警告的检查项数量

### 3. 详细检查结果
每个模块的检查结果，包括：
- 系统检查
- 命令检查
- 数据库检查

### 4. 检查项格式
- ✅ 表示通过
- ❌ 表示失败
- ⚠️ 表示警告
- 包含详细信息、错误、警告和建议

## 使用示例
```bash
# 运行检查并生成markdown报告
python -m src.health.cli check --module all --format markdown --output health_report.md

# 查看示例报告
python -m src.health.cli report-example --format text
```
        """
        )


@click.command(name="report-example")
@click.option("--format", type=click.Choice(["text", "markdown"]), default="markdown", help="输出格式")
def report_example(format: str):
    """显示健康检查报告示例"""
    cli_tool = HealthCheckCLI()

    # 创建一个简单的CheckResult数据结构，用于示例展示
    MockCheckResult = namedtuple("MockCheckResult", ["status", "details", "suggestions", "metrics", "command_results"])

    # 创建样例数据
    system_result = MockCheckResult(
        status="passed",
        details=["系统环境检查通过", "Python版本: 3.9.6", "操作系统: Linux"],
        suggestions=["建议更新至Python 3.10以获得更好的性能"],
        metrics={"total": 5, "passed": 5, "failed": 0, "warnings": 0},
        command_results=None,
    )

    db_result = MockCheckResult(
        status="warning",
        details=["数据库连接正常", "数据库版本: SQLite 3.36.0", "发现2个未使用的表"],
        suggestions=["清理未使用的表以提高性能", "考虑添加更多索引"],
        metrics={"total": 8, "passed": 6, "failed": 0, "warnings": 2},
        command_results=None,
    )

    # 命令检查结果更复杂，包含命令组和命令详情
    command_results = {
        "任务管理": {
            "status": "passed",
            "commands": {"task create": {"status": "passed"}, "task list": {"status": "passed"}, "task update": {"status": "passed"}},
        },
        "规则管理": {
            "status": "failed",
            "commands": {
                "rule list": {"status": "passed"},
                "rule create": {"status": "failed", "errors": ["缺少必要参数", "错误代码: 1001"]},
                "rule update": {"status": "warning", "warnings": ["性能较慢"]},
            },
        },
    }

    command_result = MockCheckResult(
        status="failed",
        details=["命令检查发现错误", "1个命令组失败", "1个命令组通过"],
        suggestions=["修复rule create命令中的参数检查逻辑"],
        metrics={"total": 6, "passed": 4, "failed": 1, "warnings": 1},
        command_results=command_results,
    )

    # 合并结果
    results = {"系统检查": system_result, "数据库检查": db_result, "命令检查": command_result}

    # 生成并显示报告
    report = cli_tool.generate_report(results, format)
    click.echo(report)
