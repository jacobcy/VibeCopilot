#!/usr/bin/env python
"""
测试路线图解析器

这个脚本用于测试路线图解析功能，尤其是LLM解析器的日志记录和文件保存功能。
用法:
  python scripts/test_roadmap_parser.py <yaml文件路径>
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import yaml

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_roadmap_parser")

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_test_environment():
    """设置测试环境"""
    logger.info("🔧 设置测试环境...")
    # 确保临时目录存在
    os.makedirs("/tmp", exist_ok=True)
    logger.info("✅ 测试环境设置完成")


def read_yaml_file(file_path: str) -> Optional[str]:
    """读取YAML文件内容"""
    logger.info(f"📖 读取文件: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info(f"✅ 文件读取成功，内容长度: {len(content)} 字符")
        return content
    except Exception as e:
        logger.error(f"❌ 文件读取失败: {str(e)}")
        return None


def test_roadmap_processor(file_path: str, force_llm: bool = True):
    """测试路线图处理器"""
    from src.parsing.processors.roadmap_processor import RoadmapProcessor

    logger.info("🔍 创建路线图处理器实例...")
    processor = RoadmapProcessor()
    logger.info("✅ 路线图处理器创建成功")

    # 读取文件内容
    content = read_yaml_file(file_path)
    if not content:
        return

    # 记录所有生成的文件
    generated_files = []

    logger.info(f"🚀 开始处理YAML内容，force_llm={force_llm}...")
    try:
        # 处理内容
        result = processor.process_yaml_content(content, force_llm=force_llm)
        logger.info("✅ 内容处理完成")

        # 保存处理结果
        result_file = "/tmp/test_roadmap_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"📝 已保存处理结果到: {result_file}")
        generated_files.append(result_file)

        # 尝试将结果转换为YAML
        yaml_result_file = "/tmp/test_roadmap_result.yaml"
        with open(yaml_result_file, "w", encoding="utf-8") as f:
            yaml.dump(result, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        logger.info(f"📝 已保存YAML格式结果到: {yaml_result_file}")
        generated_files.append(yaml_result_file)

        # 检查/tmp目录中的其他生成文件
        for filename in os.listdir("/tmp"):
            if filename.startswith(("roadmap_", "llm_")) and os.path.isfile(os.path.join("/tmp", filename)):
                file_path = os.path.join("/tmp", filename)
                generated_files.append(file_path)
                logger.info(f"🔍 发现生成的文件: {file_path}")

        # 打印结果摘要
        if isinstance(result, dict):
            if "metadata" in result:
                logger.info(f"📊 结果元数据: {result.get('metadata')}")
            if "epics" in result:
                epic_count = len(result.get("epics", []))
                logger.info(f"📊 结果包含 {epic_count} 个史诗")

        logger.info(f"📄 生成的文件列表:")
        for i, file_path in enumerate(generated_files, 1):
            logger.info(f"  {i}. {file_path}")

        return result
    except Exception as e:
        logger.error(f"❌ 处理过程出现异常: {str(e)}")
        import traceback

        logger.error(f"详细异常堆栈: {traceback.format_exc()}")
        return None


def test_import_service(file_path: str, verbose: bool = True):
    """测试导入服务"""
    from src.sync.import_service import RoadmapImportService

    logger.info("🔍 创建路线图导入服务实例...")
    service = RoadmapImportService()
    logger.info("✅ 路线图导入服务创建成功")

    logger.info(f"🚀 开始导入YAML文件，verbose={verbose}...")
    try:
        # 导入文件
        result = service.import_from_yaml(file_path, verbose=verbose)
        logger.info("✅ 文件导入完成")

        # 保存导入结果
        result_file = "/tmp/test_import_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"📝 已保存导入结果到: {result_file}")

        # 打印结果摘要
        if isinstance(result, dict):
            logger.info(f"📊 导入结果: success={result.get('success')}")
            if "error" in result:
                logger.error(f"❌ 导入错误: {result.get('error')}")
            if "stats" in result:
                logger.info(f"📊 导入统计: {result.get('stats')}")

        return result
    except Exception as e:
        logger.error(f"❌ 导入过程出现异常: {str(e)}")
        import traceback

        logger.error(f"详细异常堆栈: {traceback.format_exc()}")
        return None


def main():
    """主函数"""
    # 解析命令行参数
    if len(sys.argv) < 2:
        print(f"用法: python {sys.argv[0]} <yaml文件路径> [--processor|--import] [--force-llm]")
        sys.exit(1)

    file_path = sys.argv[1]
    use_processor = "--processor" in sys.argv
    use_import = "--import" in sys.argv
    force_llm = "--force-llm" in sys.argv

    # 如果没有指定，默认使用处理器
    if not use_processor and not use_import:
        use_processor = True

    # 设置测试环境
    setup_test_environment()

    # 执行测试
    if use_processor:
        logger.info("🧪 开始测试路线图处理器...")
        result = test_roadmap_processor(file_path, force_llm=force_llm)
        logger.info("✅ 路线图处理器测试完成")

    if use_import:
        logger.info("🧪 开始测试路线图导入服务...")
        result = test_import_service(file_path, verbose=True)
        logger.info("✅ 路线图导入服务测试完成")

    logger.info("🎉 所有测试完成")


if __name__ == "__main__":
    main()
