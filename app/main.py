from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI (
    title="Project Bifrost",
    description="Protocolo Ronin - Puente de iNserción Comercial",
    version = "Mark 2.0"
)

# 1. EL "STRUCT" ESCRICTO: Definimos cómo debe lucir una Armadura
class Armadura(BaseModel):
    modelo: str
    nivel_energia: int
    activa: bool = False # Si no nos mandan este dato, por defecto es False

# 2. ENDPOINT DE LECTURA (GET)
@app.get("/")
def root():
    return {"sistema": "Pop!_OS", "estado": "En line"}

# 3. ENDPOINT DE ESCRITURA (POST)
@app.post("/armadura/")
def registrar_armadura(armadura: Armadura):
    # Gracias a Pydanticd, si el codigo llega a esta linea.
    # TENEMOS GARATIA de que nivel_energia es un integer válido. 

    if armadura.nivel_energia < 20:
        return {
            "alerta": f"CRÍTICO: La armadura {armadura.modelo} no tiene energía suficiente.",
            "datos_recibidos": armadura          
        }
    return {
        "mensaje": f"Armadura {armadura.modelo} autorizada y registrada.",
        "datos_recibo": armadura
    }
