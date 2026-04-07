from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Importaciones locales
from app import models, schemas
from app.database import SessionLocal, engine
from app.api.endpoints import router as auth_router

# ==========================================
# 1. INICIALIZAR LA BASE DE DATOS
# ==========================================
# ⚠️ ESTA LÍNEA ES CLAVE: Crea las tablas físicas en la DB si no existen
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Bifrost", version="Mark 4.0 (Persistente y Seguro)")

# ==========================================
# 2. ENRUTAMIENTO DE SEGURIDAD (La rama nueva)
# ==========================================
app.include_router(auth_router, tags=["Autenticación y Usuarios"])

# ==========================================
# 3. GESTOR DE CONEXIONES (Dependencia)
# ==========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 4. RUTAS DEL SISTEMA (Las Armaduras originales)
# ==========================================
class Armadura(BaseModel):
    modelo: str
    nivel_energia: int
    activa: bool = False

@app.get("/")
def root():
    return {"sistema": "Pop!_OS", "estado": "En línea, Persistente y Seguro"}

@app.post("/armaduras/", tags=["Armaduras"])
def registrar_armadura(armadura: Armadura, db: Session = Depends(get_db)):
    armadura_existente = db.query(models.ArmaduraDB).filter(models.ArmaduraDB.modelo == armadura.modelo).first()
    if armadura_existente:
        raise HTTPException(status_code=400, detail="Ese modelo de armadura ya está registrado.")

    nueva_armadura = models.ArmaduraDB(
        modelo=armadura.modelo,
        nivel_energia=armadura.nivel_energia,
        activa=armadura.activa
    )
    db.add(nueva_armadura)  
    db.commit()             
    db.refresh(nueva_armadura) 
    
    return {"mensaje": f"{nueva_armadura.modelo} forjada y guardada en SQL.", "id": nueva_armadura.id}

@app.get("/armaduras/", tags=["Armaduras"])
def listar_armaduras(db: Session = Depends(get_db)):
    armaduras = db.query(models.ArmaduraDB).all()
    return {"inventario": armaduras}

@app.get("/armaduras/{nombre_modelo}", tags=["Armaduras"])
def obtener_armadura(nombre_modelo: str, db: Session = Depends(get_db)):
    armadura = db.query(models.ArmaduraDB).filter(models.ArmaduraDB.modelo == nombre_modelo).first()
    if not armadura:
        raise HTTPException(status_code=404, detail="Armadura no encontrada.")
    return armadura

@app.put("/armaduras/{nombre_modelo}", tags=["Armaduras"])
def actualizar_armadura(nombre_modelo: str, armadura_actualizada: Armadura, db: Session = Depends(get_db)):
    armadura_db = db.query(models.ArmaduraDB).filter(models.ArmaduraDB.modelo == nombre_modelo).first()
    if not armadura_db:
        raise HTTPException(status_code=404, detail="Armadura no encontrada para actualizar.")
    
    armadura_db.nivel_energia = armadura_actualizada.nivel_energia
    armadura_db.activa = armadura_actualizada.activa
    db.commit()
    db.refresh(armadura_db)
    return {"mensaje": f"Sistemas de {nombre_modelo} actualizados."}

@app.delete("/armaduras/{nombre_modelo}", tags=["Armaduras"])
def eliminar_armadura(nombre_modelo: str, db: Session = Depends(get_db)):
    armadura_db = db.query(models.ArmaduraDB).filter(models.ArmaduraDB.modelo == nombre_modelo).first()
    if not armadura_db:
        raise HTTPException(status_code=404, detail="Armadura no encontrada. Imposible eliminar.")
    
    db.delete(armadura_db)
    db.commit()
    return {"mensaje": f"Armadura {nombre_modelo} eliminada permanentemente."}

# ⚠️ AQUÍ TERMINA EL ARCHIVO. 
# Ya no hay un endpoint @app.post("/usuarios/") porque eso ahora lo maneja endpoints.py