from pydantic import BaseModel, EmailStr

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
        from_attributes = True # Permite a Pydantic leer el objeto de SQLAlchemy