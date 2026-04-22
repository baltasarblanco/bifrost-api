"""
AI Assistant endpoint with defense-in-depth for external service calls.

Three layers of protection around the Gemini API call, composed from
outside-in:

1. Circuit breaker (systemic protection): if Gemini is trending failures,
   reject requests immediately (~1ms) without hitting the network.
2. Retry with exponential backoff (transient fault tolerance): transient
   errors (timeouts, 503s) get 3 retries with 1s → 2s → 4s waits.
3. Timeout (worker protection): each individual call to Gemini is capped
   at 5 seconds via asyncio.wait_for, preventing worker pool starvation.

When the breaker is OPEN, returns HTTP 503 with a graceful message
instead of a cryptic 500, allowing the client to degrade elegantly
(fall back to manual form, show "AI temporarily unavailable", etc).
"""
import asyncio
from app.core.config import get_settings

# Read at module load to validate config early. If GOOGLE_API_KEY is missing,
# the app fails to start (fail-fast) instead of accepting requests that would
# all return 500s.
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from starlette.concurrency import run_in_threadpool
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.circuit_breaker import (
    RedisCircuitBreaker,
)
from app.core.redis_client import get_redis

settings = get_settings()

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


# =============================================================================
# Schemas
# =============================================================================
class ReservationIntent(BaseModel):
    armor_modelo: str = Field(
        description=(
            "El modelo exacto de la armadura mencionada "
            "(ej: Mark IV, Stealth, Asalto). Si no se menciona, "
            "devuelve 'Desconocido'."
        )
    )
    fecha_inicio: datetime = Field(
        description="La fecha y hora exacta de inicio de la reserva en formato ISO 8601."
    )
    fecha_fin: datetime = Field(
        description=(
            "La fecha y hora exacta de finalización de la reserva en formato ISO 8601. "
            "Si el usuario no especifica, asume que dura 24 horas."
        )
    )
    accion: Literal[
        "crear_reserva", "cancelar_reserva", "consultar_disponibilidad"
    ] = Field(description="La intención del usuario.")


class UserPrompt(BaseModel):
    text: str


# =============================================================================
# Configuration
# =============================================================================
# Timeout per individual Gemini call. 5s is aggressive but correct:
# Gemini typically responds in 200-800ms. Calls exceeding 5s indicate
# real trouble and shouldn't hold our workers hostage.
GEMINI_TIMEOUT_SECONDS = 5.0

# Retries are for TRANSIENT failures (network blip, brief 503).
# 3 attempts with exponential backoff: 1s → 2s → 4s between tries.
# Total worst case: 5s × 3 + 1 + 2 = 18s before giving up.
GEMINI_MAX_ATTEMPTS = 3

# Circuit breaker: trips after 5 consecutive failures, opens for 60s.
# These values are tuned for Gemini's usual error profile and can be
# adjusted via observability once we have production metrics.
GEMINI_FAILURE_THRESHOLD = 5
GEMINI_COOLDOWN_SECONDS = 60


# =============================================================================
# Core Gemini call — isolated so tenacity retry wraps cleanly
# =============================================================================
@retry(
    # Retry ONLY on transient errors: timeouts and generic Exception from
    # the Gemini SDK. We explicitly do NOT retry on CircuitBreakerOpenError
    # because that signals a systemic failure, not a transient one.
    retry=retry_if_exception_type((asyncio.TimeoutError, Exception)),
    stop=stop_after_attempt(GEMINI_MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
async def _call_gemini_with_timeout(prompt_text: str, ahora_iso: str) -> ReservationIntent:
    """
    Single Gemini invocation wrapped in a hard timeout.

    Isolated into its own function so @retry applies only to this call,
    not to the circuit breaker logic (which we want to evaluate fresh
    on every retry attempt).
    """
    llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0,
    )
    structured_llm = llm.with_structured_output(ReservationIntent)

    system_template = """
    Eres el sistema de procesamiento logístico del Hangar Bifrost.
    Tu trabajo es extraer parámetros estrictos para la base de datos PostgreSQL
    a partir del mensaje del usuario.

    INFORMACIÓN DEL SISTEMA:
    - Fecha y hora actual del servidor: {fecha_actual}

    REGLAS ESTRICTAS:
    1. Calcula las fechas relativas usando la fecha actual del servidor.
    2. Las fechas deben ser ISO 8601 con zona horaria UTC.
    3. Si la armadura es "sigilosa", el modelo es "Stealth".
       Si es "asalto pesado", el modelo es "Hulkbuster".
    """

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("user", "{user_text}"),
    ])
    chain = prompt_template | structured_llm

    # chain.invoke is sync/blocking. Offload to thread pool so it doesn't
    # block the async event loop, then apply a hard timeout via wait_for.
    return await asyncio.wait_for(
        run_in_threadpool(
            chain.invoke,
            {"user_text": prompt_text, "fecha_actual": ahora_iso},
        ),
        timeout=GEMINI_TIMEOUT_SECONDS,
    )


# =============================================================================
# Endpoint — orchestrates circuit breaker + retry + timeout
# =============================================================================
@router.post("/analyze")
async def analyze_reservation_request(
    prompt: UserPrompt,
    redis: Redis = Depends(get_redis),
):
    """
    Extracts structured reservation intent from natural language.

    Protected by defense-in-depth:
    - Circuit breaker (opens after 5 consecutive Gemini failures).
    - Retry with exponential backoff (3 attempts).
    - Per-call timeout of 5 seconds.

    Error semantics:
    - 503: circuit is OPEN (Gemini deemed unhealthy); try again in ~1min.
    - 504: Gemini was reachable but exceeded timeout on all retries.
    - 500: unexpected error (logged and returned generic).
    """
    breaker = RedisCircuitBreaker(
        redis=redis,
        service_name="gemini",
        failure_threshold=GEMINI_FAILURE_THRESHOLD,
        cooldown_seconds=GEMINI_COOLDOWN_SECONDS,
    )

    # LAYER 1: Circuit breaker check. If OPEN, fail fast with 503.
    if not await breaker.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El servicio de IA está temporalmente no disponible. "
                "Por favor, reintente en unos instantes."
            ),
        )

    ahora_iso = datetime.now(timezone.utc).isoformat()

    try:
        # LAYERS 2 + 3: retry with backoff (outer) + timeout (inner).
        resultado = await _call_gemini_with_timeout(prompt.text, ahora_iso)

        # Success: reset the failure counter on the breaker.
        await breaker.record_success()
        return {"status": "success", "extracted_data": resultado}

    except asyncio.TimeoutError:
        # All retries exhausted on timeout. Record failure toward the
        # breaker's threshold and return 504 Gateway Timeout.
        await breaker.record_failure()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                "El servicio de IA no respondió dentro del tiempo permitido. "
                "Reintente más tarde."
            ),
        )

    except Exception as e:
        # Any other failure (SDK error, JSON parse error, etc): record
        # as failure and surface a generic 500. In production this should
        # be structured-logged for observability (future fase: OpenTelemetry).
        await breaker.record_failure()
        raise HTTPException(
            status_code=500,
            detail=f"Error en el procesamiento de IA: {str(e)}",
        )