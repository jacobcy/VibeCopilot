#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接测试LLM解析，不通过roadmap_parser的预处理直接使用LLMParser
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

from src.core.config import get_config

# 导入必要的模块
from src.parsing.parsers.llm_parser import LLMParser

# 定义一个简单的roadmap提示模板（用于显示和测试）
SIMPLE_ROADMAP_PROMPT = """
请分析以下路线图YAML内容，将其解析为规范的epic-story-task结构。

路线图内容:
{content}

请返回一个JSON对象，包含解析后的路线图结构。确保正确转换所有milestone为epic-story结构。
"""

# 定义一个简单的roadmap系统提示（用于显示和测试）
SIMPLE_ROADMAP_SYSTEM_PROMPT = """
你是一个专业的路线图解析专家。你的任务是将YAML格式的路线图转换为标准的JSON格式。
请确保正确处理所有字段，并将milestone结构转换为epic-story结构。
"""


async def test_direct_llm():
    """
    直接测试LLM解析，不进行任何预检查
    """
    print("\n==== 初始化LLMParser ====\n")

    # 初始化LLMParser
    config = get_config().config
    llm_parser = LLMParser(config)

    # 示例YAML内容 - 一个简单的路线图结构
    yaml_content = """
    title: 前端框架升级计划
    description: 将现有前端框架升级到React 18，并重构关键组件
    version: 1.0
    last_updated: 2023-12-15

    milestones:
      - name: 依赖升级
        description: 升级所有依赖包到最新版本
        due_date: 2024-1-15
        status: in_progress
        tasks:
          - title: 升级React到18.0
            description: 将React库从17.x升级到18.0
            status: completed
            priority: high
            assignee: 张三
          - title: 升级相关依赖
            description: 升级React相关的依赖库
            status: in_progress
            priority: medium
            assignee: 李四

      - name: 组件重构
        description: 重构现有组件以使用新API
        due_date: 2024-2-28
        status: planned
        tasks:
          - title: 重构Context使用
            description: 使用新的Context API重构现有代码
            status: planned
            priority: high
            assignee: 王五
    """

    # 打印roadmap提示模板
    print("==== Roadmap提示模板（简化版） ====\n")
    print(SIMPLE_ROADMAP_PROMPT)

    # 打印系统提示
    print("\n==== 系统提示（简化版） ====")
    print(SIMPLE_ROADMAP_SYSTEM_PROMPT)

    # 设置保存结果的目录
    results_dir = Path("./llm_direct_results")
    results_dir.mkdir(exist_ok=True)

    # 直接调用我们的自定义方法
    print("\n==== 直接调用自定义解析方法 ====")
    try:
        # 使用我们自定义的方法而不是原始的parse_text
        result = await custom_parse_text(llm_parser, yaml_content, "roadmap")

        # 保存完整结果
        timestamp = int(time.time())
        result_path = results_dir / f"result_{timestamp}.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 保存原始响应
        raw_path = results_dir / f"raw_response_{timestamp}.txt"
        if hasattr(llm_parser, "_last_raw_response") and llm_parser._last_raw_response:
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(llm_parser._last_raw_response)

        print(f"\n结果已保存到: {result_path}")
        print(f"原始响应已保存到: {raw_path}")
        print("\n解析成功状态: ", "successful" if result.get("success", False) else "failed")
        if "error" in result:
            print("错误信息: ", result["error"])

    except Exception as e:
        print(f"解析过程中出现错误: {str(e)}")
        import traceback

        traceback.print_exc()


# 自定义解析方法，完全绕过原有模板系统
async def custom_parse_text(llm_parser, content, content_type="roadmap"):
    """自定义解析方法，直接构建消息而不使用模板系统"""
    try:
        # 直接构建系统提示和用户提示
        system_prompt = SIMPLE_ROADMAP_SYSTEM_PROMPT
        user_prompt = SIMPLE_ROADMAP_PROMPT.format(content=content)

        # 准备消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 打印构建的消息
        print(f"\n==== 构建的消息 ====")
        print(f"系统提示: {system_prompt}")
        print(f"用户提示 (部分): {user_prompt[:100]}...")

        # 直接调用LLM服务
        print("\n正在调用LLM服务...")
        response = await llm_parser.llm_service.chat_completion(messages)

        # 提取结果
        if hasattr(response, "choices") and hasattr(response.choices[0], "message"):
            # OpenAI API的原生对象格式
            result_text = response.choices[0].message.content
        else:
            # 字典格式的响应
            result_text = response["choices"][0]["message"]["content"]

        print("\nLLM响应获取成功!")

        # 保存原始响应供查看
        llm_parser._last_raw_response = result_text

        # 尝试解析为JSON
        try:
            # 清理响应文本，去除可能的代码块标记
            cleaned_text = result_text
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()

            # 解析JSON
            json_result = json.loads(cleaned_text)
            print(f"成功解析为JSON对象")

            # 构建结果
            return {"success": True, "content_type": "roadmap", "content": json_result, "raw_response": result_text}

        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {str(e)}")
            # 返回错误信息
            return {
                "success": False,
                "error": f"JSON解析失败: {str(e)}",
                "content_type": "roadmap",
                "content_preview": result_text[:300] + "..." if len(result_text) > 300 else result_text,
                "raw_response": result_text,
            }

    except Exception as e:
        print(f"解析过程中出现异常: {str(e)}")
        llm_parser._last_raw_response = f"ERROR: {str(e)}"
        raise


# 让我们给LLMParser添加一个属性来保存最后的原始响应
# 这是一个临时性的修改，只为了调试目的
def patch_llm_parser():
    """对LLMParser类打补丁，添加保存原始响应的功能"""
    # 应用补丁
    LLMParser._last_raw_response = None


if __name__ == "__main__":
    # 应用补丁
    patch_llm_parser()
    # 运行测试
    asyncio.run(test_direct_llm())
