#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCopilot Memory性能测试

测试Memory模块的性能指标，包括：
1. 搜索延迟（<500ms）
2. 更新延迟（<200ms）
3. 内存使用情况
"""

import logging
import time
import tracemalloc
import uuid
from typing import Any, Dict, List, Tuple

from src.memory import get_memory_service

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 测试参数
TEST_BATCH_SIZE = 100  # 每批测试的笔记数量
TEST_BATCHES = 10  # 测试批次数量，总共会测试 TEST_BATCH_SIZE * TEST_BATCHES 条笔记
TEST_FOLDER = f"perf_test_{uuid.uuid4().hex[:8]}"


def create_test_notes(count: int) -> List[str]:
    """创建测试笔记并返回笔记路径列表"""
    memory_service = get_memory_service()
    note_paths = []

    logger.info(f"开始创建{count}条测试笔记...")
    start_time = time.time()

    # 批量创建笔记
    for i in range(count):
        title = f"perf_note_{i}_{uuid.uuid4().hex[:8]}"
        content = f"""
        # 性能测试笔记 {i}

        这是一个用于性能测试的笔记。

        ## 随机内容

        此笔记包含一些随机内容和唯一标识: {uuid.uuid4().hex}

        ## 标签

        性能测试, 自动生成, 批次{i // 100}
        """

        success, message, data = memory_service.create_note(content=content, title=title, folder=TEST_FOLDER, tags="性能测试,自动生成")

        if success:
            note_paths.append(f"{TEST_FOLDER}/{title}")
        else:
            logger.error(f"创建笔记失败: {message}")

    end_time = time.time()
    create_time = end_time - start_time

    logger.info(f"创建完成，共{len(note_paths)}条笔记")
    logger.info(f"总耗时: {create_time:.2f}秒")
    logger.info(f"平均每条: {(create_time / count) * 1000:.2f}毫秒")

    return note_paths


def test_search_performance(query: str, iterations: int = 10) -> Dict[str, float]:
    """测试搜索性能，返回平均搜索时间"""
    memory_service = get_memory_service()
    total_time = 0
    results_count = 0

    logger.info(f"开始搜索性能测试，查询词: '{query}'")

    # 执行多次搜索以获得平均值
    for i in range(iterations):
        start_time = time.time()
        success, message, results = memory_service.search_notes(query=query)
        end_time = time.time()

        search_time = end_time - start_time
        total_time += search_time

        if success:
            results_count = len(results)
            logger.debug(f"搜索 #{i+1}: 找到 {results_count} 条结果, 耗时: {search_time*1000:.2f}毫秒")
        else:
            logger.error(f"搜索失败: {message}")

    avg_time = (total_time / iterations) * 1000  # 转换为毫秒

    logger.info(f"搜索性能测试完成")
    logger.info(f"平均搜索时间: {avg_time:.2f}毫秒")
    logger.info(f"平均结果数量: {results_count}")

    return {"avg_search_time_ms": avg_time, "results_count": results_count, "is_meeting_requirement": avg_time < 500}  # 要求<500ms


def test_update_performance(note_paths: List[str], sample_size: int = 20) -> Dict[str, float]:
    """测试更新性能，返回平均更新时间"""
    if not note_paths:
        return {"error": "没有可用的测试笔记"}

    import random

    memory_service = get_memory_service()
    total_time = 0
    success_count = 0

    # 从笔记路径中随机选择样本
    sample_paths = random.sample(note_paths, min(sample_size, len(note_paths)))

    logger.info(f"开始更新性能测试，样本大小: {len(sample_paths)}")

    for i, path in enumerate(sample_paths):
        # 生成更新内容
        updated_content = f"""
        # 已更新的笔记 {i}

        这个笔记已经被更新。

        ## 更新时间

        更新时间戳: {time.time()}

        ## 随机内容

        {uuid.uuid4().hex}
        """

        start_time = time.time()
        success, message, data = memory_service.update_note(path=path, content=updated_content)
        end_time = time.time()

        update_time = end_time - start_time
        total_time += update_time

        if success:
            success_count += 1
            logger.debug(f"更新 #{i+1}: 耗时: {update_time*1000:.2f}毫秒")
        else:
            logger.error(f"更新失败 ({path}): {message}")

    if success_count == 0:
        return {"error": "所有更新操作都失败了"}

    avg_time = (total_time / success_count) * 1000  # 转换为毫秒

    logger.info(f"更新性能测试完成")
    logger.info(f"平均更新时间: {avg_time:.2f}毫秒")
    logger.info(f"成功率: {success_count}/{len(sample_paths)}")

    return {"avg_update_time_ms": avg_time, "success_rate": success_count / len(sample_paths), "is_meeting_requirement": avg_time < 200}  # 要求<200ms


def test_memory_usage() -> Dict[str, Any]:
    """测试内存使用情况"""
    memory_service = get_memory_service()

    logger.info("开始内存使用测试")

    # 启动内存跟踪
    tracemalloc.start()

    # 执行一系列操作来测试内存使用
    operations = [
        # 创建一个笔记
        lambda: memory_service.create_note(content="内存测试内容", title=f"mem_test_{uuid.uuid4().hex[:8]}", folder="mem_test", tags="内存测试"),
        # 列出笔记
        lambda: memory_service.list_notes(folder="mem_test"),
        # 搜索笔记
        lambda: memory_service.search_notes(query="内存测试"),
    ]

    # 执行操作
    for op in operations:
        op()

    # 获取内存快照
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 转换为MB
    current_mb = current / (1024 * 1024)
    peak_mb = peak / (1024 * 1024)

    logger.info(f"内存使用测试完成")
    logger.info(f"当前内存使用: {current_mb:.2f} MB")
    logger.info(f"峰值内存使用: {peak_mb:.2f} MB")

    return {"current_memory_mb": current_mb, "peak_memory_mb": peak_mb}


def clean_up(note_paths: List[str]) -> None:
    """清理测试数据"""
    memory_service = get_memory_service()
    logger.info(f"开始清理{len(note_paths)}条测试笔记...")

    for path in note_paths:
        try:
            memory_service.delete_note(path=path, force=True)
        except Exception as e:
            logger.warning(f"删除笔记 {path} 时出错: {e}")

    logger.info("清理完成")


def run_performance_tests() -> Dict[str, Any]:
    """运行所有性能测试并返回结果"""
    results = {"total_notes": TEST_BATCH_SIZE * TEST_BATCHES, "batch_size": TEST_BATCH_SIZE, "batch_count": TEST_BATCHES}

    note_paths = []

    try:
        # 分批创建测试笔记
        for batch in range(TEST_BATCHES):
            logger.info(f"创建批次 {batch+1}/{TEST_BATCHES}")
            batch_paths = create_test_notes(TEST_BATCH_SIZE)
            note_paths.extend(batch_paths)

            # 每批创建后测试搜索性能
            search_results = test_search_performance(f"批次{batch}")
            results[f"search_batch_{batch+1}"] = search_results

        # 测试更新性能
        update_results = test_update_performance(note_paths)
        results["update_performance"] = update_results

        # 测试内存使用
        memory_results = test_memory_usage()
        results["memory_usage"] = memory_results

        # 所有批次创建完成后，进行一次总体搜索测试
        final_search = test_search_performance("性能测试")
        results["final_search_performance"] = final_search

    finally:
        # 测试完成后清理
        clean_up(note_paths)

    # 整体评估
    results["overall_assessment"] = {
        "search_performance_met": results.get("final_search_performance", {}).get("is_meeting_requirement", False),
        "update_performance_met": results.get("update_performance", {}).get("is_meeting_requirement", False),
    }

    return results


if __name__ == "__main__":
    logger.info("=== VibeCopilot Memory性能测试开始 ===")

    try:
        results = run_performance_tests()

        # 输出总结
        print("\n=== 性能测试总结 ===")
        print(f"总测试笔记数: {results['total_notes']}")

        # 搜索性能
        search_performance = results.get("final_search_performance", {})
        search_time = search_performance.get("avg_search_time_ms", "N/A")
        search_requirement_met = search_performance.get("is_meeting_requirement", False)
        search_status = "✅ 通过" if search_requirement_met else "❌ 未通过"
        print(f"搜索性能: {search_time:.2f}ms {search_status}")

        # 更新性能
        update_performance = results.get("update_performance", {})
        update_time = update_performance.get("avg_update_time_ms", "N/A")
        update_requirement_met = update_performance.get("is_meeting_requirement", False)
        update_status = "✅ 通过" if update_requirement_met else "❌ 未通过"
        print(f"更新性能: {update_time:.2f}ms {update_status}")

        # 内存使用
        memory_usage = results.get("memory_usage", {})
        peak_memory = memory_usage.get("peak_memory_mb", "N/A")
        print(f"峰值内存使用: {peak_memory:.2f}MB")

        # 整体评估
        overall = results.get("overall_assessment", {})
        all_requirements_met = all(overall.values())
        overall_status = "✅ 通过" if all_requirements_met else "❌ 未通过"
        print(f"整体评估: {overall_status}")

    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        import traceback

        traceback.print_exc()

    logger.info("=== VibeCopilot Memory性能测试结束 ===")
