import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, CheckConstraint, Index
from sqlalchemy.orm import declarative_mixin, relationship
from sqlalchemy.sql import func
from app.database import Base

# ==========================================
# 🧬 1. MIXINS (Clases Abstractas de Herencia)
# ==========================================

@declarative_mixin
class TimestampMixin:
    """Añade automáticamente campos de auditoría temporal a cualquier tabla."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # onupdate fuerza a Postgres a cambiar esta fecha solo cuando se modifica la fila
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

@declarative_mixin
class SoftDeleteMixin:
    """Inyecta el borrado lógico y su índice."""
    is_deleted = Column(Boolean, default=False, index=True)


# ==========================================
# 🏷️ 2. ENUMERADORES ESTRICTOS
# ==========================================

class EstadoReserva(str, enum.Enum):
    ACTIVA = "activa"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"

class NivelEnergiaArmadura(str, enum.Enum):
    CRITICA = "critica"
    OPERATIVA = "operativa"
    SOBRECARGA = "sobrecarga"


# ==========================================
# 🏗️ 3. MODELOS DE BASE DE DATOS (Entidades)
# ==========================================

class UsuarioDB(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Relación Mágica: Permite hacer `usuario.reservas` en el código Python
    reservas = relationship("ReservaDB", back_populates="piloto", lazy="dynamic")


class ArmaduraDB(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "armaduras"

    id = Column(Integer, primary_key=True, index=True)
    modelo = Column(String, unique=True, index=True, nullable=False)
    
    # Reemplazamos el Integer simple por un Enum de estado para mayor control
    estado_energia = Column(Enum(NivelEnergiaArmadura), default=NivelEnergiaArmadura.OPERATIVA, nullable=False)
    activa = Column(Boolean, default=False)

    # Relación Mágica
    historial_reservas = relationship("ReservaDB", back_populates="armadura")


class ReservaDB(Base, TimestampMixin):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    armadura_modelo = Column(String, ForeignKey("armaduras.modelo", onupdate="CASCADE"), nullable=False, index=True)

    fecha_inicio = Column(DateTime(timezone=True), nullable=False, index=True)
    fecha_fin = Column(DateTime(timezone=True), nullable=False, index=True)

    estado = Column(Enum(EstadoReserva), default=EstadoReserva.ACTIVA, nullable=False, index=True)

    # Enlaces bidireccionales de ORM
    piloto = relationship("UsuarioDB", back_populates="reservas")
    armadura = relationship("ArmaduraDB", back_populates="historial_reservas")

    # ==========================================
    # 🛡️ REGLAS DE NEGOCIO A NIVEL MOTOR (Restricciones e Índices Compuestos)
    # ==========================================
    __table_args__ = (
        # 1. Postgres prohíbe que alguien reserve tiempo hacia atrás
        CheckConstraint('fecha_fin > fecha_inicio', name='check_logica_temporal'),
        
        # 2. Índice hiper-optimizado para buscar el dashboard del usuario más rápido
        Index('idx_usuario_estado', 'usuario_id', 'estado'),
        
        # 3. Índice para el motor de choques temporales de la armadura
        Index('idx_armadura_rango', 'armadura_modelo', 'fecha_inicio', 'fecha_fin'),
    )