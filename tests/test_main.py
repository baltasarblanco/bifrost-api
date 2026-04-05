from fastapi.testclient import TestClient
from app.main import app

# Inicializamos a J.A.R.V.I.S. en modo simulación
cliente_prueba = TestClient(app)

def test_telemetria_raiz():
    """Prueba que el servidor responda correctamente en la ruta principal"""
    # 1. Ejecutar la acción (Disparar un GET a "/")
    respuesta = cliente_prueba.get("/")
    
    # 2. Afirmar (Assert) que el código HTTP sea 200 (Éxito)
    assert respuesta.status_code == 200
    
    # 3. Afirmar que el contenido del JSON sea exactamente el esperado
    assert respuesta.json() == {"sistema": "Pop!_OS", "estado": "En línea y Persistente"}

def test_crear_armadura_datos_invalidos():
    """Prueba que Pydantic rechace correctamente datos mal formados (El escudo 422)"""
    # Mandamos un nivel de energía como texto ("bateria_rota") en vez de un número
    datos_corruptos = {
        "modelo": "Mark X",
        "nivel_energia": "bateria_rota",
        "activa": True
    }
    
    respuesta = cliente_prueba.post("/armaduras/", json=datos_corruptos)
    
    # Afirmar que el servidor rechazó el ataque
    assert respuesta.status_code == 422