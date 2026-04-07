from pydantic import BaseModel, EmailStr
from datetime import datetime
from pydantic import ConfigDict, model_validator


# Lo que EXIGIMOS del cliente (El body del POST)
class UsuarioCreate(BaseModel):
    email: EmailStr  # EmailStr valida que tenga un formato de correo válido (@)
    password: str


# Lo que DEVOLVEMOS al cliente (Fijate que NO incluimos la contraseña)
class UsuarioResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True  # Permite a Pydantic leer el objeto de SQLAlchemy


class ReservaBase(BaseModel):
    armadura_modelo: str
    fecha_inicio: datetime
    fecha_fin: datetime


class ReservaCreate(ReservaBase):
    # Validador avanzado: Se ejecuta automáticamente para revisar la lógica de negocio temporal
    @model_validator(mode="after")
    def verificar_fechas(self) -> "ReservaCreate":
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError(
                "Operación rechazada: La fecha de fin debe ser posterior a la de inicio."
            )
        # (Opcional) Podríamos verificar que fecha_inicio no sea en el pasado,
        # pero para testear nos conviene dejarlo libre por ahora.
        return self


class ReservaResponse(ReservaBase):
    id: int
    usuario_id: int
    estado: str

    model_config = ConfigDict(from_attributes=True)
