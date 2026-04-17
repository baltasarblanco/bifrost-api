"""
Cliente Redis asíncrono con pool de conexiones.

Diseñado para ser usado en toda la aplicación:
- Rate limiting (SlowAPI)
- JWT blacklist (logout)
- Idempotency keys
- Cache general
"""
from redis.asyncio import Redis, ConnectionPool

from app.core.config import get_settings


class RedisClient:
    """
    Wrapper singleton que gestiona un pool async de Redis.
    
    Se inicializa una vez al arrancar la app (lifespan startup)
    y se cierra limpiamente al apagarla (lifespan shutdown).
    """

    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def connect(self) -> None:
        """Abre el pool de conexiones. Llamado en lifespan startup."""
        settings = get_settings()
        self._pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_MAX_CONNECTIONS,
            decode_responses=True,  # Retorna str en vez de bytes
        )
        self._client = Redis(connection_pool=self._pool)
        # Validación fail-fast: si Redis no responde, la app no arranca
        await self._client.ping()

    async def disconnect(self) -> None:
        """Cierra el pool prolijamente. Llamado en lifespan shutdown."""
        if self._client is not None:
            await self._client.aclose()
        if self._pool is not None:
            await self._pool.aclose()

    @property
    def client(self) -> Redis:
        """Accede al cliente Redis. Falla explícito si no está conectado."""
        if self._client is None:
            raise RuntimeError(
                "Redis client is not initialized. "
                "Did you forget to call connect() in the lifespan?"
            )
        return self._client


# Instancia global única (patrón singleton controlado)
redis_client = RedisClient()


async def get_redis() -> Redis:
    """
    Dependency de FastAPI para inyectar el cliente Redis en endpoints.
    
    Uso:
        @app.get("/...")
        async def my_endpoint(redis: Redis = Depends(get_redis)):
            await redis.set("key", "value")
    """
    return redis_client.client