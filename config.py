"""
Configuration management for Label Studio to ClearML pipeline
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Label Studio Configuration
    label_studio_host: str = Field(default="http://localhost:8080", env="LABEL_STUDIO_HOST")
    label_studio_api_key: str = Field(default="", env="LABEL_STUDIO_API_KEY")
    
    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="labelstudio", env="POSTGRES_DB")
    postgres_user: str = Field(default="labelstudio", env="POSTGRES_USER")
    postgres_password: str = Field(default="labelstudio", env="POSTGRES_PASSWORD")
    
    # Webhook Server Configuration
    webhook_host: str = Field(default="0.0.0.0", env="WEBHOOK_HOST")
    webhook_port: int = Field(default=8000, env="WEBHOOK_PORT")
    webhook_secret: Optional[str] = Field(default=None, env="WEBHOOK_SECRET")
    
    # ClearML Configuration
    clearml_api_host: str = Field(default="https://api.clear.ml", env="CLEARML_API_HOST")
    clearml_web_host: str = Field(default="https://app.clear.ml", env="CLEARML_WEB_HOST")
    clearml_files_host: str = Field(default="https://files.clear.ml", env="CLEARML_FILES_HOST")
    clearml_api_access_key: str = Field(default="", env="CLEARML_API_ACCESS_KEY")
    clearml_api_secret_key: str = Field(default="", env="CLEARML_API_SECRET_KEY")
    
    # Dataset Configuration
    clearml_project_name: str = Field(default="ImageAnnotation", env="CLEARML_PROJECT_NAME")
    clearml_dataset_name: str = Field(default="AnnotatedImages", env="CLEARML_DATASET_NAME")
    
    # Shared Data Directory (mounted in Label Studio container)
    shared_data_dir: Path = Field(default=Path("./shared-data"), env="SHARED_DATA_DIR")
    
    # Local paths
    data_dir: Path = Field(default=Path("./data"))
    temp_dir: Path = Field(default=Path("./temp"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.shared_data_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


# Global settings instance
settings = Settings()
