#!/usr/bin/env python3
"""
整合Cursor规则系统到VibeCopilot项目

此脚本用于简化Cursor规则系统的安装:
1. 默认模式: 安装基础规则 + 用户项目规则(custom)
2. 开发模式: 安装基础规则 + VibeCopilot开发规则(dev)

使用方法:
    python3 apply_rules.py [--dev] [--force]

选项:
    --dev: 使用开发模式，安装VibeCopilot项目开发规则
    --force: 强制重新安装(会覆盖已有的规则文件)
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
MODULES_DIR = PROJECT_ROOT / "modules" / "cursor-custom-agents-rules-generator"
CURSOR_DIR = PROJECT_ROOT / ".cursor"
CURSOR_RULES_DIR = CURSOR_DIR / "rules"

# 规则目录
DEV_RULES_DIR = Path(__file__).parent / "cursor_rules_dev"
CUSTOM_RULES_DIR = Path(__file__).parent / "cursor_rules_custom"


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="整合Cursor规则系统")
    parser.add_argument("--dev", action="store_true", help="使用开发模式，安装VibeCopilot项目开发规则")
    parser.add_argument("--force", action="store_true", help="强制重新安装(覆盖已有规则)")
    return parser.parse_args()


def check_module_exists():
    """检查cursor-custom-agents-rules-generator模块是否存在"""
    if not MODULES_DIR.exists():
        logger.error(f"错误: 未找到模块 cursor-custom-agents-rules-generator")
        logger.error(
            f"请先克隆仓库: git clone https://github.com/bmadcode/cursor-auto-rules-agile-workflow.git {MODULES_DIR}"
        )
        sys.exit(1)


def run_base_rules_script():
    """运行基础规则安装脚本"""
    script_path = MODULES_DIR / "apply-rules.sh"

    if not script_path.exists():
        logger.error(f"错误: 未找到基础规则安装脚本: {script_path}")
        sys.exit(1)

    logger.info("运行基础规则安装脚本...")

    try:
        # 确保脚本具有执行权限
        os.chmod(script_path, 0o755)

        # 运行shell脚本，直接将输出传递到当前进程
        result = subprocess.run([script_path, str(PROJECT_ROOT)], check=True, text=True)

        if result.returncode == 0:
            logger.info("基础规则安装成功")
            return True
        else:
            logger.error(f"基础规则安装失败，退出码: {result.returncode}")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"基础规则安装失败: {e}")
        return False
    except Exception as e:
        logger.error(f"运行脚本时发生错误: {e}")
        return False


def copy_files(src_dir, dest_dir, force=False):
    """复制文件，如果目标文件已存在且force为False则跳过"""
    if not src_dir.exists():
        logger.warning(f"源目录不存在: {src_dir}")
        return False

    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)

    files_copied = False
    for item in src_dir.iterdir():
        dest_path = dest_dir / item.name

        if item.is_dir():
            # 对于子目录，创建相应的目标子目录
            if not dest_path.exists():
                dest_path.mkdir(parents=True, exist_ok=True)

            # 递归复制子目录内容
            if copy_files(item, dest_path, force):
                files_copied = True
        else:
            if not dest_path.exists() or force:
                shutil.copy2(item, dest_path)
                logger.info(f"复制: {item} -> {dest_path}")
                files_copied = True
            else:
                logger.info(f"跳过已存在文件: {dest_path}")

    return files_copied


def install_dev_rules(force=False):
    """安装VibeCopilot项目开发规则"""
    logger.info("安装VibeCopilot项目开发规则...")

    if not DEV_RULES_DIR.exists():
        logger.warning(f"开发规则目录不存在: {DEV_RULES_DIR}")
        logger.warning("跳过安装开发规则")
        return False

    # 检查是否存在主规则文件
    main_rule_file = DEV_RULES_DIR / "vibe-development-main-always.mdc"
    if not main_rule_file.exists():
        logger.warning(f"未找到开发主规则文件: {main_rule_file}")
        logger.warning("请确保开发规则目录中包含vibe-development-main-always.mdc文件")

    # 复制开发规则到dev-rules目录
    dev_rules_dir = CURSOR_RULES_DIR / "dev-rules"
    if not dev_rules_dir.exists():
        dev_rules_dir.mkdir(parents=True, exist_ok=True)

    if copy_files(DEV_RULES_DIR, dev_rules_dir, force):
        logger.info("开发规则安装成功")
        return True
    else:
        logger.warning("没有开发规则被安装")
        return False


def install_custom_rules(force=False):
    """安装用户项目规则模板"""
    logger.info("安装用户项目规则模板...")

    if not CUSTOM_RULES_DIR.exists():
        logger.warning(f"用户项目规则模板目录不存在: {CUSTOM_RULES_DIR}")
        logger.warning("跳过安装用户项目规则")
        return False

    # 检查是否存在主规则文件
    main_rule_file = CUSTOM_RULES_DIR / "vibe-custom-main-always.mdc"
    if not main_rule_file.exists():
        logger.warning(f"未找到用户项目主规则文件: {main_rule_file}")
        logger.warning("请确保用户项目规则目录中包含vibe-custom-main-always.mdc文件")

    # 复制用户项目规则到my-rules目录
    my_rules_dir = CURSOR_RULES_DIR / "my-rules"
    if not my_rules_dir.exists():
        my_rules_dir.mkdir(parents=True, exist_ok=True)

    if copy_files(CUSTOM_RULES_DIR, my_rules_dir, force):
        logger.info("用户项目规则模板安装成功")
        return True
    else:
        logger.warning("没有用户项目规则模板被安装")
        return False


def main():
    args = parse_args()
    force = args.force
    dev_mode = args.dev

    logger.info(f"开始整合Cursor规则系统... 模式: {'开发模式' if dev_mode else '默认模式'}")

    # 检查模块是否存在
    check_module_exists()

    # 安装基础规则
    if not run_base_rules_script():
        logger.error("基础规则安装失败，退出")
        sys.exit(1)

    # 根据模式安装额外规则
    if dev_mode:
        # 开发模式: 安装开发规则
        dev_installed = install_dev_rules(force)
        logger.info(f"开发规则: {'已安装' if dev_installed else '安装失败'}")
    else:
        # 默认模式: 安装用户项目规则
        custom_installed = install_custom_rules(force)
        logger.info(f"用户项目规则: {'已安装' if custom_installed else '安装失败'}")

    # 总结
    logger.info("=== 安装结果摘要 ===")
    logger.info(f"安装模式: {'开发模式' if dev_mode else '默认模式'}")
    logger.info(f"基础规则: 已安装")
    if dev_mode:
        logger.info(f"开发规则: {'已安装' if dev_installed else '安装失败'}")
    else:
        logger.info(f"用户项目规则: {'已安装' if custom_installed else '安装失败'}")

    logger.info("\n整合完成!")
    logger.info("使用提示:")
    if dev_mode:
        logger.info("已安装开发模式规则，适用于VibeCopilot项目开发")
        if DEV_RULES_DIR.exists() and (DEV_RULES_DIR / "vibe-development-main-always.mdc").exists():
            logger.info("主规则: vibe-development-main-always.mdc (自动应用于所有对话)")
            logger.info("规则安装位置: .cursor/rules/dev-rules/")
    else:
        logger.info("已安装用户项目规则，适用于使用VibeCopilot的普通项目")
        if (
            CUSTOM_RULES_DIR.exists()
            and (CUSTOM_RULES_DIR / "vibe-custom-main-always.mdc").exists()
        ):
            logger.info("主规则: vibe-custom-main-always.mdc (自动应用于所有对话)")
            logger.info("规则安装位置: .cursor/rules/my-rules/")


if __name__ == "__main__":
    main()
