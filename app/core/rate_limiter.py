"""
Rate Limiting distribuido con SlowAPI + Redis.
En tests, usa storage en memoria para no depender de Redis real.
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()

# En tests no tenemos Redis accesible → memoria local
storage_uri = "memory://" if os.getenv("TESTING") == "1" else settings.REDIS_URL

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=["100/minute"],
    strategy="fixed-window",
)