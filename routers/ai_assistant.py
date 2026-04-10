from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import google.generativeai as genai
import os

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])

# 1. Definimos qué formato EXACTO queremos que devuelva Gemini
class ReservationIntent(BaseModel):
    armor_type: str = Field(description="El tipo o nombre de la armadura mencionada (ej: Mark IV, Stealth, Asalto). Si no se menciona, devuelve 'Unknown'.")
    date_requested: str = Field(description="La fecha o momento solicitado (ej: 'Viernes por la tarde', 'mañana').")
    action: str = Field(description="La acción que quiere hacer el usuario (ej: 'reserve', 'inquire', 'cancel').")

# 2. Esquema para lo que el usuario envía
class UserPrompt(BaseModel):
    text: str

@router.post("/analyze")
async def analyze_reservation_request(prompt: UserPrompt):
    # LangChain busca GOOGLE_API_KEY por defecto en las variables de entorno
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY no está configurada en el .env")

    # Inicializamos Gemini (1.5-flash es ultra rápido y perfecto para extraer datos)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    
    # Forzamos a Gemini a devolver un JSON que cumpla con el esquema ReservationIntent
    structured_llm = llm.with_structured_output(ReservationIntent)

    # Creamos el prompt con el contexto del Hangar
    system_template = """
    Eres el asistente logístico de IA del Hangar Bifrost.
    Tu trabajo es analizar el mensaje del usuario y extraer los datos de la reserva de armadura.
    No respondas conversacionalmente, solo extrae los datos pedidos.
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("user", "{user_text}")
    ])

    # Ensamblamos y ejecutamos la cadena
    chain = prompt_template | structured_llm
    
    try:
        resultado = chain.invoke({"user_text": prompt.text})
        return {"status": "success", "extracted_data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Gemini: {str(e)}")
    
@router.get("/ping")
async def ping_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta la API Key")
        
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
    
    try:
        # Hacemos una consulta cruda, sin forzar JSON ni Pydantic
        respuesta = llm.invoke("Responde exactamente con estas palabras: Conexion exitosa con Bifrost")
        return {"status": "ok", "mensaje_ia": respuesta.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error crudo: {str(e)}")
    
@router.get("/list-models")
async def list_available_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta la API Key")
        
    # Configuramos la librería base de Google
    genai.configure(api_key=api_key)
    
    # Buscamos todos los modelos que soporten generación de texto
    modelos_disponibles = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_disponibles.append(m.name)
        return {"status": "ok", "modelos": modelos_disponibles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))