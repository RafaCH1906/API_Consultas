"""
Gestor de conexión a la base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings
from app.models import Base


settings = get_settings()

# Crear motor de SQLAlchemy con Keepalives y Timeouts robustos para evitar cuelgues de red
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verificar conexión antes de usar
    connect_args={
        "connect_timeout": 15,    # Tiempo límite de conexión inicial (15s)
        "keepalives": 1,          # Activar Keepalives de TCP
        "keepalives_idle": 30,    # Enviar probe de red tras 30 segundos de inactividad
        "keepalives_interval": 5, # Reintentar cada 5 segundos si falla la respuesta
        "keepalives_count": 3,    # Cerrar la conexión si falla 3 veces seguidas
        "options": "-c statement_timeout=30000" # Cancelar automáticamente cualquier consulta que tome más de 30s
    }
)

# Factory para crear sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Session:
    """Dependency injection para obtener sesión de BD en endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crear todas las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Eliminar todas las tablas (solo para desarrollo/testing)"""
    Base.metadata.drop_all(bind=engine)

