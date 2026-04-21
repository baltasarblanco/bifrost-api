"""
Blacklist de JWTs revocados, almacenada en Redis.

Diseño clave:
- Keys: "blacklist:jti:{jti}" → valor "1" (solo importa la existencia)
- TTL automático: la entry expira cuando el token habría expirado.
  Redis limpia solo, sin tareas de mantenimiento.
- Lookup O(1): redis.exists() es constante, no degrada con el tamaño.

Esto convierte JWT (stateless) en JWT + revocation (híbrido), el patrón
estándar que usan Auth0, Stripe, y todo SaaS serio con autenticación.
"""
from datetime import datetime, timezone
from redis.asyncio import Redis

# Prefijo estándar para keys de blacklist en Redis.
# Facilita debugging con `KEYS blacklist:jti:*` y evita colisiones
# con otras keys del sistema (rate limiting, cache, etc.).
BLACKLIST_KEY_PREFIX = "blacklist:jti:"


async def revoke_token(redis: Redis, jti: str, exp_timestamp: int) -> None:
    """
    Agrega un JTI a la blacklist con TTL igual a lo que le quedaba al token.
    
    Si el token expiraba en 20 minutos, la entry en Redis vive 20 minutos.
    Después se borra sola (ahorro de memoria, no hay cleanup job que mantener).

    Args:
        redis: cliente Redis async.
        jti: JWT ID único del token a revocar.
        exp_timestamp: timestamp Unix de expiración del token (claim "exp").
    """
    now = int(datetime.now(timezone.utc).timestamp())
    ttl_seconds = max(exp_timestamp - now, 1)  # Mínimo 1s para evitar TTL=0
    
    key = f"{BLACKLIST_KEY_PREFIX}{jti}"
    await redis.setex(key, ttl_seconds, "1")


async def is_token_revoked(redis: Redis, jti: str) -> bool:
    """
    Chequea si un JTI está en la blacklist.
    
    Se llama en CADA request autenticado, así que debe ser O(1).
    redis.exists() cumple esto: ~1ms de lookup, imperceptible.
    """
    key = f"{BLACKLIST_KEY_PREFIX}{jti}"
    result = await redis.exists(key)
    return result > 0