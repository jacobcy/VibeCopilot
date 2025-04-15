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
    },
    "paths": {
        "project_root": ConfigValue(str(Path.cwd()), env_key="PROJECT_ROOT"),
        "templates_dir": ConfigValue("templates"),
        "data_dir": ConfigValue("data"),
        "output_dir": ConfigValue("output"),
        "docs_source_dir": ConfigValue("docs", env_key="DOCS_SOURCE_DIR"),
        "obsidian_vault_dir": ConfigValue(".obsidian/vault", env_key="OBSIDIAN_VAULT_DIR"),
        "docs_engine_db": ConfigValue("data/docs_engine.db", env_key="DOCS_ENGINE_DB_PATH"),
        "docs_vector_db": ConfigValue("data/docs_vector.db", env_key="DOCS_VECTOR_DB_PATH"),
    },
    "database": {
        "url": ConfigValue("sqlite:///data/vibecopilot.db", env_key="DATABASE_URL"),
        "type": ConfigValue("sqlite"),
        "debug": ConfigValue(False, env_key="DB_DEBUG"),
    },
    "ai": {
        "provider": ConfigValue("openai", env_key="AI_PROVIDER"),
        "model": ConfigValue("gpt-4o-mini", env_key="AI_MODEL"),
        "temperature": ConfigValue(0.7, env_key="AI_TEMPERATURE"),
        "openai": {
            "api_key": ConfigValue(None, env_key="OPENAI_API_KEY"),
        },
        "anthropic": {
            "api_key": ConfigValue(None, env_key="ANTHROPIC_API_KEY"),
        },
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
    # 工作流配置
    "workflow": {
        "templates_dir": ConfigValue(str(PROJECT_ROOT / "templates" / "flow"), env_key="VIBECOPILOT_TEMPLATE_DIR"),
        "workflows_dir": ConfigValue(str(PROJECT_ROOT / "workflows"), env_key="VIBECOPILOT_WORKFLOW_DIR"),
        "template_extension": ConfigValue(".json"),
    },
    # GitHub配置
    "github": {
        "owner": ConfigValue(None, env_key="GITHUB_OWNER"),
        "repo": ConfigValue(None, env_key="GITHUB_REPO"),
        "api_token": ConfigValue(None, env_key="GITHUB_TOKEN"),
    },
}
