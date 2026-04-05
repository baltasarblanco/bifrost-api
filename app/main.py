from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Project Bifrost", version="Mark 3.0")

class Armadura(BaseModel):
    modelo: str
    nivel_energia: int
    activa: bool = False

# 1. NUESTRA BASE DE DATOS FALSificada (En memoria RAM)
banco_de_armaduras = {}

@app.get("/")
def root():
    return {"sistema": "Pop!_OS", "estado": "En línea"}

# 2. CREATE (Guardar en el diccionario)
@app.post("/armaduras/")
def registrar_armadura(armadura: Armadura):
    # Guardamos el objeto entero usando el nombre del modelo como llave (key)
    banco_de_armaduras[armadura.modelo] = armadura
    return {"mensaje": f"{armadura.modelo} almacenada en memoria central."}

# 3. READ ALL (Listar todo lo que tenemos)
@app.get("/armaduras/")
def listar_armaduras():
    return {"inventario": banco_de_armaduras}

# 4. READ ONE (Buscar una armadura específica por la URL)
@app.get("/armaduras/{nombre_modelo}")
def obtener_armadura(nombre_modelo: str):
    # Verificamos si el modelo existe en nuestro banco
    if nombre_modelo not in banco_de_armaduras:
        # Si no existe, lanzamos un error 404 oficial
        raise HTTPException(status_code=404, detail="Armadura no encontrada en los registros.")
    
    # Si existe, la devolvemos
    return banco_de_armaduras[nombre_modelo]


# 5. UPDATE (Actualizar una armadura existente)
@app.put("/armaduras/{nombre_modelo}")
def actualizar_armadura(nombre_modelo: str, armadura_actualizada: Armadura):
    # Primero verificamos si existe
    if nombre_modelo not in banco_de_armaduras:
        raise HTTPException(status_code=404, detail="Armadura no encontrada para actualizar.")
    
    # Si existe, la pisamos con los datos nuevos
    banco_de_armaduras[nombre_modelo] = armadura_actualizada
    return {"mensaje": f"Sistemas de {nombre_modelo} actualizados correctamente."}


# 6. DELETE (Eliminar una armadura)
@app.delete("/armaduras/{nombre_modelo}")
def eliminar_armadura(nombre_modelo: str):
    if nombre_modelo not in banco_de_armaduras:
        raise HTTPException(status_code=404, detail="Armadura no encontrada. Imposible eliminar.")
    
    # El comando 'del' de Python elimina la llave y su valor del diccionario
    del banco_de_armaduras[nombre_modelo]
    return {"mensaje": f"Armadura {nombre_modelo} eliminada del registro. Protocolo de autodestrucción completado."}