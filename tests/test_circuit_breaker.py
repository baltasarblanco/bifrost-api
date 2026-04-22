"""
Tests for Fase F — Circuit Breaker protection of Gemini AI calls.

Validates the three defense layers applied to POST /ai-assistant/analyze:
1. Retry with exponential backoff on transient failures.
2. Timeout guardrails on individual calls.
3. Circuit breaker trip after consecutive failures.

All tests mock the Gemini call at the seam _call_gemini_with_timeout,
so the breaker and retry logic run with real code while the external
dependency is replaced. No network, no API credits consumed.
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient


# Module path to patch — our "seam" into Gemini.
# All tests replace this with a controllable mock.
GEMINI_CALL_PATH = "routers.ai_assistant._call_gemini_with_timeout"


def _make_valid_intent():
    """Builds a realistic Gemini response for success paths."""
    from routers.ai_assistant import ReservationIntent
    from datetime import datetime, timezone

    return ReservationIntent(
        armor_modelo="Mark 85",
        fecha_inicio=datetime(2027, 1, 1, 10, 0, tzinfo=timezone.utc),
        fecha_fin=datetime(2027, 1, 1, 12, 0, tzinfo=timezone.utc),
        accion="crear_reserva",
    )


@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    """
    Nuclear cleanup between tests: empty ALL fakeredis data.
    
    Avoids event-loop conflicts by going straight to fakeredis' sync
    backing store. Also ensures complete isolation: no rate limiter,
    idempotency, or blacklist state leaks between tests.
    """
    from app.core.redis_client import redis_client

    def _flush_all():
        if redis_client._client is None:
            return
        server = getattr(redis_client._client, "_server", None)
        if server is None:
            return
        # Reset every database to empty. Nuclear but bulletproof.
        for db in server.dbs.values():
            db.clear()

    _flush_all()
    yield
    _flush_all()

# =============================================================================
# Test 1: Happy path with mock — sanity check
# =============================================================================
def test_analyze_returns_200_when_gemini_succeeds(client: TestClient):
    """With a mocked successful Gemini call, endpoint returns 200 + structured data."""
    valid_intent = _make_valid_intent()

    with patch(GEMINI_CALL_PATH, new=AsyncMock(return_value=valid_intent)):
        response = client.post(
            "/ai-assistant/analyze",
            json={"text": "reservar Mark 85 el primero de enero"},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "success"
    assert response.json()["extracted_data"]["armor_modelo"] == "Mark 85"


# =============================================================================
# Test 2: Timeout → 504 after all retries exhausted
# =============================================================================
def test_analyze_returns_504_when_gemini_times_out(client: TestClient):
    """
    If every call to Gemini times out, all retries fail and the endpoint
    returns 504 Gateway Timeout (not 500). Semantic HTTP matters.
    """
    with patch(GEMINI_CALL_PATH, new=AsyncMock(side_effect=asyncio.TimeoutError())):
        response = client.post(
            "/ai-assistant/analyze",
            json={"text": "reservar algo"},
        )

    assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert "tiempo" in response.json()["detail"].lower()


# =============================================================================
# Test 3: Circuit breaker opens after 5 consecutive failures
# =============================================================================
def test_circuit_breaker_opens_after_threshold_failures(client: TestClient):
    """
    After 5 consecutive failures, the 6th request must return 503 WITHOUT
    even invoking Gemini (fail-fast). Verifies the breaker transitions
    to OPEN and short-circuits further calls.
    """
    failing_mock = AsyncMock(side_effect=Exception("Gemini is having a bad day"))

    with patch(GEMINI_CALL_PATH, new=failing_mock):
        # Trigger 5 failures → breaker should open.
        for _ in range(5):
            client.post("/ai-assistant/analyze", json={"text": "test"})

        # Reset mock call count to prove the next call doesn't touch Gemini.
        call_count_before = failing_mock.call_count

        # 6th call: breaker is OPEN, we expect fail-fast with 503.
        response = client.post(
            "/ai-assistant/analyze",
            json={"text": "this should fail fast"},
        )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "no disponible" in response.json()["detail"].lower()

    # Critical assertion: the mock was NOT invoked on the 6th call.
    # If it was, it means the breaker didn't short-circuit.
    assert failing_mock.call_count == call_count_before, (
        "Circuit breaker should have prevented the 6th call to Gemini"
    )


# =============================================================================
# Test 4: Success resets the failure counter
# =============================================================================
def test_successful_call_resets_failure_counter(client: TestClient):
    """
    Intermittent failures should NOT accumulate forever toward opening the
    breaker. A single success resets the counter, so 4 failures + 1 success
    + 4 more failures should NOT open the breaker (needs 5 CONSECUTIVE).
    """
    valid_intent = _make_valid_intent()

    # First: 4 failures (below threshold).
    with patch(GEMINI_CALL_PATH, new=AsyncMock(side_effect=Exception("temporary glitch"))):
        for _ in range(4):
            client.post("/ai-assistant/analyze", json={"text": "test"})

    # Then: 1 success → should reset counter.
    with patch(GEMINI_CALL_PATH, new=AsyncMock(return_value=valid_intent)):
        response = client.post("/ai-assistant/analyze", json={"text": "test"})
        assert response.status_code == status.HTTP_200_OK

    # Now: 4 more failures. Breaker should STILL be closed (counter was reset).
    with patch(GEMINI_CALL_PATH, new=AsyncMock(side_effect=Exception("temporary glitch"))):
        for _ in range(4):
            client.post("/ai-assistant/analyze", json={"text": "test"})

        # 5th failure would open it, but we stop at 4. Confirm breaker
        # is still closed by making another call that should NOT fail-fast.
        response = client.post("/ai-assistant/analyze", json={"text": "test"})

    # Breaker still closed → endpoint tried and failed through Gemini,
    # so we should see 500 (from Exception), NOT 503 (from open breaker).
    # In either case the request wasn't short-circuited at the breaker layer.
    assert response.status_code != status.HTTP_503_SERVICE_UNAVAILABLE, (
        "Counter should have been reset by the success; breaker should not be open"
    )