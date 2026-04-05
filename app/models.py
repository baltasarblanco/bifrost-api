from sqlalchemy import Boolean, Column, Integer, String
from .database import Base

class ArmaduraDB(Base):
    # El nombre real que tendrá la tabla en la base de datos
    __tablename__ = "armaduras"

    # Definimos las columnas exactas
    id = Column(Integer, primary_key=True, index=True) # Identificador único autoincremental
    modelo = Column(String, unique=True, index=True)   # No puede haber dos armaduras con el mismo modelo
    nivel_energia = Column(Integer)
    activa = Column(Boolean, default=False)