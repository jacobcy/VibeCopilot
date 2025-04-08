"""
模板生成测试脚本
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# 配置日志级别为DEBUG
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 导入模板处理函数
from src.templates.commands.template.handlers import handle_template_generate


def main():
    """测试主函数"""
    # 创建命令行参数
    template_id = "template_956c81b4"  # 示例命令模板ID
    output_file = "test_debug_output.md"  # 输出文件路径

    # 定义变量
    variables = {
        "name": "测试命令",
        "description": "这是一个测试命令示例",
        "command": "test",
        "parameters": [{"name": "option", "description": "选项说明", "required": True}, {"name": "verbose", "description": "详细输出", "required": False}],
        "example": "/test --option=value",
        "notes": "使用时请注意参数格式",
    }

    # 转换为JSON字符串
    variables_json = json.dumps(variables, ensure_ascii=False)
    print(f"输入变量JSON: {variables_json}")

    # 创建参数对象
    args = argparse.Namespace()
    args.template_id = template_id
    args.output = output_file
    args.variables = variables_json  # 使用JSON字符串
    args.format = "markdown"
    args.generator = "regex"

    # 调用处理函数
    try:
        handle_template_generate(args)
        print(f"成功生成文件: {output_file}")

        # 显示生成的文件内容
        content = Path(output_file).read_text(encoding="utf-8")
        print("\n生成的内容:\n" + content)
    except Exception as e:
        print(f"生成失败: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
