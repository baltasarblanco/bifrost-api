import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# ==========================================
# 1. CONFIGURACIÓN CRIPTOGRÁFICA (Bcrypt)
# ==========================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================================
# 2. CONFIGURACIÓN DE TOKENS (JWT)
# ==========================================


settings = get_settings()

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


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
    """Genera un JSON Web Token (JWT) stateless con JTI único para revocación."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # JTI (JWT ID): UUID único por token, permite revocación individual en Redis.
    # Estándar RFC 7519 Section 4.1.7.
    jti = str(uuid.uuid4())

    to_encode.update({"exp": expire, "jti": jti})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
