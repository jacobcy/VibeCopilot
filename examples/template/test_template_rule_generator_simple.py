#!/usr/bin/env python3
"""
简化版测试模板规则生成器

直接使用模板生成规则文件，不依赖数据库
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# 设置日志级别
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """
    简化版模板规则生成器测试
    """
    parser = argparse.ArgumentParser(description="简化版模板规则生成器测试")
    parser.add_argument("template_file", help="模板文件路径")
    parser.add_argument("output_file", help="输出文件路径")
    parser.add_argument("--vars", help='模板变量JSON字符串, 格式: \'{"name":"value"}\'', required=False)
    parser.add_argument("--vars-file", help="模板变量JSON文件路径", required=False)
    args = parser.parse_args()

    try:
        # 解析变量
        variables = {}

        # 从命令行参数解析变量
        if args.vars:
            try:
                variables.update(json.loads(args.vars))
            except json.JSONDecodeError as e:
                logger.error(f"解析变量JSON字符串失败: {str(e)}")
                sys.exit(1)

        # 从文件解析变量（优先级更高，会覆盖命令行参数）
        if args.vars_file:
            try:
                with open(args.vars_file, "r", encoding="utf-8") as f:
                    file_vars = json.load(f)
                    if isinstance(file_vars, dict):
                        variables.update(file_vars)
                    else:
                        logger.error("变量文件必须包含JSON对象")
                        sys.exit(1)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"读取变量文件失败: {str(e)}")
                sys.exit(1)

        # 读取模板文件
        template_path = Path(args.template_file)
        if not template_path.exists():
            logger.error(f"模板文件不存在: {template_path}")
            sys.exit(1)

        try:
            template_content = template_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"读取模板文件失败: {str(e)}")
            sys.exit(1)

        # 使用Jinja2渲染模板
        try:
            from jinja2 import Template

            template = Template(template_content)
            rendered_content = template.render(**variables)
        except ImportError:
            logger.warning("未安装Jinja2，使用简单替换")
            rendered_content = template_content
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                rendered_content = rendered_content.replace(placeholder, str(value))
        except Exception as e:
            logger.error(f"渲染模板失败: {str(e)}")
            sys.exit(1)

        # 写入输出文件
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            output_path.write_text(rendered_content, encoding="utf-8")
            logger.info(f"规则文件已生成: {output_path}")
        except Exception as e:
            logger.error(f"写入输出文件失败: {str(e)}")
            sys.exit(1)

        # 显示生成内容预览
        preview = rendered_content[:200] + ("..." if len(rendered_content) > 200 else "")
        logger.info(f"生成内容预览: \n{preview}")

    except Exception as e:
        logger.exception(f"生成规则过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
