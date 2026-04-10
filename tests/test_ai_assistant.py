from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)

def test_analyze_request_missing_data():
    """
    Prueba 1: El servidor debe rechazar peticiones mal formadas.
    Enviamos un JSON con la clave incorrecta. Pydantic debería bloquearlo.
    """
    response = client.post("/ai-assistant/analyze", json={"mensaje_equivocado": "Hola"})
    
    # 422 Unprocessable Entity es el código estándar cuando el JSON no cumple el esquema
    assert response.status_code == 422 

def test_analyze_request_success():
    """
    Prueba 2: Integración exitosa.
    Verificamos que el endpoint se comunique con Gemini y devuelva la estructura correcta.
    """
    payload = {"text": "Necesito preparar la armadura de asalto pesado para el sábado a la mañana."}
    response = client.post("/ai-assistant/analyze", json=payload)
    
    assert response.status_code == 200
    
    # Extraemos la respuesta en formato diccionario
    data = response.json()
    
    # Validamos que el JSON devuelto tenga las llaves exactas que exige nuestra base de datos
    assert data["status"] == "success"
    assert "extracted_data" in data
    assert "armor_type" in data["extracted_data"]
    assert "date_requested" in data["extracted_data"]
    assert "action" in data["extracted_data"]