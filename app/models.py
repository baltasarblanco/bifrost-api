from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from app.database import Base


class ArmaduraDB(Base):
    # El nombre real que tendrá la tabla en la base de datos
    __tablename__ = "armaduras"

    # Definimos las columnas exactas
    id = Column(
        Integer, primary_key=True, index=True
    )  # Identificador único autoincremental
    modelo = Column(
        String, unique=True, index=True
    )  # No puede haber dos armaduras con el mismo modelo
    nivel_energia = Column(Integer)
    activa = Column(Boolean, default=False)
    # 🆕 El interruptor de borrado lógico:
    is_deleted = Column(Boolean, default=False)


class UsuarioDB(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    # 🆕 Nueva columna para el mando:
    is_admin = Column(Boolean, default=False)

class ReservaDB(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    # Claves foráneas que conectan esta isla con las otras dos
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # Asumo que la armadura se identifica por un ID o un Modelo (ajustá a String si tu PK de armaduras es el modelo)
    armadura_modelo = Column(String, ForeignKey("armaduras.modelo"), nullable=False)

    # Tiempo Universal (timezone=True garantiza que PostgreSQL lo entienda con zona horaria)
    fecha_inicio = Column(DateTime(timezone=True), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=False)

    estado = Column(
        String, default="activa"
    )  # Puede ser: activa, finalizada, cancelada
