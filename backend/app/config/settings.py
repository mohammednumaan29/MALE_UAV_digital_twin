"""
Application Settings & Configuration
Loads environment variables with fallback defaults.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str = "Rotax 914 Aero-Piston Engine Digital Twin Backend"
    APP_VERSION: str = "0.1.0"
    SERVICE_NAME: str = "rotax914-digital-twin-backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Database configuration
    DATABASE_URL: str = "sqlite:///./rotax914.db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "rotax914_db"
    POSTGRES_USER: str = "rotax_user"
    POSTGRES_PASSWORD: str = "rotax_pass"

    # Physics Model Info
    PHYSICS_MODEL_INFO: str = "Physics-Informed Aerodynamic & Thermodynamic Virtual Engine (Phase 1 Ready)"
    
    # ML Models Info
    ML_MODELS_INFO: str = "Modular Pipeline (Isolation Forest, Classifier, Degradation, RUL Regressor)"

    # Health engine configuration
    HEALTHY_THRESHOLD: float = 90.0
    NORMAL_THRESHOLD: float = 70.0
    DEGRADED_THRESHOLD: float = 40.0
    HEALTH_SCORE_WEIGHTS: dict = {
        "anomaly_score": 25.0,
        "fault_probability": 30.0,
        "severity": 20.0,
        "thermal_residual": 12.0,
        "vibration": 8.0,
        "lubrication": 5.0,
    }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
