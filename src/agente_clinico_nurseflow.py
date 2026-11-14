import json
import os
import sys
import time
import msvcrt
from datetime import datetime, timezone

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

load_dotenv()
clave = os.getenv("GEMINI_API_KEY")
nombre_modelo = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

if not clave:
    raise ValueError("Falta GEMINI_API_KEY en el archivo .env")

# Base de datos clínica de prueba para NurseFlow
BASE_CLINICA = {
    "VS01": {"nombre": "Signos Vitales Adulto", "detalle": "PA normal <120/80 mmHg, FC 60-100 lpm, T° 36.5-37.5°C, SatO2 >=95%", "categoria": "Signos Vitales"},
    "LPP02": {"nombre": "Lesiones por Presión (LPP)", "detalle": "Estadios I al IV según profundidad y compromiso tisular", "categoria": "LPP"},
    "HER03": {"nombre": "Evaluación de Heridas", "detalle": "Clasificación por tipo de tejido (Granulación, Esfacelo, Necrosis)", "categoria": "Heridas"}
}

@tool
def consultar_base_clinica(codigo: str) -> str:
    """Consulta nombre, detalle clínico y categoría por código de protocolo.
    Uso: bajo riesgo (solo lectura).
    """
    item = BASE_CLINICA.get(codigo.strip().upper())
    if item is None:
        return "Elemento clínico no encontrado. Solicita un código válido (ej. VS01, LPP02, HER03)."
    return json.dumps(item, ensure_ascii=False)

class ArgumentosEvaluacionBraden(BaseModel):
    puntaje_movilidad: int = Field(gt=0, description="Puntaje de movilidad (1 a 4).")
    puntaje_humedad: int = Field(gt=0, description="Puntaje de humedad (1 a 4).")

@tool(args_schema=ArgumentosEvaluacionBraden)
def evaluar_escala_braden(puntaje_movilidad: int, puntaje_humedad: int) -> str:
    """Calcula y evalúa un parcial de riesgo de LPP.
    Uso: bajo riesgo (cálculo local).
    """
    subtotal = puntaje_movilidad + puntaje_humedad
    nivel_riesgo = "Alto Riesgo" if subtotal <= 4 else "Riesgo Moderado/Bajo"
    return json.dumps({
        "subtotal_parcial": subtotal,
        "nivel_riesgo": nivel_riesgo,
    }, ensure_ascii=False)

# --- SISTEMA DE APROBACIÓN HUMANA (Alto Riesgo) ---
registro_aprobaciones = []
registros_clinicos = {}

def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: float = 30) -> bool:
    """Espera una tecla s/n en la terminal de Windows sin pulsar Enter."""
    if not sys.stdin.isatty():
        return False
    while msvcrt.kbhit():
        msvcrt.getwch()
    print(mensaje, flush=True)
    limite = time.monotonic() + tiempo_limite_segundos
    while time.monotonic() < limite:
        if msvcrt.kbhit():
            respuesta = msvcrt.getwch().lower()
            if respuesta in ("s", "n"):
                print(respuesta)
                return respuesta == "s"
        time.sleep(0.05)
    print("Tiempo agotado: acción no aprobada.")
    return False

class ArgumentosRegistroClinico(BaseModel):
    id_paciente: str = Field(min_length=1, description="Identificador del paciente.")
    intervencion: str = Field(min_length=1, description="Detalle de la intervención clínica a registrar.")

@tool(args_schema=ArgumentosRegistroClinico)
def actualizar_registro_clinico(id_paciente: str, intervencion: str) -> str:
    """Modifica o ingresa notas en la ficha clínica oficial del paciente.
    Uso: ALTO RIESGO. Requiere aprobación humana obligatoria en consola.
    """
    id_paciente = id_paciente.strip().upper()
    argumentos = {"id_paciente": id_paciente, "intervencion": intervencion}
    
    aprobado = esperar_aprobacion(
        f"APROBACIÓN CLÍNICA: Registrar intervención '{intervencion}' para paciente {id_paciente}. "
        "¿Aprobar? s/n, sin Enter (30 segundos):"
    )
    
    registro_aprobaciones.append({
        "herramienta": "actualizar_registro_clinico",
        "argumentos": argumentos,
        "aprobado": aprobado,
        "momento": datetime.now(timezone.utc).isoformat(),
    })
    
    if not aprobado:
        return "Acción NO aprobada por el profesional. No se modificó el registro clínico."
    
    registros_clinicos[id_paciente] = intervencion
    return f"Registro clínico actualizado con éxito para el paciente {id_paciente}."

# --- GESTIÓN DE MEMORIA Y TRAZAS ---
historiales = {}

def obtener_historial(session_id: str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]

def normalizar_salida(resultado):
    texto = AIMessage(content=resultado["output"]).text
    return {**resultado, "output": str(texto)}

def registrar_traza(resultado, sesion):
    os.makedirs("docs", exist_ok=True)
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": sesion,
        "entrada": resultado["entrada"],
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "aprobaciones": registro_aprobaciones.copy(),
        "respuesta_final": resultado["output"],
    }
    with open("docs/trazas_agente.jsonl", "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    modelo = ChatGoogleGenerativeAI(
        model=nombre_modelo,
        api_key=clave,
        temperature=0,
        timeout=30,
        max_retries=0,
    )
    
    herramientas = [consultar_base_clinica, evaluar_escala_braden, actualizar_registro_clinico]
    
    prompt_agente = ChatPromptTemplate.from_messages([
        (
            "system",
            "Eres un asistente clínico experto para la aplicación NurseFlow con memoria conversacional. Responde en español. "
            "Usa consultar_base_clinica para protocolos, evaluar_escala_braden para riesgo de LPP, "
            "y actualizar_registro_clinico solo si el usuario solicita explícitamente modificar fichas clínicas. "
            "La herramienta de actualización requiere aprobación interactiva en consola. "
            "No inventes datos clínicos ni diagnósticos médicos."
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    
    agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)
    ejecutor_agente = AgentExecutor(
        agent=agente,
        tools=herramientas,
        return_intermediate_steps=True,
        max_iterations=4,
        verbose=False,
    )
    
    ejecutor_con_texto = ejecutor_agente | RunnableLambda(normalizar_salida)
    
    agente_con_memoria = RunnableWithMessageHistory(
        ejecutor_con_texto,
        obtener_historial,
        input_messages_key="entrada",
        history_messages_key="chat_history",
        output_messages_key="output",
    )
    
    config_turno = {"configurable": {"session_id": "turno_enfermeria_01"}}
    
    entradas_prueba = [
        "Consulta el protocolo con código VS01.",
        "Evalúa la escala Braden con movilidad 2 y humedad 1.",
        "Actualiza el registro clínico del paciente PAC-99 con 'Curación plana avanzada'."
    ]
    
    print("Iniciando pruebas de NurseFlow. (Para la última prueba, presiona 's' o 'n' en la consola cuando se solicite)")
    
    for entrada in entradas_prueba:
        registro_aprobaciones.clear()
        resultado = {
            "entrada": entrada,
            "output": "Turno sin finalizar; revisar error en consola.",
            "intermediate_steps": [],
        }
        try:
            resultado = agente_con_memoria.invoke({"entrada": entrada}, config=config_turno)
            print(f"\nUsuario: {entrada}")
            print(f"Asistente: {resultado['output']}")
        finally:
            registrar_traza(resultado, "turno_enfermeria_01")
            
    print("\nTrazas guardadas exitosamente en docs/trazas_agente.jsonl")