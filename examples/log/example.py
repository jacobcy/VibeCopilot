"""
VibeCopilot 日志服务使用示例
"""

import time
import uuid

from log_service import (
    log_audit,
    log_error,
    log_operation_complete,
    log_operation_start,
    log_performance_metric,
    log_task_result,
    log_workflow_complete,
    log_workflow_start,
)


def run_example():
    """运行日志服务使用示例"""
    # 生成示例ID
    workflow_id = str(uuid.uuid4())
    print(f"示例工作流ID: {workflow_id}")

    # 记录工作流开始
    log_workflow_start(workflow_id=workflow_id, workflow_name="示例工作流", trigger_info={"source": "example", "user": "demo_user"})

    try:
        # 记录操作开始
        operation_id = str(uuid.uuid4())
        log_operation_start(
            operation_id=operation_id, workflow_id=workflow_id, operation_name="数据处理操作", parameters={"data_source": "test_data", "max_items": 100}
        )

        # 模拟操作执行
        print("执行操作中...")
        start_time = time.time()
        time.sleep(1)  # 模拟处理时间

        # 记录任务结果
        task_id = str(uuid.uuid4())
        log_task_result(
            task_id=task_id,
            operation_id=operation_id,
            workflow_id=workflow_id,
            task_name="数据验证",
            status="completed",
            result={"valid_records": 95, "invalid_records": 5},
        )

        # 记录性能指标
        process_time = time.time() - start_time
        log_performance_metric(
            metric_name="processing_time",
            value=process_time,
            context={"data_size": 100, "operation": "数据处理"},
            workflow_id=workflow_id,
            operation_id=operation_id,
        )

        # 模拟可能的错误
        if process_time < 0:  # 不会触发，仅为演示
            raise ValueError("处理时间不应为负值")

        # 记录操作完成
        log_operation_complete(
            operation_id=operation_id, workflow_id=workflow_id, status="completed", result={"processed_items": 100, "success_rate": 0.95}
        )

        # 记录审计信息
        log_audit(
            user_id="demo_user",
            action="DATA_PROCESS",
            resource_type="workflow",
            resource_id=workflow_id,
            details={"source": "example", "items_processed": 100},
            workflow_id=workflow_id,
        )

        # 记录工作流完成
        log_workflow_complete(workflow_id=workflow_id, status="completed", result={"total_operations": 1, "success": True})

    except Exception as e:
        # 记录错误
        log_error(
            error_message=str(e),
            error_type=type(e).__name__,
            stack_trace=None,  # 在实际应用中，可以使用traceback模块获取堆栈信息
            workflow_id=workflow_id,
            operation_id=operation_id if "operation_id" in locals() else None,
            context={"step": "data_processing"},
        )

        # 记录工作流异常完成
        log_workflow_complete(workflow_id=workflow_id, status="failed", result={"error": str(e)})

        raise

    print(f"示例完成。日志已记录，请查看日志文件。")


if __name__ == "__main__":
    run_example()
