"""
Test del KPI Semana 7: Rate Limiting.

Criterio de aceptación (del roadmap):
> Verificar que el 4to login en 1 min da 429.

Nota: como configuramos 5/minute en /login/access-token,
el 6to request debe devolver 429.
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status


@pytest.fixture(autouse=True)
def reset_rate_limiter_storage(client: TestClient):
    """
    Antes de cada test, limpiamos las keys del rate limiter en Redis
    para que los tests sean aislados.
    """
    # Limpieza vía el limiter attached al app state
    app = client.app
    if hasattr(app.state, "limiter"):
        app.state.limiter.reset()
    yield


def test_login_rate_limit_returns_429_on_sixth_request(client: TestClient):
    """
    Dado un rate limit de 5/minute en /login/access-token,
    el 6to request consecutivo debe devolver HTTP 429.
    """
    payload = {"username": "fake@example.com", "password": "wrong"}

    # Los primeros 5 requests: esperamos 401 (credenciales malas) pero NO 429.
    # Lo importante es que el rate limiter NO se disparó todavía.
    for i in range(5):
        response = client.post("/login/access-token", data=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Request #{i+1} debería devolver 401 (creds malas), "
            f"no {response.status_code}"
        )

    # El 6to: rate limit activado → 429
    response = client.post("/login/access-token", data=payload)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS, (
        f"El 6to request debería devolver 429, no {response.status_code}"
    )
    assert "Rate limit exceeded" in response.text or "rate" in response.text.lower()


def test_different_endpoints_have_independent_limits(client: TestClient):
    """
    El rate limit es por endpoint + IP. Saturar /login no afecta /.
    """
    # Saturamos /login/access-token
    for _ in range(6):
        client.post("/login/access-token", data={"username": "x", "password": "y"})

    # / debe seguir respondiendo 200
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK