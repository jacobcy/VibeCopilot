#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板生成工具

简单的包装脚本，用于从命令行生成模板文件
"""

import json
import logging
import sys
from pathlib import Path

# 配置日志级别
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    # 检查参数
    if len(sys.argv) < 4:
        print("用法: python generate_template.py <template_id> <output_file> <json_variables>")
        print('示例: python generate_template.py template_956c81b4 output.md \'{"name":"测试"}\'')
        return 1

    # 获取参数
    template_id = sys.argv[1]
    output_file = sys.argv[2]
    variables_json = sys.argv[3]

    try:
        # 解析变量
        variables = json.loads(variables_json)

        # 导入所需模块
        from src.db import get_session_factory
        from src.templates.core.template_manager import TemplateManager
        from src.templates.generators import RegexTemplateGenerator

        # 创建会话
        session_factory = get_session_factory()
        session = session_factory()

        try:
            # 创建模板管理器
            template_manager = TemplateManager(session)

            # 获取模板
            template = template_manager.get_template(template_id)
            if not template:
                print(f"错误: 模板 {template_id} 不存在")
                return 1

            # 创建生成器
            generator = RegexTemplateGenerator()

            # 生成内容
            content = generator.generate(template, variables)

            # 保存到文件
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")

            print(f"已成功生成文件: {output_file}")
            return 0

        finally:
            session.close()

    except json.JSONDecodeError:
        print(f"错误: 变量格式不正确，请提供有效的JSON")
        return 1
    except Exception as e:
        logger.exception("生成模板失败")
        print(f"错误: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
