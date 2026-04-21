"""
Cliente Redis asíncrono con pool de conexiones.

En tests (TESTING=1), usa fakeredis — implementación 100% en memoria
de Redis. El código de producción no cambia: mismas llamadas, mismo
comportamiento. Test Double tipo "Fake" (categoría oficial xUnit).
"""
import os
from redis.asyncio import Redis, ConnectionPool

from app.core.config import get_settings


class RedisClient:
    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def connect(self) -> None:
        """Abre el pool de conexiones. Llamado en lifespan startup."""
        if os.getenv("TESTING") == "1":
            # En tests: usamos fakeredis en memoria, sin TCP, sin servidor.
            # Import local para no forzar la dependencia en producción.
            from fakeredis import aioredis as fake_aioredis
            self._client = fake_aioredis.FakeRedis(decode_responses=True)
            await self._client.ping()  # valida que el fake responde
            return
        
        # En producción: Redis real con pool.
        settings = get_settings()
        self._pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_MAX_CONNECTIONS,
            decode_responses=True,
        )
        self._client = Redis(connection_pool=self._pool)
        await self._client.ping()

    async def disconnect(self) -> None:
        """Cierra el pool prolijamente. Llamado en lifespan shutdown."""
        if self._client is not None:
            await self._client.aclose()
        if self._pool is not None:
            await self._pool.aclose()

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError(
                "Redis client is not initialized. "
                "Did you forget to call connect() in the lifespan?"
            )
        return self._client


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