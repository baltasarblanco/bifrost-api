from fastapi.security import OAuth2PasswordBearer
import jwt
from redis.asyncio import Redis

from app.core.security import SECRET_KEY, ALGORITHM
from app.core.redis_client import get_redis
from app.core.token_blacklist import is_token_revoked
from app.schemas.token import TokenPayload

from fastapi import Request, Header, HTTPException, status as http_status, Depends, status

from app.core.idempotency import (
    get_cached_response,
    hash_request_body,
    store_response,
)

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

# =============================================================================
# Idempotency dependency
# =============================================================================
class IdempotencyContext:
    """
    Carrier object passed from the dependency to the endpoint.

    - If `cached_response` is set, the endpoint MUST return it verbatim
      without executing its business logic (the response was already
      computed in a previous request with the same key).
    - If `cached_response` is None, the endpoint proceeds normally and
      the dependency will store its response afterwards via `persist`.
    """

    def __init__(
        self,
        idempotency_key: str,
        body_hash: str,
        cached_response: dict | None,
        redis: Redis,
        endpoint_name: str,
    ):
        self.idempotency_key = idempotency_key
        self.body_hash = body_hash
        self.cached_response = cached_response
        self._redis = redis
        self._endpoint_name = endpoint_name

    async def persist(self, status_code: int, body: dict) -> None:
        """Store the endpoint's computed response for future retries."""
        await store_response(
            redis=self._redis,
            endpoint=self._endpoint_name,
            idempotency_key=self.idempotency_key,
            status_code=status_code,
            body=body,
            body_hash=self.body_hash,
        )


def idempotency_dependency(endpoint_name: str):
    """
    Factory that builds a FastAPI dependency for a specific endpoint.

    Usage:
        @router.post("/reservas/")
        async def crear_reserva(
            idem: IdempotencyContext = Depends(idempotency_dependency("reservas")),
            ...
        ):
            if idem.cached_response:
                return idem.cached_response["body"]
            # ... normal logic ...
            await idem.persist(201, response.dict())

    The factory pattern lets different endpoints share the dependency code
    while using distinct Redis namespaces (idempotency:reservas:...,
    idempotency:pagos:..., etc.).
    """

    async def _dependency(
        request: Request,
        idempotency_key: str | None = Header(
            default=None,
            alias="Idempotency-Key",
            description="Unique UUID per logical operation (client-generated). "
                        "Same key + same body = cached response. "
                        "Same key + different body = 422.",
        ),
        redis: Redis = Depends(get_redis),
    ) -> IdempotencyContext:
        if not idempotency_key:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Header 'Idempotency-Key' is required for this endpoint.",
            )

        # Read raw body bytes for hashing. FastAPI caches the body internally,
        # so Pydantic can still parse it downstream without re-reading.
        body_bytes = await request.body()
        body_hash = hash_request_body(body_bytes)

        # Look up any previously-cached response for this key.
        cached = await get_cached_response(redis, endpoint_name, idempotency_key)

        if cached is not None:
            # Key seen before. Validate body hasn't changed (replay protection).
            if cached["body_hash"] != body_hash:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Idempotency-Key reused with a different request body. "
                        "Use a new key for distinct operations."
                    ),
                )
            # Same key, same body → endpoint will return cached response.

        return IdempotencyContext(
            idempotency_key=idempotency_key,
            body_hash=body_hash,
            cached_response=cached,
            redis=redis,
            endpoint_name=endpoint_name,
        )

    return _dependency
