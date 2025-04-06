"""
Obsidian到Docusaurus转换主模块

提供命令行接口和主要转换入口
"""

import argparse
import sys

from .file_converter import FileConverter


class ObsidianDocusaurusConverter(FileConverter):
    """Obsidian到Docusaurus的转换器

    完整的转换功能，包含文件映射、链接转换和文件转换
    """

    pass


def main():
    """
    主函数，解析命令行参数并执行转换
    """
    parser = argparse.ArgumentParser(description="将Obsidian笔记转换为Docusaurus兼容的Markdown文件")
    parser.add_argument("obsidian_dir", help="Obsidian文档目录")
    parser.add_argument("docusaurus_dir", help="Docusaurus文档目录")
    parser.add_argument("--assets-dir", help="资源文件目录（默认为obsidian_dir/assets）")

    args = parser.parse_args()

    try:
        # 初始化转换器
        converter = ObsidianDocusaurusConverter(
            args.obsidian_dir, args.docusaurus_dir, args.assets_dir
        )

        # 转换所有文件
        success_count, failure_count = converter.convert_all_files()

        # 输出结果
        print(f"\n转换完成！成功: {success_count}, 失败: {failure_count}")

        # 返回状态码
        if failure_count > 0:
            return 1
        return 0
    except Exception as e:
        print(f"转换过程发生错误: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
