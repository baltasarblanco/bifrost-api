from fastapi import Request
from app.core.rate_limiter import limiter
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from fastapi import Request
from app.core.rate_limiter import limiter

# Importaciones de seguridad
from app.core.security import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
    verify_password,
)
from app.schemas.token import Token, TokenPayload
from app.api.dependencies import get_current_user
from app import models, schemas

# Importaciones de Base de Datos y Modelos
from app.database import (
    get_db,
)  # <-- Asegurate de que esta ruta a tu get_db sea la correcta
from app.models import UsuarioDB
from app.schemas import (
    UsuarioCreate,
    UsuarioResponse,
)  # <-- Vi en tu Swagger que ya tenés estos esquemas

router = APIRouter()


# ==========================================
# 1. REGISTRO DE USUARIO (El Blindaje)
# ==========================================
@router.post(
    "/usuarios/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/hour")
def crear_usuario(
    request: Request,
    usuario_in: UsuarioCreate,
    db: Session = Depends(get_db),
):
    """
    Registra un nuevo usuario encriptando su contraseña con Bcrypt.
    """
    user_exists = (
        db.query(UsuarioDB).filter(UsuarioDB.email == usuario_in.email).first()
    )
    if user_exists:
        raise HTTPException(
            status_code=400, detail="El email ya está registrado en el sistema."
        )

    hashed_pw = get_password_hash(usuario_in.password)
    nuevo_usuario = UsuarioDB(email=usuario_in.email, hashed_password=hashed_pw)
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


# ==========================================
# 2. LOGIN (La Puerta de Entrada)
# ==========================================
@router.post("/login/access-token", response_model=Token)
@limiter.limit("5/minute")
def login_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Endpoint para autenticar usuarios contra la base de datos y devolver un JWT.
    """
    user = db.query(UsuarioDB).filter(UsuarioDB.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# 3. ZONA VIP
# ==========================================
@router.get("/ruta-privada")
def ruta_super_secreta(current_user: TokenPayload = Depends(get_current_user)):
    """
    Este endpoint está blindado. Si llegás acá, es porque tu JWT es válido.
    """
    return {
        "mensaje": "¡Bienvenido a la zona VIP de Bifrost!",
        "usuario_logueado": current_user.sub,
    }


@router.post("/reservas/", response_model=schemas.ReservaResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def crear_reserva(
    request: Request,
    reserva_in: schemas.ReservaCreate,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Crea una nueva reserva aplicando bloqueos pesimistas para evitar overbooking.
    """
    # 0. BUSCAMOS AL USUARIO EN LA DB (Para obtener su ID)
    usuario = db.query(models.UsuarioDB).filter(models.UsuarioDB.email == current_user.sub).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en la base de datos.")

    # 1. BLOQUEO PESIMISTA: Buscamos la armadura y bloqueamos su fila.
    armadura = db.query(models.ArmaduraDB).filter(
        models.ArmaduraDB.modelo == reserva_in.armadura_modelo
    ).with_for_update().first()

    if not armadura:
        raise HTTPException(status_code=404, detail="Armadura no encontrada.")

    if not armadura.activa:
        raise HTTPException(status_code=400, detail="La armadura se encuentra fuera de servicio.")

    # 2. DETECCIÓN DE COLISIONES TEMPORALES (Overbooking)
    colision = db.query(models.ReservaDB).filter(
        models.ReservaDB.armadura_modelo == reserva_in.armadura_modelo,
        models.ReservaDB.estado == "activa",
        models.ReservaDB.fecha_inicio < reserva_in.fecha_fin,
        models.ReservaDB.fecha_fin > reserva_in.fecha_inicio
    ).first()

    if colision:
        raise HTTPException(
            status_code=409,
            detail="Operación rechazada: La armadura ya está reservada para ese rango horario."
        )

    # 3. PERSISTENCIA
    nueva_reserva = models.ReservaDB(
        usuario_id=usuario.id,  # <-- Usamos el ID numérico que requiere la tabla
        armadura_modelo=reserva_in.armadura_modelo,
        fecha_inicio=reserva_in.fecha_inicio,
        fecha_fin=reserva_in.fecha_fin,
        estado="activa"
    )
    
    db.add(nueva_reserva)
    db.commit()
    db.refresh(nueva_reserva)

    return nueva_reserva

