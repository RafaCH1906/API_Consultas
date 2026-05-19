"""
Manejador de caché Redis
"""
import json
from typing import Optional, Any
import redis
from app.config import get_settings


class RedisCache:
    """Gestor de caché con Redis"""

    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.REDIS_ENABLED
        self.client = None

        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_keepalive=True,
                )
                # Verificar que Redis está disponible
                self.client.ping()
            except Exception as e:
                print(f"Advertencia: No se pudo conectar a Redis: {e}")
                self.enabled = False
                self.client = None

    def get(self, key: str) -> Optional[dict]:
        """Obtiene un valor del caché"""
        if not self.enabled or not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error al leer del caché: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Guarda un valor en el caché"""
        if not self.enabled or not self.client:
            return False

        try:
            ttl = ttl or self.settings.REDIS_TTL
            self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
        except Exception as e:
            print(f"Error al escribir en caché: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Elimina un valor del caché"""
        if not self.enabled or not self.client:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Error al eliminar del caché: {e}")
            return False

    def build_dni_key(self, numero: str) -> str:
        """Construye la clave de caché para DNI"""
        return f"{self.settings.REDIS_KEY_PREFIX}:dni:{numero}"

    def build_ruc_key(self, numero: str) -> str:
        """Construye la clave de caché para RUC"""
        return f"{self.settings.REDIS_KEY_PREFIX}:ruc:{numero}"


# Instancia global del caché
cache = RedisCache()

