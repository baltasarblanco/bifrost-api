from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. EL DISCO DURO FLEXIBLE
# Leemos la URL desde las variables de entorno (inyectadas por Docker)
# Si no la encuentra (ej. si corrés el script sin Docker), usa SQLite de respaldo
SQLALCHEMY_DATABASE_URL = "postgresql://ronin:helados_fuente@localhost:5432/bifrost_db"

# 2. EL MOTOR
# Postgres no necesita "check_same_thread", así que condicionamos la creación
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. LA SESIÓN
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. LA BASE
Base = declarative_base()


# Función al final:
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
