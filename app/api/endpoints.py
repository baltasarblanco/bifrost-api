from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Importaciones de seguridad
from app.core.security import (
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    get_password_hash, 
    verify_password
)
from app.schemas.token import Token, TokenPayload
from app.api.dependencies import get_current_user

# Importaciones de Base de Datos y Modelos
from app.database import get_db  # <-- Asegurate de que esta ruta a tu get_db sea la correcta
from app.models import UsuarioDB
from app.schemas import UsuarioCreate, UsuarioResponse # <-- Vi en tu Swagger que ya tenés estos esquemas

router = APIRouter()

# ==========================================
# 1. REGISTRO DE USUARIO (El Blindaje)
# ==========================================
@router.post("/usuarios/", response_model=UsuarioResponse)
def crear_usuario(usuario_in: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario encriptando su contraseña con Bcrypt.
    """
    # Verificamos si el email ya existe para evitar duplicados
    user_exists = db.query(UsuarioDB).filter(UsuarioDB.email == usuario_in.email).first()
    if user_exists:
        raise HTTPException(
            status_code=400,
            detail="El email ya está registrado en el sistema."
        )
    
    # 🛡️ PASO CLAVE: Hasheamos la contraseña
    hashed_pw = get_password_hash(usuario_in.password)
    
    # Guardamos en la base de datos usando el hash, NUNCA la contraseña en texto plano
    nuevo_usuario = UsuarioDB(
        email=usuario_in.email,
        hashed_password=hashed_pw
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return nuevo_usuario

# ==========================================
# 2. LOGIN (La Puerta de Entrada)
# ==========================================
@router.post("/login/access-token", response_model=Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint para autenticar usuarios contra la base de datos y devolver un JWT.
    """
    # 💡 NOTA SENIOR: OAuth2 usa el campo 'username' por defecto. 
    # Como nosotros usamos email, mapeamos form_data.username a UsuarioDB.email
    user = db.query(UsuarioDB).filter(UsuarioDB.email == form_data.username).first()
    
    # Validamos que el usuario exista y que la contraseña coincida con el hash
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Si todo está OK, generamos el JWT usando el email del usuario como "Subject" (sub)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

# ==========================================
# 3. ZONA VIP
# ==========================================
@router.get("/ruta-privada")
def ruta_super_secreta(current_user: TokenPayload = Depends(get_current_user)):
    """
    Este endpoint está blindado. Si llegás acá, es porque tu JWT es válido.
    """
    return {
        "mensaje": "¡Bienvenido a la zona VIP de Bifrost!",
        "usuario_logueado": current_user.sub
    }