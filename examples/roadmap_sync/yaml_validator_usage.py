#!/usr/bin/env python
"""
路线图YAML验证器使用示例

展示如何使用拆分后的验证器模块
"""

import logging
import os
import sys
from pathlib import Path

# 将项目根目录添加到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from src.roadmap.sync.yaml_validator import RoadmapYamlValidator
from src.roadmap.sync.yaml_validator_core import RoadmapValidator
from src.roadmap.sync.yaml_validator_output import ValidatorOutput
from src.roadmap.sync.yaml_validator_template import TemplateManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("yaml_validator_usage")


def basic_usage_example() -> None:
    """展示基本使用方法"""
    print("\n=== 基本使用示例 ===\n")

    # 获取示例文件路径
    test_yaml_file = os.path.join(current_dir, "test_yaml_file.yaml")

    if not os.path.exists(test_yaml_file):
        logger.error(f"测试文件不存在: {test_yaml_file}")
        return

    # 1. 创建验证器
    validator = RoadmapYamlValidator()

    # 2. 验证YAML文件
    is_valid, messages, fixed_data = validator.validate(test_yaml_file)

    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"消息数: {len(messages)}")
    if messages:
        print("前5条消息:")
        for i, msg in enumerate(messages[:5]):
            print(f"  {i+1}. {msg}")

    # 3. 创建修复后的文件
    if not is_valid:
        fixed_file = os.path.join(current_dir, "test_yaml_file_fixed.yaml")
        if validator.generate_fixed_yaml(fixed_data, fixed_file):
            print(f"已生成修复后的文件: {fixed_file}")


def advanced_usage_example() -> None:
    """展示高级使用方法"""
    print("\n=== 高级使用示例 ===\n")

    # 使用子模块直接访问更多功能

    # 1. 创建模板管理器
    template_manager = TemplateManager()

    # 2. 创建路线图验证器
    roadmap_validator = RoadmapValidator(template_manager)

    # 3. 获取测试文件
    test_yaml_file = os.path.join(current_dir, "test_yaml_file.yaml")

    if not os.path.exists(test_yaml_file):
        logger.error(f"测试文件不存在: {test_yaml_file}")
        return

    # 4. 执行验证
    is_valid, messages, fixed_data = roadmap_validator.validate_yaml(test_yaml_file)

    # 5. 生成自定义格式的报告
    print("自定义验证报告:")
    print(f"文件: {test_yaml_file}")
    print(f"状态: {'通过' if is_valid else '失败'}")

    # 对消息进行分类
    errors = [msg for msg in messages if msg.startswith("❌")]
    warnings = [msg for msg in messages if msg.startswith("⚠️")]
    infos = [msg for msg in messages if msg.startswith("ℹ️")]
    fixes = [msg for msg in messages if msg.startswith("🔧")]

    print(f"错误: {len(errors)}, 警告: {len(warnings)}, 信息: {len(infos)}, 修复: {len(fixes)}")

    # 6. 使用输出处理器生成修复文件
    if not is_valid:
        fixed_file = os.path.join(current_dir, "test_yaml_file_fixed_advanced.yaml")
        if ValidatorOutput.generate_fixed_yaml(fixed_data, fixed_file):
            print(f"已生成修复后的文件: {fixed_file}")


def template_example() -> None:
    """展示模板操作示例"""
    print("\n=== 模板操作示例 ===\n")

    # 1. 显示标准模板
    validator = RoadmapYamlValidator()
    template_str = validator.show_template()

    print("标准模板预览 (前10行):")
    template_lines = template_str.split("\n")
    for i, line in enumerate(template_lines[:10]):
        print(f"  {i+1}: {line}")
    print("  ...")

    # 2. 使用自定义模板
    custom_template_path = os.path.join(
        project_root, "templates", "roadmap", "standard_roadmap_template.yaml"
    )
    if os.path.exists(custom_template_path):
        print(f"\n使用自定义模板: {custom_template_path}")
        custom_validator = RoadmapYamlValidator(custom_template_path)

        test_yaml_file = os.path.join(current_dir, "test_yaml_file.yaml")
        if os.path.exists(test_yaml_file):
            is_valid, report = custom_validator.check_and_suggest(test_yaml_file)
            print(f"\n验证结果: {'通过' if is_valid else '失败'}")
    else:
        print(f"\n自定义模板不存在: {custom_template_path}")


def main() -> None:
    """主函数"""
    print("=" * 50)
    print("路线图YAML验证器使用示例")
    print("=" * 50)

    # 展示基本使用方法
    basic_usage_example()

    # 展示高级使用方法
    advanced_usage_example()

    # 展示模板操作
    template_example()

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
