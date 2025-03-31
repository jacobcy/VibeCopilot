"""Configuration management for VibeCopilot."""
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file if it exists
load_dotenv()


class AppConfig(BaseModel):
    """Application configuration settings."""

    # Application settings
    app_name: str = "VibeCopilot"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "debug"

    # AI settings
    openai_api_key: Optional[str] = None
    ai_model: str = "gpt-4o"
    provider: str = "openai"

    # Project settings
    project_dir: str = "~/projects"
    default_template: str = "standard"
    auto_save: bool = True
    auto_backup: bool = True

    class Config:
        """Configuration for settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class ProjectConfig(BaseModel):
    """Project-specific configuration."""

    name: str
    path: Path
    description: Optional[str] = None
    template: str = "standard"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Path) -> "ProjectConfig":
        """Load project configuration from file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        # Ensure 'path' is a Path object
        if "path" in config_data and isinstance(config_data["path"], str):
            config_data["path"] = Path(config_data["path"])

        return cls(**config_data)

    def save(self, config_path: Path) -> None:
        """Save project configuration to file."""
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Path to string for YAML serialization
        config_dict = self.model_dump()
        config_dict["path"] = str(config_dict["path"])

        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)


# Global app config instance
app_config = AppConfig()


def get_app_config() -> AppConfig:
    """Get the application configuration."""
    return app_config


def get_project_config(project_path: Path) -> Optional[ProjectConfig]:
    """Get project configuration if it exists."""
    config_path = project_path / ".vibecopilot" / "config.yml"
    if not config_path.exists():
        return None

    return ProjectConfig.load(config_path)


def create_project_config(
    name: str,
    path: Path,
    description: Optional[str] = None,
    template: str = "standard",
) -> ProjectConfig:
    """Create a new project configuration."""
    config = ProjectConfig(
        name=name, path=path, description=description, template=template
    )

    # Save the configuration
    config_path = path / ".vibecopilot" / "config.yml"
    config.save(config_path)

    return config
