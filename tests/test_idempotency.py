"""
Tests del KPI Semana 10 — Idempotency Key en POST /reservas/.

Criterio de aceptación:
> Un mismo Idempotency-Key + mismo body devuelve la misma respuesta
> sin crear duplicados. Un mismo key + body distinto devuelve 422.
> Sin header → 400.

Protege contra:
1. Reintentos de red (cliente retry en timeout).
2. Replay attacks (atacante reusa key con payload manipulado).
3. Double-click en frontends.
"""
import uuid
from fastapi.testclient import TestClient
from fastapi import status

TEST_USER_SECRET = "dummy_test_value_not_a_real_password"  # nosec


def _login(client: TestClient, email: str = "idem@example.com") -> str:
    """Helper: crea usuario si no existe y devuelve token."""
    client.post("/usuarios/", json={"email": email, "password": TEST_USER_SECRET})
    response = client.post(
        "/login/access-token",
        data={"username": email, "password": TEST_USER_SECRET},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()["access_token"]


def _seed_armadura(client: TestClient, modelo: str) -> None:
    """Helper: asegura que existe una armadura para el test."""
    # Usamos SQL directo vía el ORM que la app ya tiene configurado en tests.
    # Para este test, asumimos que _register_armadura funciona o se saltea.
    # Si el endpoint POST /armaduras/ está roto (enum vs int), este seed
    # tiene que hacerse fuera. Por ahora lo dejamos como placeholder.
    pass


def _create_armadura_via_sql(client: TestClient, modelo: str):
    """
    Inserta una armadura usando la MISMA sesión de DB que el TestClient.

    No podemos usar SessionLocal directo porque en tests SQLite in-memory cada
    conexión es una DB aislada. El fixture `client` de conftest override
    get_db con una sesión sobre el StaticPool compartido — ese es el que tenemos
    que usar acá también.
    """
    from app.main import app
    from app.database import get_db
    from app import models

    # Extraemos el override de get_db que instaló el conftest.
    # Es la misma función que inyecta la sesión en el endpoint.
    override = app.dependency_overrides[get_db]
    db_gen = override()
    db = next(db_gen)

    try:
        existing = db.query(models.ArmaduraDB).filter_by(modelo=modelo).first()
        if existing:
            return
        nueva = models.ArmaduraDB(
            modelo=modelo,
            activa=True,
        )
        db.add(nueva)
        db.commit()
    finally:
        # Cerramos el generador para liberar la sesión correctamente.
        try:
            next(db_gen)
        except StopIteration:
            pass

def test_post_reserva_without_header_returns_400(client: TestClient):
    """Sin Idempotency-Key, el endpoint rechaza con 400."""
    token = _login(client, "idem1@example.com")
    _create_armadura_via_sql(client, "Mark 85")

    response = client.post(
        "/reservas/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "armadura_modelo": "Mark 85",
            "fecha_inicio": "2027-01-01T10:00:00Z",
            "fecha_fin": "2027-01-01T12:00:00Z",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Idempotency-Key" in response.json()["detail"]


def test_same_key_same_body_returns_cached_response(client: TestClient):
    """Dos POSTs con mismo key + mismo body devuelven respuesta idéntica."""
    token = _login(client, "idem2@example.com")
    _create_armadura_via_sql(client, "Mark 85")
    idem_key = str(uuid.uuid4())

    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idem_key,
    }
    body = {
        "armadura_modelo": "Mark 85",
        "fecha_inicio": "2027-02-01T10:00:00Z",
        "fecha_fin": "2027-02-01T12:00:00Z",
    }

    # Primer request: crea la reserva.
    response_1 = client.post("/reservas/", headers=headers, json=body)
    assert response_1.status_code == status.HTTP_201_CREATED
    reserva_1 = response_1.json()

    # Segundo request: debe devolver la MISMA respuesta, cached.
    response_2 = client.post("/reservas/", headers=headers, json=body)
    assert response_2.status_code == status.HTTP_201_CREATED
    reserva_2 = response_2.json()

    # Mismo id de reserva → confirma que no se creó una segunda fila.
    assert reserva_1["id"] == reserva_2["id"]
    assert reserva_1 == reserva_2


def test_same_key_different_body_returns_422(client: TestClient):
    """Mismo key con body distinto es rechazado con 422 (replay protection)."""
    token = _login(client, "idem3@example.com")
    _create_armadura_via_sql(client, "Mark 85")
    _create_armadura_via_sql(client, "Hulkbuster")
    idem_key = str(uuid.uuid4())

    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idem_key,
    }

    # Primer request: Mark 85.
    response_1 = client.post(
        "/reservas/",
        headers=headers,
        json={
            "armadura_modelo": "Mark 85",
            "fecha_inicio": "2027-03-01T10:00:00Z",
            "fecha_fin": "2027-03-01T12:00:00Z",
        },
    )
    assert response_1.status_code == status.HTTP_201_CREATED

    # Segundo request: MISMO key, body distinto → 422.
    response_2 = client.post(
        "/reservas/",
        headers=headers,
        json={
            "armadura_modelo": "Hulkbuster",
            "fecha_inicio": "2027-03-01T10:00:00Z",
            "fecha_fin": "2027-03-01T12:00:00Z",
        },
    )
    assert response_2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "different request body" in response_2.json()["detail"].lower()


def test_different_keys_create_different_reservas(client: TestClient):
    """Keys distintos crean reservas distintas (no idempotencia cruzada)."""
    token = _login(client, "idem4@example.com")
    _create_armadura_via_sql(client, "Mark 85")

    headers_base = {"Authorization": f"Bearer {token}"}

    # Primera reserva con key_1.
    response_1 = client.post(
        "/reservas/",
        headers={**headers_base, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "armadura_modelo": "Mark 85",
            "fecha_inicio": "2027-04-01T10:00:00Z",
            "fecha_fin": "2027-04-01T12:00:00Z",
        },
    )
    assert response_1.status_code == status.HTTP_201_CREATED

    # Segunda reserva con key_2 distinto, rango de fechas distinto.
    response_2 = client.post(
        "/reservas/",
        headers={**headers_base, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "armadura_modelo": "Mark 85",
            "fecha_inicio": "2027-04-02T10:00:00Z",
            "fecha_fin": "2027-04-02T12:00:00Z",
        },
    )
    assert response_2.status_code == status.HTTP_201_CREATED

    # IDs distintos → reservas distintas.
    assert response_1.json()["id"] != response_2.json()["id"]