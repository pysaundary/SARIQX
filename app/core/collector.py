import os
from typing import Any, Dict
from loguru import logger

class ObjectCollector:
    """
    SARIQX Centralized Singleton Object Collector Registry.
    Single-process memory context mein global configuration aur states ko
    ultra-fast O(1) lookup speed par manage karne ke liye.
    """
    _instance = None
    _registry: Dict[str, Any] = {}

    def __new__(cls, *args, **kwargs):
        # Enforce strict Singleton boundary at class initialization level
        if cls._instance is None:
            cls._instance = super(ObjectCollector, cls).__new__(cls, *args, **kwargs)
            logger.info("🧠 SARIQX Singleton Object Collector Matrix instantiated in memory.")
        return cls._instance

    def set(self, key: str, value: Any) -> None:
        """Registry mein naya object ya env value set ya overwrite karne ke liye."""
        self._registry[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """O(1) speed par state cache se object uthane ke liye."""
        return self._registry.get(key, default)

    def update(self, payload: Dict[str, Any]) -> None:
        """Bulk update chalane ke liye (jaise poora env dump karna)."""
        self._registry.update(payload)

    def remove(self, key: str) -> None:
        """Kisi specific context variable ko memory se delete karne ke liye."""
        if key in self._registry:
            del self._registry[key]

    def clean(self) -> None:
        """Puri in-memory registry ko flush (khaali) karne ke liye."""
        self._registry.clear()
        logger.warning("♻️ Object Collector state matrix flushed clean.")

    def dump_env(self) -> None:
        """
        Application startup par saare system environment variables ko 
        utha kar is in-memory dict mein dump karne ki utilities.
        """
        # Load critical configurations with fallbacks
        env_data = {
            "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/sariqx_db"),
            "MONGO_URL": os.getenv("MONGO_URL", "mongodb://localhost:27017"),
            "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "JWT_SECRET": os.getenv("JWT_SECRET", "SARIQX_SUPER_SECRET_TOKEN_MATRIX_2026"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "DEVELOPMENT")
        }
        self.update(env_data)
        logger.info(f"📋 Environment variables successfully cached inside Object Collector [{len(env_data)} variables].")

# Global access object export kar dete hain shortcut ke liye
collector = ObjectCollector()