#!/usr/bin/env python3
"""
规则解析命令行工具
用于将规则文件解析为结构化数据
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("rule_parser")

# 确保模块可导入
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 尝试加载.env文件
env_path = os.path.join(parent_dir, ".env")
if os.path.exists(env_path):
    logger.info(f"从{env_path}加载环境变量")
    load_dotenv(env_path)
else:
    logger.warning(f"未找到.env文件: {env_path}")

from adapters.rule_parser.utils import detect_rule_conflicts, parse_rule_file


def check_environment():
    """检查环境变量"""
    env_vars = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "VIBE_OPENAI_MODEL": os.environ.get("VIBE_OPENAI_MODEL", "默认：gpt-4o-mini"),
        "VIBE_RULE_PARSER": os.environ.get("VIBE_RULE_PARSER", "默认：openai"),
        "VIBE_OLLAMA_MODEL": os.environ.get("VIBE_OLLAMA_MODEL", "默认：llama3"),
        "VIBE_OLLAMA_BASE_URL": os.environ.get("VIBE_OLLAMA_BASE_URL", "默认：http://localhost:11434"),
    }

    # 检查OpenAI API Key
    if not env_vars["OPENAI_API_KEY"] and (not os.environ.get("VIBE_RULE_PARSER") or os.environ.get("VIBE_RULE_PARSER") == "openai"):
        print("警告: 未设置OPENAI_API_KEY环境变量，无法使用OpenAI解析器")
        print("您可以设置VIBE_RULE_PARSER=ollama来使用Ollama解析器，或者设置OPENAI_API_KEY")

    return env_vars


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="规则解析工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 解析命令
    parse_parser = subparsers.add_parser("parse", help="解析规则文件")
    parse_parser.add_argument("file", help="要解析的规则文件路径")
    parse_parser.add_argument(
        "--parser",
        "-p",
        choices=["openai", "ollama"],
        default=os.environ.get("VIBE_RULE_PARSER", "openai"),
        help="解析器类型 (默认: 环境变量VIBE_RULE_PARSER或openai)",
    )
    parse_parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="使用的模型 (默认: 环境变量VIBE_OPENAI_MODEL/VIBE_OLLAMA_MODEL或各引擎默认值)",
    )
    parse_parser.add_argument("--output", "-o", help="输出文件路径 (不指定则输出到标准输出)")
    parse_parser.add_argument("--pretty", "-t", action="store_true", help="美化输出")

    # 冲突检测命令
    conflict_parser = subparsers.add_parser("check-conflict", help="检测规则冲突")
    conflict_parser.add_argument("file1", help="第一个规则文件路径")
    conflict_parser.add_argument("file2", help="第二个规则文件路径")
    conflict_parser.add_argument(
        "--parser",
        "-p",
        choices=["openai", "ollama"],
        default=os.environ.get("VIBE_RULE_PARSER", "openai"),
        help="解析器类型 (默认: 环境变量VIBE_RULE_PARSER或openai)",
    )
    conflict_parser.add_argument("--pretty", "-t", action="store_true", help="美化输出")

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
            from adapters.rule_parser.openai_rule_parser import OpenAIRuleParser

            print("  OpenAI解析器: ✅ 可用")
        except ImportError:
            print("  OpenAI解析器: ❌ 不可用 (缺少依赖)")

        try:
            from adapters.rule_parser.ollama_rule_parser import OllamaRuleParser

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

            print(f"正在使用 {args.parser} 解析器解析规则文件: {args.file}", file=sys.stderr)

            # 解析规则
            result = parse_rule_file(args.file, args.parser, args.model)

            # 输出结果
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2 if args.pretty else None)
                print(f"规则解析结果已保存到: {args.output}")
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))

        except Exception as e:
            print(f"解析失败: {e}", file=sys.stderr)
            logger.error(f"解析失败", exc_info=True)
            sys.exit(1)

    elif args.command == "check-conflict":
        try:
            # 检查文件是否存在
            for file_path in [args.file1, args.file2]:
                if not os.path.exists(file_path):
                    print(f"错误: 文件不存在: {file_path}", file=sys.stderr)
                    sys.exit(1)

            print(f"正在使用 {args.parser} 解析器检测规则冲突:", file=sys.stderr)
            print(f"  规则1: {args.file1}", file=sys.stderr)
            print(f"  规则2: {args.file2}", file=sys.stderr)

            # 解析两个规则
            rule1 = parse_rule_file(args.file1, args.parser)
            rule2 = parse_rule_file(args.file2, args.parser)

            # 分析冲突
            conflict_result = detect_rule_conflicts(rule1, rule2, args.parser)

            # 输出结果
            print(json.dumps(conflict_result, ensure_ascii=False, indent=2 if args.pretty else None))

            # 打印易读的总结
            if conflict_result.get("has_conflict"):
                print(f"\n检测到冲突: {conflict_result.get('conflict_type', '未知类型')}", file=sys.stderr)
                print(f"冲突描述: {conflict_result.get('conflict_description', '无详细描述')}", file=sys.stderr)
            else:
                print("\n未检测到冲突", file=sys.stderr)

        except Exception as e:
            print(f"冲突检测失败: {e}", file=sys.stderr)
            logger.error(f"冲突检测失败", exc_info=True)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
