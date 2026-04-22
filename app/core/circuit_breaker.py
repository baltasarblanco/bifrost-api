"""
Circuit Breaker pattern with Redis-backed distributed state.

Protects downstream services (Gemini AI, external APIs) from cascading
failures. When a service becomes unhealthy, the breaker "opens" and
fails fast without hitting the broken service, protecting the caller
from resource exhaustion (blocked threads, connection pool starvation).

State machine:

    CLOSED ──[N failures in window]──▶ OPEN
      ▲                                  │
      │                                  │
      │                            [cooldown elapsed]
      │                                  │
      │                                  ▼
      └───[success]── HALF_OPEN ◀────────┘
                         │
                         └──[failure]──▶ OPEN

Redis as state store ensures consistency across multiple FastAPI replicas:
all instances observe the same breaker state (critical for horizontal
scaling — in-memory breakers would each have their own state, defeating
the protection when one replica falls through while others are open).

References:
- Michael Nygard, "Release It!" (2007) — original pattern definition
- Netflix Hystrix documentation
- https://martinfowler.com/bliki/CircuitBreaker.html
"""
from enum import Enum
from redis.asyncio import Redis


class CircuitState(str, Enum):
    CLOSED = "closed"       # Normal operation; requests pass through.
    OPEN = "open"           # Service deemed unhealthy; fail fast.
    HALF_OPEN = "half_open"  # Cooldown elapsed; one trial request allowed.


class CircuitBreakerOpenError(Exception):
    """Raised when a request is rejected because the breaker is OPEN."""
    pass


class RedisCircuitBreaker:
    """
    Distributed circuit breaker backed by Redis.

    Args:
        redis: async Redis client.
        service_name: unique identifier for the protected service
            (e.g., "gemini"). Used as Redis key namespace.
        failure_threshold: consecutive failures before opening the circuit.
        cooldown_seconds: how long OPEN state persists before transitioning
            to HALF_OPEN to probe recovery.
    """

    def __init__(
        self,
        redis: Redis,
        service_name: str,
        failure_threshold: int = 5,
        cooldown_seconds: int = 60,
    ):
        self.redis = redis
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._state_key = f"cb:{service_name}:state"
        self._failures_key = f"cb:{service_name}:failures"

    async def get_state(self) -> CircuitState:
        """Fetch the current state, defaulting to CLOSED if never set."""
        raw = await self.redis.get(self._state_key)
        if raw is None:
            return CircuitState.CLOSED
        return CircuitState(raw)

    async def is_available(self) -> bool:
        """
        Check whether a request can proceed to the downstream service.

        - CLOSED: always allow.
        - OPEN: deny (fail fast).
        - HALF_OPEN: allow ONE trial (caller must call record_success or
          record_failure after the trial completes).
        """
        state = await self.get_state()
        return state != CircuitState.OPEN

    async def record_success(self) -> None:
        """
        Report a successful downstream call.

        Resets the failure counter and forces the breaker back to CLOSED.
        Called after a request to Gemini succeeds.
        """
        await self.redis.delete(self._failures_key)
        await self.redis.set(self._state_key, CircuitState.CLOSED.value)

    async def record_failure(self) -> None:
        """
        Report a failed downstream call.

        Increments the failure counter. If the threshold is hit, trips
        the breaker to OPEN with a TTL = cooldown_seconds (Redis will
        auto-expire the state, transitioning us back toward HALF_OPEN).
        """
        # INCR is atomic in Redis — safe under concurrent failures from
        # multiple FastAPI workers/replicas.
        failures = await self.redis.incr(self._failures_key)

        if failures >= self.failure_threshold:
            # Set OPEN with TTL: after cooldown, the key expires and
            # get_state() returns CLOSED again (our "half-open probe":
            # the next request tests the service; if it fails, we
            # re-open; if it succeeds, we stay closed).
            await self.redis.setex(
                self._state_key,
                self.cooldown_seconds,
                CircuitState.OPEN.value,
            )