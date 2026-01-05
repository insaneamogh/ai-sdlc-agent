#_______________This Code was generated using GenAI tool: Codify, Please check for accuracy_______________#

"""
Application Configuration Module

This module handles all configuration settings using Pydantic Settings.
Settings are loaded from environment variables and .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden by setting the corresponding
    environment variable (case-insensitive).
    """
    
    # ===========================================
    # OpenAI Configuration
    # ===========================================
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for LLM access"
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use"
    )
    
    # ===========================================
    # Jira Configuration
    # ===========================================
    jira_url: str = Field(
        default="",
        description="Jira instance URL"
    )
    jira_email: str = Field(
        default="",
        description="Jira account email"
    )
    jira_api_token: str = Field(
        default="",
        description="Jira API token"
    )
    
    # ===========================================
    # GitHub Configuration
    # ===========================================
    github_token: str = Field(
        default="",
        description="GitHub personal access token"
    )
    
    # ===========================================
    # Application Settings
    # ===========================================
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # ===========================================
    # Vector Database Settings
    # ===========================================
    chroma_persist_directory: str = Field(
        default="./chroma_data",
        description="Directory to persist ChromaDB data"
    )
    
    # ===========================================
    # API Settings
    # ===========================================
    api_title: str = Field(
        default="AI SDLC Agent",
        description="API title for documentation"
    )
    api_version: str = Field(
        default="0.1.0",
        description="API version"
    )
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once
    and reused across the application.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Convenience function to check if required settings are configured
def validate_settings() -> dict:
    """
    Validate that required settings are configured.
    
    Returns:
        dict: Validation results with status and missing settings
    """
    settings = get_settings()
    missing = []
    warnings = []
    
    # Check required settings
    if not settings.openai_api_key:
        missing.append("OPENAI_API_KEY")
    
    # Check optional but recommended settings
    if not settings.jira_url:
        warnings.append("JIRA_URL (Jira integration disabled)")
    if not settings.github_token:
        warnings.append("GITHUB_TOKEN (GitHub integration disabled)")
    
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "warnings": warnings
    }

#__________________________GenAI: Generated code ends here______________________________#
