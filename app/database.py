"""
Configuración del engine de SQLAlchemy y gestión de sesiones.

La URL de conexión viene de Settings (12-factor config),
no hardcodeada. Diferente valor en dev/staging/prod
sin cambiar una sola línea de código.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

# 1. URL DE CONEXIÓN
# Leída desde .env vía pydantic-settings (Single Source of Truth).
# Sin fallbacks silenciosos: si falta DATABASE_URL, la app NO arranca.
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 2. EL MOTOR
# Postgres no necesita "check_same_thread" (eso es específico de SQLite).
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,   # Valida conexión antes de usarla (evita errores por conexiones stale)
        pool_size=10,         # Pool consistente con el de Redis
        max_overflow=20,      # Conexiones extra bajo picos de tráfico
    )

# 3. LA SESIÓN
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. LA BASE
Base = declarative_base()


def get_db():
    """
    Generador de sesiones para la base de datos.
    Abre la conexión por cada request y la cierra automáticamente al terminar.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()