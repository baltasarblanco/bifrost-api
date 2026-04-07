def test_registrar_y_loguear_usuario(client):
    # --- ARRANGE (Organizar) ---
    usuario_data = {"email": "test@stark.com", "password": "password123"}

    # --- ACT (Actuar) - Registro ---
    response_reg = client.post("/usuarios/", json=usuario_data)

    # --- ASSERT (Afirmar) ---
    assert response_reg.status_code == 201
    assert response_reg.json()["email"] == usuario_data["email"]

    # --- ACT (Actuar) - Login ---
    # Nota: OAuth2 usa form-data, no JSON
    login_data = {
        "username": usuario_data["email"],
        "password": usuario_data["password"],
    }
    response_login = client.post("/login/access-token", data=login_data)

    # --- ASSERT ---
    assert response_login.status_code == 200
    assert "access_token" in response_login.json()
    assert response_login.json()["token_type"] == "bearer"


def test_acceso_ruta_privada(client):
    # 1. Creamos y logueamos un usuario para obtener el token
    usuario_data = {"email": "vip@stark.com", "password": "password123"}
    client.post("/usuarios/", json=usuario_data)

    login_response = client.post(
        "/login/access-token",
        data={"username": usuario_data["email"], "password": usuario_data["password"]},
    )
    token = login_response.json()["access_token"]

    # 2. Intentamos entrar a la ruta privada USANDO el token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/ruta-privada", headers=headers)

    # 3. Verificamos éxito
    assert response.status_code == 200
    assert response.json()["usuario_logueado"] == usuario_data["email"]


def test_acceso_denegado_sin_token(client):
    # Intentamos entrar sin el header de Authorization
    response = client.get("/ruta-privada")

    # Debería rebotarnos con 401
    assert response.status_code == 401
