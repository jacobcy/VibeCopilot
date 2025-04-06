"""
路线图YAML验证器输出模块

负责生成验证结果报告和修复后的YAML文件
"""

import logging
import os
from typing import Any, Dict, List, Tuple

import yaml

logger = logging.getLogger(__name__)


class ValidatorOutput:
    """验证器输出处理"""

    @staticmethod
    def generate_fixed_yaml(data: Dict[str, Any], output_path: str) -> bool:
        """
        生成修复后的YAML文件

        Args:
            data: 修复后的数据
            output_path: 输出文件路径

        Returns:
            bool: 是否成功生成
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            logger.info(f"已生成修复后的YAML文件: {output_path}")
            return True
        except Exception as e:
            logger.error(f"生成修复后的YAML文件失败: {str(e)}")
            return False

    @staticmethod
    def format_check_report(
        yaml_path: str,
        is_valid: bool,
        messages: List[str],
        fixed_data: Dict[str, Any],
        fix: bool = False,
    ) -> str:
        """
        格式化检查报告

        Args:
            yaml_path: YAML文件路径
            is_valid: 是否有效
            messages: 错误/警告消息列表
            fixed_data: 修复后的数据
            fix: 是否生成修复后的文件

        Returns:
            str: 格式化的检查结果报告
        """
        result = []
        result.append(f"📋 路线图YAML格式检查结果: {'✅ 通过' if is_valid else '❌ 失败'}")
        result.append(f"🔍 检查文件: {yaml_path}")
        result.append("")

        # 添加消息
        if messages:
            result.append("📝 检查结果:")
            for msg in messages:
                result.append(f"  {msg}")
        else:
            result.append("📝 检查结果: 未发现问题")

        # 如果验证失败，提供修复建议
        if not is_valid:
            result.append("")
            result.append("🔧 修复建议:")
            result.append("  1. 使用标准模板创建路线图文件")
            result.append("  2. 确保包含所有必填字段")
            result.append("  3. 修复上述错误后重新验证")

            # 如果需要自动修复
            if fix:
                fixed_path = f"{os.path.splitext(yaml_path)[0]}_fixed.yaml"
                if ValidatorOutput.generate_fixed_yaml(fixed_data, fixed_path):
                    result.append("")
                    result.append(f"✅ 已生成修复后的文件: {fixed_path}")

        return "\n".join(result)
