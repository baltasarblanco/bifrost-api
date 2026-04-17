import os 
from redis.asyncio import Redis
from app.core.redis_client import get_redis

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.core.rate_limiter import limiter  # ← NUEVO

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from routers import ai_assistant
from app import models
from app.database import SessionLocal, engine
from app.api.endpoints import router as auth_router
from app.core.redis_client import redis_client  # ← NUEVO

# ==========================================
# 1. INICIALIZAR LA BASE DE DATOS
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación.
    
    Startup: inicializa el pool de Redis.
    Shutdown: cierra conexiones prolijamente.
    """
    # --- STARTUP ---
    # Crear tablas solo en dev real, no en tests.
    # TESTING=1 lo seteará el conftest.py antes de importar la app.
    is_testing = os.getenv("TESTING") == "1"
    
    if not is_testing:
        models.Base.metadata.create_all(bind=engine)
        await redis_client.connect()
        print("✅ Redis pool initialized")
    
    yield
    
    # --- SHUTDOWN ---
    if not is_testing:
        await redis_client.disconnect()
        print("👋 Redis pool closed")

app = FastAPI(
    title="Bifrost API - Enterprise Resource Manager",
    description="""
    Motor transaccional de gestión de armaduras y reservas.
    
    ### Características:
    * **AI-Powered**: Extracción de intenciones con Gemini.
    * **Enterprise Ready**: Auditoría completa y Soft-Delete.
    * **Cloud Optimized**: Diseñado para despliegue en AWS.
    """,
    version="1.0.0",
    contact={
        "name": "Baltasar Blanco",
        "url": "https://github.com/baltasarblanco",
    },
    license_info={
        "name": "MIT License",
    },
    lifespan=lifespan,
)

# Rate Limiter: attach al state de la app + middleware + exception handler
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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

@app.get("/health/redis", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_redis(redis: Redis = Depends(get_redis)):
    """
    Healthcheck de Redis. Útil para:
    - Debugging local.
    - AWS App Runner / ECS healthchecks.
    - Smoke tests en CI/CD.
    """
    try:
        pong = await redis.ping()
        return {"redis": "healthy", "ping": pong}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis unhealthy: {e}",
        )

@app.post("/armaduras/", tags=["Armaduras"])
def registrar_armadura(armadura: Armadura, db: Session = Depends(get_db)):
    armadura_existente = (
        db.query(models.ArmaduraDB)
        .filter(models.ArmaduraDB.modelo == armadura.modelo)
        .first()
    )
    if armadura_existente:
        raise HTTPException(
            status_code=400, detail="Ese modelo de armadura ya está registrado."
        )

    nueva_armadura = models.ArmaduraDB(
        modelo=armadura.modelo,
        nivel_energia=armadura.nivel_energia,
        activa=armadura.activa,
    )
    db.add(nueva_armadura)
    db.commit()
    db.refresh(nueva_armadura)

    return {
        "mensaje": f"{nueva_armadura.modelo} forjada y guardada en SQL.",
        "id": nueva_armadura.id,
    }


@app.get("/armaduras/", tags=["Armaduras"])
def listar_armaduras(db: Session = Depends(get_db)):
    armaduras = db.query(models.ArmaduraDB).all()
    return {"inventario": armaduras}


@app.get("/armaduras/{nombre_modelo}", tags=["Armaduras"])
def obtener_armadura(nombre_modelo: str, db: Session = Depends(get_db)):
    armadura = (
        db.query(models.ArmaduraDB)
        .filter(models.ArmaduraDB.modelo == nombre_modelo)
        .first()
    )
    if not armadura:
        raise HTTPException(status_code=404, detail="Armadura no encontrada.")
    return armadura


@app.put("/armaduras/{nombre_modelo}", tags=["Armaduras"])
def actualizar_armadura(
    nombre_modelo: str, armadura_actualizada: Armadura, db: Session = Depends(get_db)
):
    armadura_db = (
        db.query(models.ArmaduraDB)
        .filter(models.ArmaduraDB.modelo == nombre_modelo)
        .first()
    )
    if not armadura_db:
        raise HTTPException(
            status_code=404, detail="Armadura no encontrada para actualizar."
        )

    armadura_db.nivel_energia = armadura_actualizada.nivel_energia
    armadura_db.activa = armadura_actualizada.activa
    db.commit()
    db.refresh(armadura_db)
    return {"mensaje": f"Sistemas de {nombre_modelo} actualizados."}


@app.delete("/armaduras/{nombre_modelo}", tags=["Armaduras"])
def eliminar_armadura(nombre_modelo: str, db: Session = Depends(get_db)):
    armadura_db = (
        db.query(models.ArmaduraDB)
        .filter(models.ArmaduraDB.modelo == nombre_modelo)
        .first()
    )
    if not armadura_db:
        raise HTTPException(
            status_code=404, detail="Armadura no encontrada. Imposible eliminar."
        )

    db.delete(armadura_db)
    db.commit()
    return {"mensaje": f"Armadura {nombre_modelo} eliminada permanentemente."}


# ⚠️ AQUÍ TERMINA EL ARCHIVO.
# Ya no hay un endpoint @app.post("/usuarios/") porque eso ahora lo maneja endpoints.py

app.include_router(ai_assistant.router)