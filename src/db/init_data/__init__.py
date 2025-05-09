"""
数据库初始化模块 - 提供初始数据加载函数
"""

# 避免循环导入
import logging

logger = logging.getLogger(__name__)


def load_all_initial_data(session):
    """加载所有初始数据"""
    logger.info("开始加载初始数据...")

    # 修改导入顺序，先导入没有依赖的数据
    from .roadmaps import init_roadmaps
    from .rules import init_rules
    from .templates import init_templates
    from .workflows import init_workflows

    # 有条件地导入可能存在问题的模块
    try:
        from .memory_items import init_memory_items

        memory_items_available = True
    except ImportError as e:
        logger.warning(f"内存项初始化模块不可用: {e}")
        memory_items_available = False

    try:
        from .docs import init_docs

        docs_available = True
    except ImportError as e:
        logger.warning(f"文档初始化模块不可用: {e}")
        docs_available = False

    # 执行初始化，确保依赖顺序正确，检查每个函数是否接受session参数
    logger.info("初始化模板...")
    # 检查函数签名
    import inspect

    if len(inspect.signature(init_templates).parameters) == 0:
        init_templates()  # 不接受参数
    else:
        init_templates(session)  # 接受session参数

    logger.info("初始化规则...")
    if len(inspect.signature(init_rules).parameters) == 0:
        init_rules()  # 不接受参数
    else:
        init_rules(session)  # 接受session参数

    logger.info("初始化路线图...")
    if len(inspect.signature(init_roadmaps).parameters) == 0:
        init_roadmaps()  # 不接受参数
    else:
        init_roadmaps(session)  # 接受session参数

    logger.info("初始化工作流...")
    if len(inspect.signature(init_workflows).parameters) == 0:
        init_workflows()  # 不接受参数
    else:
        init_workflows(session)  # 接受session参数

    if memory_items_available:
        logger.info("初始化内存项...")
        if len(inspect.signature(init_memory_items).parameters) == 0:
            init_memory_items()  # 不接受参数
        else:
            init_memory_items(session)  # 接受session参数

    if docs_available:
        logger.info("初始化文档...")
        if len(inspect.signature(init_docs).parameters) == 0:
            init_docs()  # 不接受参数
        else:
            init_docs(session)  # 接受session参数

    logger.info("初始数据加载完成")
    return True
