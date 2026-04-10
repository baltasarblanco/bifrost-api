from pydantic import BaseModel, EmailStr, ConfigDict, model_validator
from datetime import datetime, timezone
# Importamos los ENUMS directamente desde tus modelos de base de datos
from app.models import EstadoReserva, NivelEnergiaArmadura
from .token import Token as Token, TokenPayload as TokenPayload

# ==========================================
# 🛡️ USUARIOS
# ==========================================
class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str

class UsuarioResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_admin: bool  # 🆕 Agregamos el campo de admin
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 🛡️ ARMADURAS
# ==========================================
class ArmaduraBase(BaseModel):
    modelo: str
    activa: bool = True
    estado_energia: NivelEnergiaArmadura  # 🆕 Usamos el Enum estricto

class ArmaduraResponse(ArmaduraBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 🛡️ RESERVAS
# ==========================================
class ReservaBase(BaseModel):
    armadura_modelo: str
    fecha_inicio: datetime
    fecha_fin: datetime

class ReservaCreate(ReservaBase):
    @model_validator(mode="after")
    def verificar_fechas(self) -> "ReservaCreate":
        # 🆕 Nos aseguramos de que las fechas tengan timezone (UTC)
        if self.fecha_inicio.tzinfo is None:
            self.fecha_inicio = self.fecha_inicio.replace(tzinfo=timezone.utc)
        if self.fecha_fin.tzinfo is None:
            self.fecha_fin = self.fecha_fin.replace(tzinfo=timezone.utc)

        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError(
                "Operación rechazada: La fecha de fin debe ser posterior a la de inicio."
            )
        return self

class ReservaResponse(ReservaBase):
    id: int
    usuario_id: int
    estado: EstadoReserva  # 🆕 Usamos el Enum en lugar de 'str'
    
    model_config = ConfigDict(from_attributes=True)