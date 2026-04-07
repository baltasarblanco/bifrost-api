def test_flujo_completo_armadura(client):
    # 1. CREAR (POST)
    nueva_armadura = {"modelo": "Mark 85", "nivel_energia": 100, "activa": True}
    res_post = client.post("/armaduras/", json=nueva_armadura)
    assert res_post.status_code == 200
    
    # 2. LEER (GET ALL)
    res_get_all = client.get("/armaduras/")
    assert res_get_all.status_code == 200
    assert len(res_get_all.json()["inventario"]) >= 1

    # 3. LEER UNA (GET ONE)
    res_get_one = client.get("/armaduras/Mark 85")
    assert res_get_one.status_code == 200
    assert res_get_one.json()["modelo"] == "Mark 85"

    # 4. ACTUALIZAR (PUT)
    actualizacion = {"modelo": "Mark 85", "nivel_energia": 80, "activa": False}
    res_put = client.put("/armaduras/Mark 85", json=actualizacion)
    assert res_put.status_code == 200
    assert res_put.json()["mensaje"] == "Sistemas de Mark 85 actualizados."

    # 5. BORRAR (DELETE)
    res_del = client.delete("/armaduras/Mark 85")
    assert res_del.status_code == 200