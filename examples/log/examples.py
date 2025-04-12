"""
日志服务使用示例

本文件展示了如何使用日志服务记录各种类型的日志。
"""

import time
import uuid

from log_service import (
    get_time_ms,
    log_audit,
    log_error,
    log_operation_complete,
    log_operation_start,
    log_performance_metric,
    log_task_result,
    log_workflow_complete,
    log_workflow_start,
)


def example_workflow():
    """模拟一个简单的工作流，并记录相关日志"""
    # 生成唯一ID
    workflow_id = str(uuid.uuid4())
    operation_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    # 记录工作流开始
    log_workflow_start(
        workflow_id=workflow_id,
        workflow_name="示例工作流",
        trigger_info={"trigger_type": "manual", "source": "example"},
        user_id="user123",
        additional_data={"priority": "high"},
    )

    try:
        # 记录操作开始
        start_time = get_time_ms()
        log_operation_start(
            operation_id=operation_id,
            workflow_id=workflow_id,
            operation_name="数据处理操作",
            input_data={"data_source": "example_db", "query_params": {"limit": 100}},
        )

        # 模拟任务执行
        time.sleep(1)  # 模拟操作耗时

        # 记录任务结果
        log_task_result(
            task_id=task_id, operation_id=operation_id, task_name="数据过滤任务", status="success", result={"filtered_records": 42, "total_records": 100}
        )

        # 记录操作完成
        elapsed_time = get_time_ms() - start_time
        log_operation_complete(operation_id=operation_id, status="completed", output_data={"processed_records": 100, "success_rate": 0.99})

        # 记录性能指标
        log_performance_metric(
            operation_id=operation_id,
            metric_name="processing_time",
            value=elapsed_time,
            unit="ms",
            tags={"environment": "development", "operation_type": "data_processing"},
        )

        # 记录工作流完成
        log_workflow_complete(
            workflow_id=workflow_id, status="completed", result={"summary": "成功处理了100条记录", "details": {"successful": 99, "failed": 1}}
        )

        # 记录审计日志
        log_audit(
            user_id="user123",
            action="EXECUTE_WORKFLOW",
            resource_type="workflow",
            resource_id=workflow_id,
            status="success",
            details={"workflow_name": "示例工作流", "execution_time": elapsed_time},
        )

    except Exception as e:
        # 记录错误
        log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"workflow_id": workflow_id, "operation_id": operation_id},
            stack_trace="模拟的堆栈跟踪信息",
        )

        # 记录操作失败
        log_operation_complete(operation_id=operation_id, status="failed", error_info={"type": type(e).__name__, "message": str(e)})

        # 记录工作流失败
        log_workflow_complete(workflow_id=workflow_id, status="failed", error_info={"type": type(e).__name__, "message": str(e)})


def example_error_logging():
    """模拟一个错误情况的日志记录"""
    try:
        # 模拟错误
        result = 1 / 0
    except Exception as e:
        log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"function": "example_error_logging", "input_params": {}},
            stack_trace="模拟的堆栈跟踪信息",
        )


if __name__ == "__main__":
    print("运行日志服务示例...")
    example_workflow()
    example_error_logging()
    print("示例完成。请查看日志文件以了解详情。")
