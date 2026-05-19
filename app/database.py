"""
Gestor de conexión a la base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings
from app.models import Base


settings = get_settings()

# Crear motor de SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verificar conexión antes de usar
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