@router.get("/reservas/mis-reservas", response_model=List[schemas.ReservaResponse])
def obtener_mis_reservas(
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Devuelve el historial completo de reservas del usuario autenticado.
    """
    # 1. Buscamos el ID del usuario real
    usuario = db.query(models.UsuarioDB).filter(models.UsuarioDB.email == current_user.sub).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # 2. Traemos TODAS las reservas que le pertenecen a este usuario
    reservas = db.query(models.ReservaDB).filter(
        models.ReservaDB.usuario_id == usuario.id
    ).order_by(models.ReservaDB.fecha_inicio.desc()).all()

    # Si no tiene reservas, devolvemos una lista vacía [], lo cual es correcto en REST
    return reservas

@router.patch("/reservas/{reserva_id}/cancelar", response_model=schemas.ReservaResponse)
def cancelar_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Cancela una reserva activa del usuario. Solo el dueño puede cancelarla.
    """
    # 1. Buscamos al usuario
    usuario = db.query(models.UsuarioDB).filter(models.UsuarioDB.email == current_user.sub).first()
    
    # 2. Buscamos la reserva y aplicamos bloqueo pesimista (para que nadie la use mientras cancelamos)
    reserva = db.query(models.ReservaDB).filter(
        models.ReservaDB.id == reserva_id,
        models.ReservaDB.usuario_id == usuario.id  # <-- SEGURIDAD: Solo podés cancelar las TUYAS
    ).with_for_update().first()

    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada o no tienes permiso.")

    if reserva.estado == "cancelada":
        raise HTTPException(status_code=400, detail="La reserva ya se encuentra cancelada.")

    # 3. Cambiamos el estado
    reserva.estado = "cancelada"
    
    db.commit()
    db.refresh(reserva)

    return reserva


@router.get("/admin/reservas", response_model=List[schemas.ReservaResponse])
def obtener_todas_las_reservas(
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user) # <-- Por ahora cualquier logueado entra
):
    """
    VISTA DE ADMINISTRADOR: Devuelve todas las reservas del sistema.
    """
    # En una fase avanzada, aquí preguntaríamos: if usuario.rol != "admin": raise 403
    
    todas = db.query(models.ReservaDB).all()
    return todas


# ==========================================
# 4. ADMINISTRACIÓN Y DISPONIBILIDAD
# ==========================================

@router.get("/armaduras/disponibles", response_model=List[schemas.ArmaduraResponse])
@limiter.limit("60/minute")
def listar_disponibilidad_actual(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Muestra las armaduras que NO tienen reservas activas en este preciso momento.
    """
    ahora = datetime.now(timezone.utc)
    
    # 1. Buscamos qué modelos de armadura tienen una reserva "pisando" el horario de ahora
    ocupadas = db.query(models.ReservaDB.armadura_modelo).filter(
        models.ReservaDB.estado == "activa",
        models.ReservaDB.fecha_inicio <= ahora,
        models.ReservaDB.fecha_fin >= ahora
    ).all()
    
    # Convertimos la lista de tuplas de SQLAlchemy en una lista simple de strings
    lista_modelos_ocupados = [r[0] for r in ocupadas]

    # 2. Filtramos armaduras: que no estén ocupadas, estén activas y NO estén borradas
    libres = db.query(models.ArmaduraDB).filter(
        models.ArmaduraDB.modelo.notin_(lista_modelos_ocupados),
        models.ArmaduraDB.activa,
        models.ArmaduraDB.is_deleted.is_(False)
    ).all()
    
    return libres

# --- Agregá esto arriba de tus endpoints ---

# Esta versión BUSCA al usuario en la DB para ver si es Admin
async def get_current_admin_user(
    current_user_payload: schemas.TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(models.UsuarioDB).filter(models.UsuarioDB.email == current_user_payload.sub).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    return user
# -------------------------------------------

@router.delete("/admin/armaduras/{armadura_id}", status_code=204)
def borrar_armadura(
    armadura_id: int,
    db: Session = Depends(get_db),
    current_admin: models.UsuarioDB = Depends(get_current_admin_user)
):
    """
    SOFT DELETE: Marca una armadura como fuera de servicio.
    Preserva el historial pero la quita de la vista del usuario.
    """
    armadura = db.query(models.ArmaduraDB).filter(models.ArmaduraDB.id == armadura_id).first()
    
    if not armadura:
        raise HTTPException(status_code=404, detail="Esa armadura no existe en el hangar.")

    armadura.is_deleted = True
    db.commit()
    
    return None # 204 No Content no devuelve cuerpo