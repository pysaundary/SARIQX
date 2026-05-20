import os
from typing import List, Any, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.collector import collector
from loguru import logger

class SariqxConfigSchema(BaseSettings):
    """
    Pydantic V2 Strict Configuration Blueprint.
    Enforces strict environment variable casting across both .env and OS shell parameters.
    """
    ENVIRONMENT: str = Field(default="DEVELOPMENT")
    
    # ⚡ Fix: Type ko temporarily Any/Union ya flexible target dete hain 
    # taaki system env validation bypass karke seedha validator ise parse kare
    ALLOWED_HOSTS: Any = Field(default=["localhost", "127.0.0.1"])
    CORS_ORIGINS: Any = Field(default=["*"])

    DATABASE_URL: str = Field(...) 
    MONGO_URL: str = Field(default="mongodb://localhost:27017")
    MONGO_MAIN_DB: str = Field(default="sariqx_system_db")

    JWT_SECRET_KEY: str = Field(...)
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    BREVO_SMTP_SERVER: str = Field(default="smtp-relay.brevo.com")
    BREVO_SMTP_PORT: int = Field(default=587)
    BREVO_SMTP_USER: str = Field(default="")
    BREVO_SMTP_KEY: str = Field(default="")
    BREVO_FROM_EMAIL: str = Field(default="no-reply@sariqx.com")
    BREVO_FROM_NAME: str = Field(default="SARIQX Support Engine")

    # ⚡ THE HARDENED VALIDATOR: Handles pure OS variables, JSON payloads, and comma strings
    @field_validator("ALLOWED_HOSTS", "CORS_ORIGINS", mode="before")
    @classmethod
    def parse_flexible_lists(cls, value: Any) -> List[str]:
        """
        System environment strings aur local configuration blueprints dono ko 
        bina complex JSON failure ke strictly string array mein breakdown karna.
        """
        if isinstance(value, str):
            value_stripped = value.strip()
            
            # Agar string JSON array format mein dikhe toh handle karo, varna normal split
            if value_stripped.startswith("[") and value_stripped.endswith("]"):
                import json
                try:
                    return json.loads(value_stripped)
                except Exception:
                    pass
            
            if value_stripped == "*":
                return ["*"]
                
            return [item.strip() for item in value_stripped.split(",") if item.strip()]
            
        elif isinstance(value, list):
            return [str(item).strip() for item in value]
            
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


def load_sariqx_config() -> None:
    """
    Pydantic validation ko bootstrap karta hai aur clean typed values 
    ko in-memory Collector Box mein sync karta hai.
    """
    logger.info("🎬 Launching Pydantic Settings validation pipeline...")
    try:
        validated_settings = SariqxConfigSchema()
        clean_payload = validated_settings.model_dump()
        
        # Enforce explicitly that the output stored inside collector is always a structured list
        collector.update(clean_payload)
        logger.info(f"📋 Pydantic fully parsed and type-casted {len(clean_payload)} system variables into Collector.")
        
    except Exception as err:
        logger.critical(f"💥 CONFIGURATION CRASH: Pydantic validation failed for environment parameters!")
        print(f"\n[PYDANTIC ENFORCED EXCEPTION TRACKER]:\n{err}\n", flush=True)
        raise SystemExit(1)