"""
默认配置定义模块

定义应用程序的默认配置值。
"""

from pathlib import Path

from src.core.config.models import ConfigEnvironment, ConfigValue

# 项目根目录
PROJECT_ROOT = Path(__file__).parents[3]

# 默认配置定义
DEFAULT_CONFIG = {
    "app": {
        "name": ConfigValue("VibeCopilot", env_key="APP_NAME"),
        "version": ConfigValue("0.1.0", env_key="APP_VERSION"),
        "environment": ConfigValue(
            ConfigEnvironment.DEVELOPMENT.value,
            env_key="APP_ENV",
            validator=lambda x: x in [e.value for e in ConfigEnvironment],
        ),
        "log_level": ConfigValue("INFO", env_key="LOG_LEVEL"),
        "debug": ConfigValue(True, env_key="DEBUG"),
        "developer": ConfigValue("Default Developer", env_key="APP_DEVELOPER"),
    },
    "paths": {
        "project_root": ConfigValue(str(Path.cwd()), env_key="PROJECT_ROOT"),
        "templates_dir": ConfigValue("templates"),
        "data_dir": ConfigValue(".vibecopilot"),
        "output_dir": ConfigValue("output"),
        "docs_source_dir": ConfigValue("docs", env_key="DOCS_SOURCE_DIR"),
        "obsidian_vault_dir": ConfigValue(".obsidian/vault", env_key="OBSIDIAN_VAULT_DIR"),
        "vector_db": ConfigValue(".vibecopilot/chroma_db", env_key="VECTOR_DB_PATH"),
        "notion_export_dir": ConfigValue("exports", env_key="NOTION_OUTPUT_DIR"),
        "agent_work_dir": ConfigValue(".ai", env_key="AGENT_WORK_DIR"),
        "docs_engine_db": ConfigValue(".vibecopilot/docs_engine.db", env_key="DOCS_ENGINE_DB_PATH"),
        "docs_vector_db": ConfigValue(".vibecopilot/docs_vector.db", env_key="DOCS_VECTOR_DB_PATH"),
    },
    "database": {
        "url": ConfigValue("sqlite:///.vibecopilot/vibecopilot.db", env_key="DATABASE_URL"),
        "type": ConfigValue("sqlite"),
        "debug": ConfigValue(False, env_key="DB_DEBUG"),
        "pool_size": ConfigValue(20, env_key="DB_POOL_SIZE"),
        "max_overflow": ConfigValue(30, env_key="DB_MAX_OVERFLOW"),
        "pool_timeout": ConfigValue(60, env_key="DB_POOL_TIMEOUT"),
        "pool_recycle": ConfigValue(3600, env_key="DB_POOL_RECYCLE"),
    },
    "ai": {
        "provider": ConfigValue("openai", env_key="AI_PROVIDER"),
        "chat_model": ConfigValue("gpt-4o-mini", env_key="AI_CHAT_MODEL"),
        "temperature": ConfigValue(0.7, env_key="AI_TEMPERATURE"),
        "embedding_model": ConfigValue("text-embedding-3-small", env_key="AI_EMBEDDING_MODEL"),
        "embedding_dimension": ConfigValue(384, env_key="AI_EMBEDDING_DIMENSION"),
        "openai": {
            "api_key": ConfigValue(None, env_key="OPENAI_API_KEY"),
        },
        "anthropic": {
            "api_key": ConfigValue(None, env_key="ANTHROPIC_API_KEY"),
        },
    },
    "agent": {
        "name": ConfigValue("VibeAgent", env_key="AGENT_NAME"),
    },
    "ide": {
        "name": ConfigValue("cursor", env_key="IDE_NAME"),
    },
    "content_parsing": {
        "parser": ConfigValue("openai", env_key="VIBE_CONTENT_PARSER"),
        "openai_model": ConfigValue("gpt-4o-mini", env_key="VIBE_OPENAI_MODEL"),
        "ollama_model": ConfigValue("mistral", env_key="VIBE_OLLAMA_MODEL"),
        "ollama_base_url": ConfigValue("http://localhost:11434", env_key="VIBE_OLLAMA_BASE_URL"),
    },
    "notion_export": {
        "api_key": ConfigValue(None, env_key="NOTION_API_KEY"),
        "page_id": ConfigValue(None, env_key="NOTION_PAGE_ID"),
        "output_filename": ConfigValue("notion_export.md", env_key="NOTION_OUTPUT_FILENAME"),
        "recursive": ConfigValue(True, env_key="NOTION_RECURSIVE_EXPORT"),
        "max_depth": ConfigValue(0, env_key="NOTION_MAX_DEPTH"),
        "use_page_title": ConfigValue(True, env_key="NOTION_USE_PAGE_TITLE_AS_FILENAME"),
    },
    "github": {
        "owner": ConfigValue(None, env_key="GITHUB_OWNER"),
        "repo": ConfigValue(None, env_key="GITHUB_REPO"),
        "api_token": ConfigValue(None, env_key="GITHUB_TOKEN"),
        "project_name": ConfigValue(None, env_key="ROADMAP_PROJECT_NAME"),
    },
    "features": {
        "enable_command_line": ConfigValue(True),
        "enable_mcp": ConfigValue(True),
        "enable_web_ui": ConfigValue(False),
    },
    "sync": {
        "auto_sync_docs": ConfigValue(False, env_key="AUTO_SYNC_DOCS"),
        "auto_sync_interval": ConfigValue(300, env_key="AUTO_SYNC_INTERVAL"),
    },
    "workflow": {
        "templates_dir": ConfigValue(str(PROJECT_ROOT / "templates" / "flow"), env_key="VIBECOPILOT_TEMPLATE_DIR"),
        "workflows_dir": ConfigValue(str(PROJECT_ROOT / "workflows"), env_key="VIBECOPILOT_WORKFLOW_DIR"),
        "template_extension": ConfigValue(".json"),
    },
    "project_settings": {
        "default_template": ConfigValue("standard", env_key="DEFAULT_TEMPLATE"),
        "auto_save": ConfigValue(True, env_key="AUTO_SAVE"),
        "auto_backup": ConfigValue(True, env_key="AUTO_BACKUP"),
    },
}
