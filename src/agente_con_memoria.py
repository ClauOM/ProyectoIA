import json
import os

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

BASE_CLINICA = {
    "VS01": {"nombre": "Signos Vitales Adulto", "detalle": "PA normal <120/80 mmHg, FC 60-100 lpm, T° 36.5-37.5°C, SatO2 >=95%", "categoria": "Signos Vitales"},
    "LPP02": {"nombre": "Lesiones por Presión (LPP)", "detalle": "Estadios I al IV según profundidad y compromiso tisular (Eritema no blanqueable hasta exposición ósea)", "categoria": "LPP"},
    "HER03": {"nombre": "Evaluación de Heridas", "detalle": "Clasificación por tipo de tejido (Granulación, Esfacelo, Necrosis) y características del exudado", "categoria": "Heridas"}
}

@tool
def consultar_base_clinica(codigo: str) -> str:
    """Consulta nombre, detalle clínico y categoría por código de protocolo.
    Usar para consultar datos de la base clínica. No calcula evaluaciones de riesgo.
    """
    item = BASE_CLINICA.get(codigo.strip().upper())
    
    if item is None:
        return "Elemento clínico no encontrado. Solicita un código válido (ej. VS01, LPP02, HER03)."
    
    return json.dumps(item, ensure_ascii=False)

class ArgumentosEvaluacionBraden(BaseModel):
    puntaje_movilidad: int = Field(
        gt=0,
        description="Puntaje de movilidad (1 a 4), obtenido de la consulta o del usuario."
    )
    puntaje_humedad: int = Field(
        gt=0,
        description="Puntaje de humedad (1 a 4), obtenido de la consulta o del usuario."
    )
    incluir_alerta_avanzada: bool = Field(
        default=True,
        description="True para incluir recomendación de cambio de posición; False para formato estándar."
    )
    
@tool(args_schema=ArgumentosEvaluacionBraden)
def evaluar_escala_braden(puntaje_movilidad: int, puntaje_humedad: int, 
incluir_alerta_avanzada: bool = True) -> str:
    """Calcula y evalúa un parcial de riesgo de LPP usando puntajes de movilidad y humedad (escala Braden simplificada).
    Nivel de alerta: Alto riesgo si la suma es <= 4. Incluye recomendación si incluir_alerta_avanzada es True.
    No consulta protocolos previos, no realiza diagnósticos médicos cerrados.
    """
    subtotal = puntaje_movilidad + puntaje_humedad
    nivel_riesgo = "Alto Riesgo" if subtotal <= 4 else "Riesgo Moderado/Bajo"
    recomendacion = "Requiere cambios posturales frecuentes y superficie de alivio de presión." if incluir_alerta_avanzada and subtotal <= 4 else "Mantener cuidados preventivos estándar."
    
    return json.dumps({
        "puntaje_movilidad": puntaje_movilidad,
        "puntaje_humedad": puntaje_humedad,
        "subtotal_parcial": subtotal,
        "nivel_riesgo": nivel_riesgo,
        "recomendacion": recomendacion,
    }, ensure_ascii=False) 
    
historiales = {}
    
def obtener_historial(session_id: str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]

def normalizar_salida(resultado):
    """Convierte la respuesta final a texto antes de guardarla en el historial."""
    texto = AIMessage(content=resultado["output"]).text
    
    return {
        **resultado,
        "output": str(texto),
    }

def mostrar_resultado(resultado, sesion):
    print(f"\nSESIÓN: {sesion} | Usuario: {resultado['entrada']}")
    
    pasos = resultado["intermediate_steps"]
    
    if not pasos:
        print("TRAZA: sin llamadas a herramientas.")
        
    for accion, observacion in pasos:
        print("HERRAMIENTA:", accion.tool)
        print("ARGUMENTOS:", accion.tool_input)
        print("RESULTADO:", observacion)
    
    print("ASISTENTE:", resultado["output"])
    print("Mensajes guardados:", len(obtener_historial(sesion).messages))
    
if __name__ == "__main__":
    modelo = ChatGoogleGenerativeAI(
        model=nombre_modelo,
        api_key=clave,
        temperature=0,
        timeout=30,
        max_retries=0,
    )
    
    herramientas = [consultar_base_clinica, evaluar_escala_braden]
    prompt_agente = ChatPromptTemplate.from_messages([
        (
            "system",
            "Eres un asistente clínico experto para la aplicación NurseFlow con memoria conversacional. Responde en español. "
            "Usa consultar_base_clinica para consultar protocolos, rangos o detalles clínicos y evaluar_escala_braden "
            "para calcular riesgo parcial de LPP. Usa el historial para entender referencias "
            "como 'ese protocolo' y cambios de puntajes. Puedes reutilizar la información "
            "consultada antes en esta conversación clínica. "
            "Si falta un dato y no está en el historial, pídelo. "
            "No inventes datos clínicos, escalas ni diagnósticos médicos. "
            "Solo entregas información de protocolos, guías y apoyo a la gestión de enfermería."
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    
    agente = create_tool_calling_agent(
        modelo,
        herramientas,
        prompt_agente,
    )
    
    ejecutor_agente = AgentExecutor(
        agent=agente,
        tools=herramientas,
        return_intermediate_steps=True,
        max_iterations=4,
        verbose=False,
    )
    
    ejecutor_con_texto = (
        ejecutor_agente | RunnableLambda(normalizar_salida)
    )
    
    agente_con_memoria = RunnableWithMessageHistory(
        ejecutor_con_texto,
        obtener_historial,
        input_messages_key="entrada",
        history_messages_key="chat_history",
        output_messages_key="output",
    )
    
    config_a = {"configurable": {"session_id": "turno_a"}}
    config_b = {"configurable": {"session_id": "turno_b"}}

    resultado_1 = agente_con_memoria.invoke(
        {"entrada": "Consulta el protocolo con código VS01."},
        config=config_a,
    )
    mostrar_resultado(resultado_1, "turno_a")

    resultado_2 = agente_con_memoria.invoke(
        {"entrada": "Evalúa el riesgo de LPP con movilidad 2 y humedad 1 para ese paciente."},
        config=config_a,
    )
    mostrar_resultado(resultado_2, "turno_a")

    resultado_3 = agente_con_memoria.invoke(
        {"entrada": "Y si la movilidad fuera 3, ¿cuál sería el resultado?"},
        config=config_a,
    )
    mostrar_resultado(resultado_3, "turno_a")

    resultado_4 = agente_con_memoria.invoke(
        {"entrada": "Y si la movilidad fuera 3, ¿cuál sería el resultado?"},
        config=config_b,
    )
    mostrar_resultado(resultado_4, "turno_b")