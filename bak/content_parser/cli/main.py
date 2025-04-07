#!/usr/bin/env python3
"""
内容解析命令行工具
用于解析规则文件和Markdown文档为结构化数据
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Moved import to the top
from adapters.content_parser.utils import parse_content, parse_file

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("content_parser")

# 确保模块可导入
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 尝试加载.env文件
env_path = os.path.join(parent_dir, ".env")
if os.path.exists(env_path):
    logger.info(f"从{env_path}加载环境变量")
    load_dotenv(env_path)
else:
    logger.warning(f"未找到.env文件: {env_path}")


def check_environment():
    """检查环境变量"""
    env_vars = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "VIBE_OPENAI_MODEL": os.environ.get("VIBE_OPENAI_MODEL", "默认：gpt-4o-mini"),
        "VIBE_CONTENT_PARSER": os.environ.get("VIBE_CONTENT_PARSER", "默认：openai"),
        "VIBE_OLLAMA_MODEL": os.environ.get("VIBE_OLLAMA_MODEL", "默认：mistral"),
    }

    # 检查OpenAI API Key
    if not env_vars["OPENAI_API_KEY"] and (not os.environ.get("VIBE_CONTENT_PARSER") or os.environ.get("VIBE_CONTENT_PARSER") == "openai"):
        print("警告: 未设置OPENAI_API_KEY环境变量，无法使用OpenAI解析器")
        print("您可以设置VIBE_CONTENT_PARSER=ollama来使用Ollama解析器，或者设置OPENAI_API_KEY")

    return env_vars


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="内容解析工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 解析命令
    parse_parser = subparsers.add_parser("parse", help="解析文件")
    parse_parser.add_argument("file", help="要解析的文件路径")
    parse_parser.add_argument(
        "--type",
        "-t",
        choices=["rule", "document", "generic"],
        default="generic",
        help="内容类型 (默认: generic，自动检测)",
    )
    parse_parser.add_argument(
        "--parser",
        "-p",
        choices=["openai", "ollama"],
        default=os.environ.get("VIBE_CONTENT_PARSER", "openai"),
        help="解析器类型 (默认: 环境变量VIBE_CONTENT_PARSER或openai)",
    )
    parse_parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="使用的模型 (默认: 环境变量VIBE_OPENAI_MODEL/VIBE_OLLAMA_MODEL或各引擎默认值)",
    )
    parse_parser.add_argument("--output", "-o", help="输出文件路径 (不指定则输出到标准输出)")
    parse_parser.add_argument("--pretty", action="store_true", help="美化输出")
    parse_parser.add_argument("--save", "-s", action="store_true", help="保存解析结果到数据库")

    # 内容解析命令
    content_parser = subparsers.add_parser("parse-content", help="解析文本内容")
    content_parser.add_argument("text", help="要解析的文本内容或包含内容的文件路径")
    content_parser.add_argument(
        "--type",
        "-t",
        choices=["rule", "document", "generic"],
        default="generic",
        help="内容类型 (默认: generic)",
    )
    content_parser.add_argument(
        "--parser",
        "-p",
        choices=["openai", "ollama"],
        default=os.environ.get("VIBE_CONTENT_PARSER", "openai"),
        help="解析器类型 (默认: 环境变量VIBE_CONTENT_PARSER或openai)",
    )
    content_parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="使用的模型 (默认: 环境变量VIBE_OPENAI_MODEL/VIBE_OLLAMA_MODEL或各引擎默认值)",
    )
    content_parser.add_argument("--context", "-c", default="", help="上下文信息，如文件路径")
    content_parser.add_argument("--output", "-o", help="输出文件路径 (不指定则输出到标准输出)")
    content_parser.add_argument("--pretty", action="store_true", help="美化输出")
    content_parser.add_argument("--save", "-s", action="store_true", help="保存解析结果到数据库")
    content_parser.add_argument("--from-file", "-f", action="store_true", help="从文件读取内容")

    # 环境检查命令
    env_parser = subparsers.add_parser("check-env", help="检查环境配置")

    args = parser.parse_args()

    # 环境检查
    if args.command == "check-env":
        env_vars = check_environment()
        print("\n环境变量状态:")
        for name, value in env_vars.items():
            status = "✅ 已设置" if value and not value.startswith("默认：") else "❌ 未设置"
            if value and value.startswith("默认："):
                value = value
            print(f"  {name}: {status} {value if value else ''}")

        if not env_vars["OPENAI_API_KEY"]:
            print("\n提示: 使用OpenAI解析器需要设置OPENAI_API_KEY环境变量")
            print("设置方法: export OPENAI_API_KEY=您的密钥")

        print("\n可用解析器:")
        try:
            from adapters.content_parser.openai_parser import OpenAIParser

            print("  OpenAI解析器: ✅ 可用")
        except ImportError:
            print("  OpenAI解析器: ❌ 不可用 (缺少依赖)")

        try:
            from adapters.content_parser.ollama_parser import OllamaParser

            print("  Ollama解析器: ✅ 可用")
        except ImportError:
            print("  Ollama解析器: ❌ 不可用 (缺少依赖)")

        return

    # 如果不是环境检查命令，检查其他命令的环境
    check_environment()

    if args.command == "parse":
        try:
            # 检查文件是否存在
            if not os.path.exists(args.file):
                print(f"错误: 文件不存在: {args.file}", file=sys.stderr)
                sys.exit(1)

            print(f"正在使用 {args.parser} 解析器解析文件: {args.file}", file=sys.stderr)
            print(f"内容类型: {args.type}", file=sys.stderr)

            # 解析文件
            result = parse_file(
                file_path=args.file,
                content_type=args.type,
                parser_type=args.parser,
                model=args.model,
            )

            # 输出结果
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2 if args.pretty else None)
                print(f"解析结果已保存到: {args.output}")
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))

            print(f"解析完成", file=sys.stderr)
            if args.save:
                print(f"解析结果已保存到数据库", file=sys.stderr)

        except Exception as e:
            print(f"解析失败: {e}", file=sys.stderr)
            logger.error(f"解析失败", exc_info=True)
            sys.exit(1)

    elif args.command == "parse-content":
        try:
            content = args.text

            # 如果指定从文件读取
            if args.from_file:
                if not os.path.exists(args.text):
                    print(f"错误: 文件不存在: {args.text}", file=sys.stderr)
                    sys.exit(1)

                with open(args.text, "r", encoding="utf-8") as f:
                    content = f.read()

                # 如果没有提供上下文，使用文件路径作为上下文
                if not args.context:
                    args.context = args.text

            print(f"正在使用 {args.parser} 解析器解析内容", file=sys.stderr)
            print(f"内容类型: {args.type}, 上下文: {args.context}", file=sys.stderr)

            # 解析内容
            result = parse_content(
                content=content,
                context=args.context,
                content_type=args.type,
                parser_type=args.parser,
                model=args.model,
            )

            # 输出结果
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2 if args.pretty else None)
                print(f"解析结果已保存到: {args.output}")
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))

            print(f"解析完成", file=sys.stderr)
            if args.save:
                print(f"解析结果已保存到数据库", file=sys.stderr)

        except Exception as e:
            print(f"解析失败: {e}", file=sys.stderr)
            logger.error(f"解析失败", exc_info=True)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
