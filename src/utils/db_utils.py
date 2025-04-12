def get_or_create_db_session():
    """获取或创建数据库会话"""
    from src.db import ensure_tables_exist, get_session

    # 确保数据库表存在
    ensure_tables_exist()

    # 获取数据库会话
    return get_session()
