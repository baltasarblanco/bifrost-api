import os
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt

# ==========================================
# 1. CONFIGURACIÓN CRIPTOGRÁFICA (Bcrypt)
# ==========================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================================
# 2. CONFIGURACIÓN DE TOKENS (JWT)
# ==========================================
# En producción, esto se carga desde un archivo .env
SECRET_KEY = os.getenv("SECRET_KEY", "tu_super_clave_secreta_de_desarrollo_cambiar_en_prod")
ALGORITHM = "HS256"
# ESTA es la variable que causaba el error:
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")) 


# ==========================================
# 3. FUNCIONES DE CONTRASEÑAS
# ==========================================
def get_password_hash(password: str) -> str:
    """Toma una contraseña en texto plano y devuelve su hash seguro."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña ingresada con el hash guardado en la base de datos."""
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================
# 4. FUNCIONES DE AUTENTICACIÓN
# ==========================================
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Genera un JSON Web Token (JWT) stateless."""
    to_encode = data.copy()
    
    # Manejo de tiempo en UTC
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Firma del token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt