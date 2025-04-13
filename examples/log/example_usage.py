#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统示例用法

本示例演示了如何使用VibeCopilot的日志系统记录各种类型的日志。
"""

import os
import sys
import time
import traceback
import uuid

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 导入日志模块
from src.logger import (
    get_operation_tasks,
    get_recent_errors,
    get_workflow_logs,
    get_workflow_operations,
    log_audit,
    log_error,
    log_operation_complete,
    log_operation_start,
    log_performance_metric,
    log_task_result,
    log_workflow_complete,
    log_workflow_start,
)


def simulate_data_processing_workflow():
    """
    模拟一个数据处理工作流，演示日志系统的完整用法
    """
    # 生成唯一ID
    workflow_id = f"data-process-{uuid.uuid4().hex[:8]}"
    user_id = "user-12345"

    try:
        # 1. 记录工作流开始
        log_workflow_start(
            workflow_id=workflow_id,
            workflow_name="数据处理工作流",
            trigger_info={"source": "scheduled_job", "user_id": user_id, "data_source": "example_dataset"},
        )

        # 2. 数据获取操作
        fetch_operation_id = f"fetch-{uuid.uuid4().hex[:8]}"
        log_operation_start(
            operation_id=fetch_operation_id, workflow_id=workflow_id, operation_name="数据获取", parameters={"source": "example_dataset", "limit": 1000}
        )

        # 模拟操作执行时间
        start_time = time.time()
        time.sleep(0.5)  # 模拟处理时间

        # 记录性能指标
        duration = time.time() - start_time
        log_performance_metric(
            metric_name="data_fetch_time", value=duration, context={"records_count": 1000}, workflow_id=workflow_id, operation_id=fetch_operation_id
        )

        # 记录操作完成
        log_operation_complete(
            operation_id=fetch_operation_id,
            workflow_id=workflow_id,
            status="completed",
            result={"records_fetched": 1000, "duration_seconds": duration},
        )

        # 3. 数据处理操作
        process_operation_id = f"process-{uuid.uuid4().hex[:8]}"
        log_operation_start(
            operation_id=process_operation_id,
            workflow_id=workflow_id,
            operation_name="数据处理",
            parameters={"filters": ["date > 2023-01-01"], "transformations": ["normalize"]},
        )

        # 模拟任务执行
        for i in range(3):
            task_id = f"process-task-{i}"
            task_start = time.time()

            # 模拟偶尔的任务失败
            if i == 1:
                try:
                    # 故意触发错误
                    result = 10 / 0
                except Exception as e:
                    error_trace = traceback.format_exc()
                    # 记录错误
                    log_error(
                        error_message=str(e),
                        error_type=type(e).__name__,
                        stack_trace=error_trace,
                        workflow_id=workflow_id,
                        operation_id=process_operation_id,
                        context={"task_id": task_id, "step": "calculation"},
                    )

                    # 记录失败的任务结果
                    log_task_result(
                        task_id=task_id,
                        operation_id=process_operation_id,
                        workflow_id=workflow_id,
                        task_name=f"处理批次 {i}",
                        status="failed",
                        result={"error": str(e)},
                    )
                    continue

            # 模拟处理时间
            time.sleep(0.2)
            task_duration = time.time() - task_start

            # 记录任务结果
            log_task_result(
                task_id=task_id,
                operation_id=process_operation_id,
                workflow_id=workflow_id,
                task_name=f"处理批次 {i}",
                status="completed",
                result={"processed_items": 300, "duration": task_duration},
            )

        # 记录操作完成
        process_duration = time.time() - start_time
        log_operation_complete(
            operation_id=process_operation_id,
            workflow_id=workflow_id,
            status="completed",
            result={"total_processed": 900, "failures": 1, "duration_seconds": process_duration},
        )

        # 4. 记录审计信息
        log_audit(
            user_id=user_id,
            action="DATA_PROCESSING",
            resource_type="dataset",
            resource_id="example_dataset",
            details={"processed_records": 900, "workflow_id": workflow_id},
            workflow_id=workflow_id,
        )

        # 5. 工作流完成
        log_workflow_complete(
            workflow_id=workflow_id,
            status="completed",
            result={"total_records_processed": 900, "total_duration_seconds": time.time() - start_time, "success_rate": 0.67},  # 2/3 tasks succeeded
        )

    except Exception as e:
        # 捕获并记录整个工作流中的任何未处理异常
        error_trace = traceback.format_exc()
        log_error(
            error_message=f"工作流执行失败: {str(e)}",
            error_type=type(e).__name__,
            stack_trace=error_trace,
            workflow_id=workflow_id,
            context={"critical": True},
        )

        # 记录工作流失败
        log_workflow_complete(workflow_id=workflow_id, status="failed", result={"error": str(e)})

    return workflow_id


def show_logs(workflow_id):
    """
    展示工作流相关的日志
    """
    print("\n===== 从数据库查询日志 =====")

    # 获取所有工作流日志
    workflow_logs = get_workflow_logs(limit=5)
    print(f"最近的工作流日志 ({len(workflow_logs)}):")
    for log in workflow_logs:
        print(f"  - [{log.get('status', 'unknown')}] {log.get('workflow_name', 'unnamed')} ({log.get('workflow_id', 'unknown')})")

    # 获取特定工作流的操作日志
    operations = get_workflow_operations(workflow_id)
    print(f"\n工作流 '{workflow_id}' 的操作 ({len(operations)}):")
    for op in operations:
        print(f"  - [{op.get('status', 'unknown')}] {op.get('operation_name', 'unnamed')} ({op.get('operation_id', 'unknown')})")

        # 获取特定操作的任务日志
        tasks = get_operation_tasks(op.get("operation_id", ""))
        if tasks:
            print(f"    任务 ({len(tasks)}):")
            for task in tasks:
                print(f"    - [{task.get('status', 'unknown')}] {task.get('task_name', 'unnamed')}")

    # 获取最近的错误日志
    errors = get_recent_errors(limit=5)
    print(f"\n最近的错误日志 ({len(errors)}):")
    for error in errors:
        print(f"  - [{error.get('error_type', 'unknown')}] {error.get('error_message', 'no message')} ({error.get('workflow_id', 'unknown')})")


if __name__ == "__main__":
    print("===== 开始日志系统示例 =====")

    # 执行示例工作流
    workflow_id = simulate_data_processing_workflow()
    print(f"\n工作流执行完成！ID: {workflow_id}")

    # 查询和显示日志
    try:
        show_logs(workflow_id)
    except Exception as e:
        print(f"\n查询日志时出错: {e}")
        print("可能是数据库未正确设置，但文件日志功能仍然正常工作。")

    print("\n===== 示例结束 =====")
    print(f"日志文件已保存至: {os.path.join(project_root, 'logs')}")
