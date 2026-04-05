from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Importamos las piezas que creaste en el Día 5
from . import models
from .database import SessionLocal, engine

# 1. INICIALIZAR EL DISCO DURO
# Esta línea le dice a SQLAlchemy: "Creá el archivo bifrost.db y todas las tablas si no existen"
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Bifrost", version="Mark 4.0 (Persistente)")

# El "Struct" de validación de entrada (Pydantic)
class Armadura(BaseModel):
    modelo: str
    nivel_energia: int
    activa: bool = False

# 2. EL GESTOR DE CONEXIONES (Dependencia)
# Abre una sesión para la petición HTTP y la cierra obligatoriamente al terminar
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"sistema": "Pop!_OS", "estado": "En línea y Persistente"}

# --- ENDPOINTS REFACTORIZADOS A SQL ---

# CREATE
@app.post("/armaduras/")
def registrar_armadura(armadura: Armadura, db: Session = Depends(get_db)):
    # Verificamos si el modelo ya existe en la DB para no duplicarlo
    armadura_existente = db.query(models.ArmaduraDB).filter(models.ArmaduraDB.modelo == armadura.modelo).first()
    if armadura_existente:
        raise HTTPException(status_code=400, detail="Ese modelo de armadura ya está registrado.")

    # Traducimos de Pydantic a SQLAlchemy
    nueva_armadura = models.ArmaduraDB(
        modelo=armadura.modelo,
        nivel_energia=armadura.nivel_energia,
        activa=armadura.activa
    )
    
    db.add(nueva_armadura)  # La preparamos
    db.commit()             # Impactamos el disco duro
    db.refresh(nueva_armadura) # Refrescamos para obtener el ID generado (Primary Key)
    
    return {"mensaje": f"{nueva_armadura.modelo} forjada y guardada en SQL.", "id": nueva_armadura.id}

# READ ALL
@app.get("/armaduras/")
def listar_armaduras(db: Session = Depends(get_db)):
    # Un simple "SELECT * FROM armaduras"
    armaduras = db.query(models.ArmaduraDB).all()
    return {"inventario": armaduras}

# READ ONE
@app.get("/armaduras/{nombre_modelo}")
def obtener_armadura(nombre_modelo: str, db: Session = Depends(get_db)):
    # "SELECT * FROM armaduras WHERE modelo = nombre_modelo LIMIT 1"
    armadura = db.query(models.ArmaduraDB).filter(models.ArmaduraDB.modelo == nombre_modelo).first()
    
    if not armadura:
        raise HTTPException(status_code=404, detail="Armadura no encontrada en los archivos de S.H.I.E.L.D.")
    return armadura

# 5. UPDATE SQL (Actualizar en el disco)
@app.put("/armaduras/{nombre_modelo}")
def actualizar_armadura(nombre_modelo: str, armadura_actualizada: Armadura, db: Session = Depends(get_db)):
    # 1. Buscar en la base de datos
    armadura_db = db.query(models.ArmaduraDB).filter(models.ArmaduraDB.modelo == nombre_modelo).first()
    
    if not armadura_db:
        raise HTTPException(status_code=404, detail="Armadura no encontrada para actualizar.")
    
    # 2. Modificar los atributos
    armadura_db.nivel_energia = armadura_actualizada.nivel_energia
    armadura_db.activa = armadura_actualizada.activa
    
    # 3. Sellar la transacción en el disco
    db.commit()
    db.refresh(armadura_db)
    
    return {"mensaje": f"Sistemas de {nombre_modelo} actualizados en la base de datos."}

# 6. DELETE SQL (Eliminar del disco)
@app.delete("/armaduras/{nombre_modelo}")
def eliminar_armadura(nombre_modelo: str, db: Session = Depends(get_db)):
    # 1. Buscar en la base de datos
    armadura_db = db.query(models.ArmaduraDB).filter(models.ArmaduraDB.modelo == nombre_modelo).first()
    
    if not armadura_db:
        raise HTTPException(status_code=404, detail="Armadura no encontrada. Imposible eliminar.")
    
    # 2. Ejecutar borrado y sellar transacción
    db.delete(armadura_db)
    db.commit()
    
    return {"mensaje": f"Armadura {nombre_modelo} eliminada permanentemente del archivo."}