"""
Tests del KPI Semana 7 — JWT Blacklist (Logout).

Criterio de aceptación:
> Logout → token usado da 401, aunque no haya expirado.
> Test de integración con Redis mockeado.

Usa fakeredis (configurado en redis_client) para que el lifespan
conecte a un Redis en memoria durante los tests.
"""
from fastapi.testclient import TestClient
from fastapi import status

# Valores dummy para tests — no son credenciales reales.
# Nombres explícitos para evitar falsos positivos de scanners de secretos.
TEST_USER_SECRET = "dummy_test_value_not_a_real_password"  # nosec

def _register_and_login(client: TestClient, email: str, secret: str = TEST_USER_SECRET) -> str:
    """Helper: registra un usuario (si no existe) y devuelve un token fresco."""
    client.post("/usuarios/", json={"email": email, "password": secret})
    response = client.post(
        "/login/access-token",
        data={"username": email, "password": secret},
    )
    assert response.status_code == status.HTTP_200_OK, (
        f"Login falló: {response.status_code} {response.text}"
    )
    return response.json()["access_token"]


def test_logout_revokes_token(client: TestClient):
    """Login → logout → reusar token → 401 con mensaje de revocación."""
    token = _register_and_login(client, "logout1@example.com", "supersecret")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. El token funciona antes del logout
    response = client.get("/ruta-privada", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    # 2. Logout exitoso
    response = client.post("/logout", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    # 3. El mismo token YA NO funciona
    response = client.get("/ruta-privada", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "revocado" in response.json()["detail"].lower()


def test_logout_is_idempotent(client: TestClient):
    """Llamar logout dos veces con el mismo token no debería fallar."""
    token = _register_and_login(client, "logout2@example.com", "supersecret")
    headers = {"Authorization": f"Bearer {token}"}

    response1 = client.post("/logout", headers=headers)
    assert response1.status_code == status.HTTP_200_OK

    response2 = client.post("/logout", headers=headers)
    assert response2.status_code == status.HTTP_200_OK


def test_new_token_after_logout_works(client: TestClient):
    """Revocar el token viejo no debe afectar nuevos tokens del mismo usuario."""
    email = "logout3@example.com"
    
    old_token = _register_and_login(client, email)

    # Revocamos el viejo
    client.post("/logout", headers={"Authorization": f"Bearer {old_token}"})

    # Login genera uno nuevo
    response = client.post(
        "/login/access-token",
        data={"username": email, "password": TEST_USER_SECRET},
    )
    new_token = response.json()["access_token"]
    assert new_token != old_token, "El nuevo token debería ser distinto al revocado"

    # El nuevo funciona
    response = client.get(
        "/ruta-privada",
        headers={"Authorization": f"Bearer {new_token}"},
    )
    assert response.status_code == status.HTTP_200_OK