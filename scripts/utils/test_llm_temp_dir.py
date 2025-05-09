"""
测试LLM日志目录创建和文件写入
"""
import json
import logging
import os
import time

# 设置日志格式
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger("test_llm_logging")


def test_llm_dir_creation():
    """测试创建LLM日志目录并写入文件"""
    # 获取项目根目录
    current_file = os.path.abspath(__file__)
    script_dir = os.path.dirname(current_file)
    project_root = os.path.dirname(script_dir)

    # 创建临时目录路径
    temp_dir = os.path.join(project_root, "temp", "llm_logs")

    # 确保目录存在
    os.makedirs(temp_dir, exist_ok=True)

    logger.info(f"创建临时目录: {temp_dir}")

    # 写入测试文件
    timestamp = int(time.time())
    test_file = os.path.join(temp_dir, f"test_llm_file_{timestamp}.json")

    test_data = {"timestamp": timestamp, "test": "测试LLM日志目录", "content": "这是一个测试文件"}

    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    logger.info(f"成功写入测试文件: {test_file}")

    # 列出目录中的所有文件
    files = os.listdir(temp_dir)

    logger.info(f"目录中的文件列表:")
    for file in files:
        file_path = os.path.join(temp_dir, file)
        file_size = os.path.getsize(file_path)
        file_mtime = os.path.getmtime(file_path)

        logger.info(f"  - {file} (大小: {file_size} 字节, 修改时间: {time.ctime(file_mtime)})")

    return temp_dir, test_file


if __name__ == "__main__":
    temp_dir, test_file = test_llm_dir_creation()
    print(f"\n✅ 测试成功!")
    print(f"  临时目录: {temp_dir}")
    print(f"  测试文件: {test_file}")
