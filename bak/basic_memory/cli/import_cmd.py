#!/usr/bin/env python3
"""
文档导入命令行工具
提供批量导入文档到Basic Memory数据库的命令行接口
使用content_parser进行文档解析
"""

import argparse
import os
import sys
from pathlib import Path

from adapters.basic_memory.db.memory_store import MemoryStore
from adapters.basic_memory.parsers import LangChainKnowledgeProcessor
from adapters.basic_memory.utils.formatters import convert_to_entity_format
from adapters.content_parser.utils.parser import parse_file


class DocumentImporter:
    """文档导入器"""

    def __init__(self, source_dir: str, db_path: str, parser_type: str = "ollama", model: str = "mistral"):
        """初始化导入器

        Args:
            source_dir: 源文档目录
            db_path: 数据库路径
            parser_type: 解析器类型 ("openai" 或 "ollama")
            model: 使用的模型名称
        """
        self.source_dir = Path(source_dir)
        self.parser_type = parser_type
        self.model = model
        self.memory_store = MemoryStore(db_path)
        self.memory_store.setup_database()

    def process_documents(self) -> None:
        """处理所有文档"""
        print(f"开始处理目录: {self.source_dir}")
        processed = 0

        # 处理所有Markdown文件
        for md_file in self.source_dir.rglob("*.md"):
            print(f"解析文件: {md_file}")

            try:
                # 使用content_parser解析文件
                parse_result = parse_file(
                    str(md_file),
                    content_type="document",
                    parser_type=self.parser_type,
                    model=self.model,
                )

                # 转换为实体关系格式
                entity_result = convert_to_entity_format(parse_result)

                # 设置源路径相对于源目录
                rel_path = md_file.relative_to(self.source_dir)
                entity_result["source_path"] = str(rel_path)

                # 存储解析结果
                self.memory_store.store_document(entity_result, md_file)

                processed += 1
                print(f"✓ 已处理: {md_file}")

            except Exception as e:
                print(f"处理文件 {md_file} 时出错: {e}")

        print(f"\n导入完成! 共处理了 {processed} 个文件。")
        print(f"数据已存储到: {self.memory_store.db_path}")

        # 打印统计信息
        self.memory_store.print_stats()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="导入文档到Basic Memory数据库")
    parser.add_argument("source_dir", help="源文档目录")
    parser.add_argument(
        "--db",
        default="/Users/chenyi/basic-memory/main.db",
        help="Basic Memory数据库路径 (默认: /Users/chenyi/basic-memory/main.db)",
    )
    parser.add_argument(
        "--parser",
        choices=["openai", "ollama"],
        default="ollama",
        help="解析器类型 (默认: ollama)",
    )
    parser.add_argument(
        "--model",
        default="mistral",
        help="模型名称 (默认: mistral)",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.source_dir):
        print(f"错误: 目录不存在: {args.source_dir}")
        sys.exit(1)

    print(f"Basic Memory文档导入工具 (使用{args.parser} {args.model})")
    print("=====================================")

    try:
        importer = DocumentImporter(args.source_dir, args.db, args.parser, args.model)
        importer.process_documents()
    except Exception as e:
        print(f"\n❌ 处理过程中发生错误: {e}")
        sys.exit(1)


def setup_import_parser(subparsers):
    """设置导入命令的解析器

    Args:
        subparsers: 父解析器的子解析器
    """
    import_parser = subparsers.add_parser("import", help="从各种来源导入知识到Basic Memory")
    import_subparsers = import_parser.add_subparsers(dest="import_type", help="导入类型")

    # 设置LangChain导入
    langchain_parser = import_subparsers.add_parser("langchain", help="使用LangChain从文档导入知识")
    langchain_parser.add_argument("source_dir", help="源文档目录")
    langchain_parser.add_argument("--model", default="gpt-4o-mini", help="使用的OpenAI模型名称")
    langchain_parser.add_argument(
        "--db",
        default="/Users/chenyi/basic-memory/main.db",
        help="Basic Memory数据库路径 (默认: /Users/chenyi/basic-memory/main.db)",
    )

    # 设置更多导入类型...

    return import_parser


def handle_import(args):
    """处理导入命令

    Args:
        args: 解析后的命令行参数
    """
    if args.import_type == "langchain":
        _handle_langchain_import(args)
    else:
        print(f"错误: 未知的导入类型: {args.import_type}")
        sys.exit(1)


def _handle_langchain_import(args):
    """处理LangChain导入

    Args:
        args: 解析后的命令行参数
    """
    source_dir = args.source_dir

    # 检查目录是否存在
    if not os.path.isdir(source_dir):
        print(f"错误: 目录不存在: {source_dir}")
        sys.exit(1)

    # 显示信息
    print(f"使用LangChain处理目录: {source_dir}")
    print("----------------------------")
    print("注意: 此功能需要完成相关依赖模块的实现")
    print(
        """
使用说明:
1. 开发环境:
   - 使用默认数据库路径: python -m adapters.basic_memory.cli import langchain ./docs
   - 自定义数据库路径: python -m adapters.basic_memory.cli import langchain ./docs --db ./my_knowledge.db
   - 修改模型: python -m adapters.basic_memory.cli import langchain ./docs --model gpt-4

2. 生产环境:
   - 确保已正确配置OpenAI API密钥环境变量(OPENAI_API_KEY)
   - 建议使用绝对路径: python -m adapters.basic_memory.cli import langchain /path/to/docs --db /path/to/db.db
   - 对于大型文档集，处理可能需要较长时间
    """
    )
    print("执行操作:")
    print("1. 清空现有Basic Memory数据库")
    print("2. 加载并分割文档")
    print("3. 创建向量嵌入和索引")
    print("4. 提取知识实体和关系")
    print("5. 构建知识图谱")
    print("----------------------------")

    try:
        # 创建处理器并处理文档
        processor = LangChainKnowledgeProcessor(source_dir, model=args.model, db_path=args.db)
        processor.process_documents()

        print("\n处理完成! 您可以:")
        print(f"1. 使用basic_memory export命令导出数据到Obsidian")
        print(f"2. 使用basic_memory query命令进行知识库问答")
        print(f"数据库路径: {args.db}")
    except Exception as e:
        print(f"处理过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
