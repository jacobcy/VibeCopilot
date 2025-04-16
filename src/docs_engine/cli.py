"""
文档引擎命令行工具

提供命令行接口，用于文档解析、转换和管理。
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from src.docs_engine.converters.docs_converter import (
    convert_document_links,
    create_document_from_template,
    extract_document_blocks,
    import_document_to_db,
    parse_document_file,
)
from src.docs_engine.engine import create_document_engine


def main():
    """命令行工具入口函数"""
    # 初始化日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    # 创建命令行解析器
    parser = argparse.ArgumentParser(description="文档引擎命令行工具")

    # 基本参数
    parser.add_argument("--base-dir", "-d", help="项目根目录", default=os.getcwd())
    parser.add_argument("--debug", action="store_true", help="显示调试信息")

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # parse命令 - 解析文档
    parse_parser = subparsers.add_parser("parse", help="解析文档")
    parse_parser.add_argument("file", help="要解析的文档文件路径")
    parse_parser.add_argument("--output", "-o", help="输出文件路径")
    parse_parser.add_argument("--pretty", action="store_true", help="美化输出")

    # extract命令 - 提取文档块
    extract_parser = subparsers.add_parser("extract", help="提取文档块")
    extract_parser.add_argument("file", help="要提取块的文档文件路径")
    extract_parser.add_argument("--output", "-o", help="输出文件路径")
    extract_parser.add_argument("--pretty", action="store_true", help="美化输出")

    # import命令 - 导入文档到数据库
    import_parser = subparsers.add_parser("import", help="导入文档到数据库")
    import_parser.add_argument("file", help="要导入的文档文件路径")

    # convert命令 - 转换文档链接
    convert_parser = subparsers.add_parser("convert", help="转换文档链接")
    convert_parser.add_argument("file", help="要转换的文档文件路径")
    convert_parser.add_argument("--from", dest="from_format", help="源格式", required=True)
    convert_parser.add_argument("--to", dest="to_format", help="目标格式", required=True)
    convert_parser.add_argument("--output", "-o", help="输出文件路径")

    # create命令 - 创建文档
    create_parser = subparsers.add_parser("create", help="创建文档")
    create_parser.add_argument("--template", "-t", help="模板名称", default="default")
    create_parser.add_argument("--output", "-o", help="输出文件路径", required=True)
    create_parser.add_argument("--title", help="文档标题")
    create_parser.add_argument("--description", help="文档描述")

    # 解析参数
    args = parser.parse_args()

    # 如果指定了debug模式，调整日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("已启用调试模式")

    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0

    try:
        # 根据命令执行操作
        logger.info(f"执行命令: {args.command}")

        if args.command == "parse":
            # 解析文档
            doc_data = parse_document_file(args.file)

            if args.output:
                # 写入文件
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(doc_data, f, indent=2 if args.pretty else None, ensure_ascii=False)
                print(f"解析结果已保存到: {args.output}")
            else:
                # 输出到控制台
                print(json.dumps(doc_data, indent=2 if args.pretty else None, ensure_ascii=False))

        elif args.command == "extract":
            # 提取文档块
            blocks = extract_document_blocks(args.file)

            if args.output:
                # 写入文件
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(blocks, f, indent=2 if args.pretty else None, ensure_ascii=False)
                print(f"提取的块已保存到: {args.output}")
            else:
                # 输出到控制台
                print(json.dumps(blocks, indent=2 if args.pretty else None, ensure_ascii=False))

        elif args.command == "import":
            # 导入文档到数据库
            result = import_document_to_db(args.file)

            # 输出结果
            if result["success"]:
                print(f"成功: {result['message']}")
                print(f"文档ID: {result['document_id']}")
                print(f"块数量: {result['block_count']}")
            else:
                print(f"失败: {result.get('message', '未知错误')}")

        elif args.command == "convert":
            # 读取文档内容
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()

            # 转换链接
            converted = convert_document_links(content, args.from_format, args.to_format)

            if args.output:
                # 写入文件
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(converted)
                print(f"转换后的文档已保存到: {args.output}")
            else:
                # 输出到控制台
                print(converted)

        elif args.command == "create":
            # 准备变量
            variables = {}
            if args.title:
                variables["title"] = args.title
            if args.description:
                variables["description"] = args.description

            # 创建文档
            success = create_document_from_template(template=args.template, output_path=args.output, variables=variables)

            if success:
                print(f"文档已成功创建: {args.output}")
            else:
                print(f"文档创建失败")
                return 1

    except ModuleNotFoundError as e:
        print(f"错误: 缺少必要的模块 - {str(e)}")
        print("请确保已安装所有依赖项，可以运行: pip install -e .")
        return 1
    except ImportError as e:
        print(f"错误: 导入模块失败 - {str(e)}")
        print("可能是模块路径错误或模块不存在")
        return 1
    except FileNotFoundError as e:
        print(f"错误: 文件未找到 - {str(e)}")
        return 1
    except PermissionError as e:
        print(f"错误: 权限不足 - {str(e)}")
        return 1
    except Exception as e:
        print(f"错误: {str(e)}")
        logger = logging.getLogger(__name__)
        logger.exception("执行命令时发生未处理的异常")

        # 在调试模式下打印堆栈跟踪
        if "--debug" in sys.argv:
            import traceback

            traceback.print_exc()
        else:
            print("使用 --debug 参数可以查看详细错误信息")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
