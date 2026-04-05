from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. EL DISCO DURO
SQLALCHEMY_DATABASE_URL = "sqlite:///./bifrost.db"

# 2. EL MOTOR
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. LA SESIÓN
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. LA BASE (¡Esta es la pieza que el sistema no encuentra!)
Base = declarative_base()