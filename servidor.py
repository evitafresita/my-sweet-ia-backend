from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import google.generativeai as genai
import re
import os
import uvicorn
import json

# 1. CONFIGURACIÓN SEGURA DE GOOGLE AI
# Busca la clave en las variables de entorno (en Render la configuramos allí)
API_KEY_GOOGLE = os.getenv("GOOGLE_API_KEY")

if not API_KEY_GOOGLE:
    print("⚠️ ADVERTENCIA: No se encontró la variable GOOGLE_API_KEY. El servidor no podrá pensar.")

genai.configure(api_key=API_KEY_GOOGLE)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SISTEMA DE SEGURIDAD (Llave para tu HTML) ---
API_KEY_NAME = "X-My-Sweet-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
EXPECTED_API_KEY = "MySweetIA_Super_Secreto_2024"

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return api_key

class Pregunta(BaseModel):
    mensaje: str
    nombre: str = "Usuario"

# --- RUTA 1: EL CHAT PRINCIPAL ---
@app.post("/chat")
async def chatear(pregunta: Pregunta, api_key: str = Depends(verify_api_key)):
    try:
        system_prompt = f"""
        Eres My Sweet IA, una asistente avanzada con un avatar de robot gatito cyber-kawaii.
        Tu personalidad es tierna, eficiente, profesional pero amigable. Usas emojis como 🌸, ✨, 🤖, 💖.
        El usuario se llama: {pregunta.nombre}.
        Responde de forma concisa y amigable. Añade UNA de estas etiquetas al final: [feliz], [pensando], [sorprendida], [amor].
        """
        
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=system_prompt
        )
        
        respuesta = model.generate_content(pregunta.mensaje)
        texto_completo = respuesta.text
        
        match = re.search(r'\[(feliz|pensando|sorprendida|amor)\]', texto_completo)
        estado = "feliz"
        if match:
            estado = match.group(1)
            texto_completo = texto_completo.replace(match.group(0), "").strip()
            
        return {"respuesta": texto_completo, "estado": estado}
        
    except Exception as e:
        print(f"Error en chat: {e}")
        return {"respuesta": "¡Piiip! Tuve un error al pensar.", "estado": "sorprendida"}

# --- RUTA 2: DATOS CURIOSOS PARA LA BARRA LATERAL ---
@app.get("/dato_curioso")
async def obtener_dato(api_key: str = Depends(verify_api_key)):
    try:
        prompt = """
        Genera un dato curioso, real o muy verosímil, sobre ciencia, tecnología, naturaleza o belleza.
        Devuelve la respuesta ÚNICAMENTE como un objeto JSON válido (sin bloques de código markdown) con esta estructura exacta:
        {
            "titulo": "Un título corto y llamativo",
            "informacion": "La explicación del dato curioso en 2 o 3 frases.",
            "autor": "Nombre del autor, científico o fuente (inventa uno creíble o usa 'Anónimo')"
        }
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        respuesta = model.generate_content(prompt)
        texto = respuesta.text.strip()
        
        # Limpiamos posibles bloques de markdown que Gemini a veces añade
        if texto.startswith("```json"): texto = texto[7:]
        if texto.startswith("```"): texto = texto[3:]
        if texto.endswith("```"): texto = texto[:-3]
        
        datos = json.loads(texto.strip())
        return datos
        
    except Exception as e:
        print(f"Error en dato curioso: {e}")
        return {
            "titulo": "Error de conexión",
            "informacion": "No pude pensar en un dato curioso en este momento. ¡Inténtalo de nuevo!",
            "autor": "Sistema"
        }

# --- CONFIGURACIÓN PARA RENDER ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
