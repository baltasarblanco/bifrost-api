from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from redis.asyncio import Redis

from app.core.security import SECRET_KEY, ALGORITHM
from app.core.redis_client import get_redis
from app.core.token_blacklist import is_token_revoked
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/access-token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis),
) -> TokenPayload:
    """
    Dependencia global de seguridad.
    
    Validaciones en orden (fail-fast):
    1. Firma del JWT válida (con SECRET_KEY).
    2. No expirado (claim "exp").
    3. Tiene "sub" y "jti" en el payload.
    4. JTI NO está en la blacklist de Redis (logout previo).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")

        if username is None or jti is None:
            raise credentials_exception

        token_data = TokenPayload(sub=username, jti=jti)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado. Por favor, inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    # Chequeo post-firma: ¿fue revocado explícitamente?
    if await is_token_revoked(redis, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado. Por favor, inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data