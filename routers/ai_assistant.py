from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime, timezone
from typing import Literal
import os

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])

# ==========================================
# 1. EL ESQUEMA ESTRICTO (El traductor para la Base de Datos)
# ==========================================
class ReservationIntent(BaseModel):
    armor_modelo: str = Field(
        description="El modelo exacto de la armadura mencionada (ej: Mark IV, Stealth, Asalto). Si no se menciona, devuelve 'Desconocido'."
    )
    # Obligamos a la IA a calcular la fecha real y devolverla en formato ISO 8601
    fecha_inicio: datetime = Field(
        description="La fecha y hora exacta de inicio de la reserva en formato ISO 8601."
    )
    fecha_fin: datetime = Field(
        description="La fecha y hora exacta de finalización de la reserva en formato ISO 8601. Si el usuario no especifica, asume que dura 24 horas."
    )
    # Restringimos las opciones para que no invente acciones raras
    accion: Literal["crear_reserva", "cancelar_reserva", "consultar_disponibilidad"] = Field(
        description="La intención del usuario."
    )

class UserPrompt(BaseModel):
    text: str

# ==========================================
# 2. EL ENDPOINT PRINCIPAL
# ==========================================
@router.post("/analyze")
async def analyze_reservation_request(prompt: UserPrompt):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY no está configurada")

    # Usamos el modelo estable que confirmamos que tenés disponible
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(ReservationIntent)

    # 🕒 INYECCIÓN DE CONTEXTO: Le pasamos la hora real del servidor
    ahora = datetime.now(timezone.utc)
    
    system_template = """
    Eres el sistema de procesamiento logístico del Hangar Bifrost.
    Tu trabajo es extraer parámetros estrictos para la base de datos PostgreSQL a partir del mensaje del usuario.
    
    INFORMACIÓN DEL SISTEMA:
    - Fecha y hora actual del servidor: {fecha_actual}
    
    REGLAS ESTRICTAS:
    1. Calcula las fechas relativas (ej: "mañana", "el viernes") usando la fecha actual del servidor.
    2. Las fechas deben ser devueltas en formato de marca de tiempo (ISO 8601 con zona horaria UTC).
    3. Si la armadura es "sigilosa", el modelo es "Stealth". Si es "asalto pesado", el modelo es "Hulkbuster".
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("user", "{user_text}")
    ])

    chain = prompt_template | structured_llm
    
    try:
        # Ejecutamos la cadena inyectando el texto del usuario Y la fecha actual
        resultado = chain.invoke({
            "user_text": prompt.text,
            "fecha_actual": ahora.isoformat()
        })
        
        # FastAPI automáticamente convertirá los objetos datetime a un JSON seguro
        return {"status": "success", "extracted_data": resultado}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento de IA: {str(e)}")