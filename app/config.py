"""
Configuración de la aplicación
Carga variables de entorno desde .env
"""
import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """Configuración centralizada de la aplicación"""

    # Base de datos PostgreSQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "sunat_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "tu_password")

    # URL de conexión PostgreSQL
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?client_encoding=utf8"

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_ENABLED: bool = bool(int(os.getenv("REDIS_ENABLED", "1")))
    REDIS_TTL: int = int(os.getenv("REDIS_TTL", "86400"))  # 24 horas por defecto
    REDIS_KEY_PREFIX: str = os.getenv("REDIS_KEY_PREFIX", "sunat")

    # Redis URL
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")

    # Seguridad por API key (temporal hasta implementar usuarios/JWT multi-tenant)
    SUPERADMIN_API_KEYS: str = os.getenv("SUPERADMIN_API_KEYS", "")
    ADMIN_API_KEYS: str = os.getenv("ADMIN_API_KEYS", "")
    OPERATOR_API_KEYS: str = os.getenv("OPERATOR_API_KEYS", "")
    READONLY_API_KEYS: str = os.getenv("READONLY_API_KEYS", "")

    # ETL
    PADRON_RUC_PATH: str = os.getenv("PADRON_RUC_PATH", "padron_reducido_ruc.txt")
    ETL_CHUNK_SIZE: int = int(os.getenv("ETL_CHUNK_SIZE", "50000"))
    ETL_LOG_INTERVAL: int = int(os.getenv("ETL_LOG_INTERVAL", "5"))
    ETL_VALIDATE_ONLY: bool = bool(int(os.getenv("ETL_VALIDATE_ONLY", "0")))


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la instancia única de configuración (patrón Singleton)"""
    return Settings()

