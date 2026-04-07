from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.core.security import SECRET_KEY, ALGORITHM
from app.schemas.token import TokenPayload

# 1. Configuración del esquema OAuth2
# Esto le dice a FastAPI en qué URL los usuarios consiguen su token.
# Además, habilita automáticamente el botón "Authorize" en la documentación de Swagger.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/access-token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependencia global de seguridad. 
    Intercepta el token JWT, lo valida y extrae el usuario.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Intentamos abrir el candado usando nuestra clave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenPayload(sub=username)
        
    except jwt.ExpiredSignatureError:
        # El token es válido, pero ya pasaron los 15 minutos
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado. Por favor, inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        # El token es inválido (fue modificado, firmado con otra clave, etc.)
        raise credentials_exception

    # ⚠️ TODO: En el futuro, aquí harás una consulta a la DB:
    # user = get_user_from_db(username=token_data.sub)
    # if not user: raise credentials_exception
    # return user

    # Por ahora, devolvemos el payload simulando que es nuestro usuario autenticado
    return token_data