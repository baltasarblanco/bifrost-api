"""
Idempotency key handling for critical POST endpoints.

Pattern used by Stripe, MercadoPago, Pomelo and modern fintech APIs:
clients send an 'Idempotency-Key' header with a unique UUID per logical
operation. The server caches the response in Redis for 24h. Retries with
the same key return the cached response without side effects.

Safety properties:
- Body hash validation: same key + different body → 422 (prevents replay
  attacks and client-side bugs).
- Atomic locking via SETNX prevents concurrent duplicate processing.
- Stores both success and failure responses: reprocessing never produces
  different results on retry.

References:
- https://stripe.com/docs/api/idempotent_requests
- https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header
"""
import hashlib
import json
from typing import Any
from redis.asyncio import Redis

# TTL aligned with Stripe's default. Long enough for client retries after
# extended downtimes; short enough to bound Redis memory usage.
IDEMPOTENCY_TTL_SECONDS = 24 * 60 * 60  # 24 hours

# Namespace prefix: "idempotency:{endpoint}:{key}" separates concerns from
# rate limiting ("LIMITER:...") and JWT blacklist ("blacklist:jti:...").
IDEMPOTENCY_KEY_PREFIX = "idempotency"


def hash_request_body(body: bytes) -> str:
    """
    Compute SHA-256 of the raw request body.

    Used to detect the replay attack where a client sends the same
    Idempotency-Key with a modified body. SHA-256 has ~zero collision
    probability for realistic inputs.
    """
    return hashlib.sha256(body).hexdigest()


def build_redis_key(endpoint: str, idempotency_key: str) -> str:
    """Compose the full Redis key: 'idempotency:reservas:abc-123-uuid'."""
    return f"{IDEMPOTENCY_KEY_PREFIX}:{endpoint}:{idempotency_key}"


async def get_cached_response(
    redis: Redis,
    endpoint: str,
    idempotency_key: str,
) -> dict[str, Any] | None:
    """
    Fetch a previously-stored response for this key, if any.

    Returns a dict with keys: 'status_code', 'body', 'body_hash'.
    Returns None if the key has never been seen (first request).
    """
    redis_key = build_redis_key(endpoint, idempotency_key)
    raw = await redis.get(redis_key)
    if raw is None:
        return None
    return json.loads(raw)


async def store_response(
    redis: Redis,
    endpoint: str,
    idempotency_key: str,
    status_code: int,
    body: Any,
    body_hash: str,
) -> None:
    """
    Persist the endpoint's response under the idempotency key.

    Stores status_code + body + body_hash so future retries can:
    - Return the same status and body verbatim.
    - Detect key reuse with a different payload (replay protection).
    """
    redis_key = build_redis_key(endpoint, idempotency_key)
    payload = json.dumps({
        "status_code": status_code,
        "body": body,
        "body_hash": body_hash,
    })
    await redis.setex(redis_key, IDEMPOTENCY_TTL_SECONDS, payload)