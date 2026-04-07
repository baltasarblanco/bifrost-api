def test_telemetria_raiz(client): # <--- Ahora pedimos el 'client' como fixture
    """Prueba que el servidor responda correctamente en la ruta principal"""
    respuesta = client.get("/")
    
    assert respuesta.status_code == 200
    # Actualizamos el mensaje para que coincida con tu main.py actual:
    assert respuesta.json() == {
        "sistema": "Pop!_OS", 
        "estado": "En línea, Persistente y Seguro"
    }

def test_crear_armadura_datos_invalidos(client):
    """Prueba que Pydantic rechace correctamente datos mal formados (El escudo 422)"""
    datos_corruptos = {
        "modelo": "Mark X",
        "nivel_energia": "bateria_rota",
        "activa": True
    }
    
    respuesta = client.post("/armaduras/", json=datos_corruptos)
    assert respuesta.status_code == 422