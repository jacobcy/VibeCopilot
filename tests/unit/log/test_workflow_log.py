#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流日志模块测试脚本
"""

import json
import os
import shutil
from typing import Any, Dict

from src.log import log_service
from src.workflow.execution import get_execution_by_id, get_executions_for_workflow, save_execution


def test_log_service_direct():
    """测试直接使用日志服务"""
    print("===== 测试日志服务 =====")

    # 清理测试数据
    clean_test_data()

    # 1. 记录工作流执行开始
    workflow_id = "test_workflow_123"
    context = {"test_param": "value1", "user": "tester"}

    print(f"开始工作流执行: {workflow_id}")
    execution = log_service.start_workflow_execution(workflow_id, context)

    execution_id = execution["execution_id"]
    print(f"执行ID: {execution_id}")

    # 2. 更新执行状态
    print("更新执行状态...")
    log_service.update_workflow_execution(execution_id=execution_id, status="in_progress", messages=["执行中..."])

    # 3. 添加任务结果
    print("添加任务结果...")
    task_results = {"task1": {"status": "success", "output": "任务1完成"}}
    log_service.update_workflow_execution(execution_id=execution_id, task_results=task_results)

    # 4. 完成执行
    print("完成执行...")
    log_service.complete_workflow_execution(execution_id=execution_id, success=True, messages=["执行成功完成"])

    # 5. 获取执行记录
    print("获取执行记录...")
    execution_data = log_service.get_workflow_execution(execution_id)
    print(f"执行状态: {execution_data['status']}")
    print(f"消息列表: {execution_data['messages']}")

    # 6. 获取工作流的所有执行记录
    print("获取工作流的所有执行记录...")
    executions = log_service.get_workflow_executions(workflow_id)
    print(f"执行记录数: {len(executions)}")

    # 7. 记录工作流操作
    print("记录工作流操作...")
    operation_data = {"action": "update", "changes": {"name": "新名称"}}
    operation = log_service.log_workflow_operation(operation_type="UPDATE", workflow_id=workflow_id, data=operation_data, user="test_user")

    print(f"操作ID: {operation.get('operation_id', 'N/A')}")

    # 8. 获取操作记录
    print("获取操作记录...")
    operations = log_service.get_workflow_operations(workflow_id)
    print(f"操作记录数: {len(operations)}")

    print("测试完成")


def test_workflow_compatibility():
    """测试与workflow模块的兼容性"""
    print("===== 测试与workflow模块的兼容性 =====")

    # 清理测试数据
    clean_test_data()

    # 1. 使用原workflow API保存执行数据
    workflow_id = "compat_workflow_456"
    execution_id = "test_exec_456"

    execution_data = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "status": "pending",
        "start_time": "2023-10-26T10:00:00",
        "messages": ["初始化"],
        "task_results": {},
    }

    print(f"使用原API保存执行数据: {workflow_id}")
    save_execution(execution_data)

    # 2. 更新执行状态
    execution_data["status"] = "completed"
    execution_data["end_time"] = "2023-10-26T10:30:00"
    execution_data["messages"].append("执行完成")

    print("更新执行状态...")
    save_execution(execution_data)

    # 3. 使用原API获取执行记录
    print("使用原API获取执行记录...")
    executions = get_executions_for_workflow(workflow_id)
    print(f"执行记录数: {len(executions)}")

    # 4. 获取单个执行记录
    print("获取单个执行记录...")
    execution = get_execution_by_id(execution_id)
    if execution:
        print(f"执行状态: {execution['status']}")
        print(f"消息列表: {execution['messages']}")
    else:
        print("未找到执行记录")

    # 5. 验证是否可以通过新API访问
    print("通过新API验证数据...")
    log_executions = log_service.get_workflow_executions(workflow_id)
    print(f"通过日志服务获取的执行记录数: {len(log_executions)}")

    print("测试完成")


def clean_test_data():
    """清理测试数据"""
    # 获取日志目录
    log_dir = log_service.config["log_dir"]
    execution_dir = log_service.config["workflow_execution_dir"]
    operation_dir = log_service.config["workflow_operation_dir"]

    # 清理目录
    if os.path.exists(execution_dir):
        for file in os.listdir(execution_dir):
            if file.endswith(".json"):
                os.remove(os.path.join(execution_dir, file))

    if os.path.exists(operation_dir):
        for file in os.listdir(operation_dir):
            if file.endswith(".json"):
                os.remove(os.path.join(operation_dir, file))


if __name__ == "__main__":
    # 运行测试
    test_log_service_direct()
    print("\n")
    test_workflow_compatibility()
