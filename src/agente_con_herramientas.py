import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

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
def consultar_base_clinica(consulta: str) -> str:
    """Consulta nombre, detalles y categoría de protocolos clínicos (Signos Vitales, LPP, Heridas).
    Acepta nombre, código (ej. VS01) o categoría.
    Úsala cuando el usuario pregunte por rangos, clasificaciones o guías clínicas.
    No realiza diagnósticos médicos cerrados.
    """
    consulta_limpia = consulta.strip().casefold()
    
    for codigo, item in BASE_CLINICA.items():
        coincide_codigo = consulta_limpia == codigo.casefold()
        coincide_nombre = consulta_limpia == item["nombre"].casefold()
        coincide_categoria = consulta_limpia == item["categoria"].casefold()
        
        if coincide_codigo or coincide_nombre or coincide_categoria:
            return (
                f"Protocolo/Guía: {item['nombre']}. "
                f"Categoría: {item['categoria']}. "
                f"Detalle clínico: {item['detalle']}."
            )
            
    return "Elemento clínico no encontrado. Pide al usuario que revise el nombre, código (ej. VS01) o categoría."

@tool
def evaluar_escala_braden(puntaje_movilidad: int, puntaje_humedad: int) -> str:
    """Calcula y evalúa un parcial de riesgo de LPP usando puntajes de movilidad y humedad (escala Braden simplificada).
    Úsala cuando se requiera evaluar riesgo de úlceras por presión.
    No reemplaza la valoración clínica integral de enfermería.
    """
    if puntaje_movilidad <= 0 or puntaje_humedad <= 0:
        return "Error: los puntajes de evaluación deben ser mayores que cero."
    
    subtotal = puntaje_movilidad + puntaje_humedad
    nivel_riesgo = "Alto Riesgo" if subtotal <= 4 else "Riesgo Moderado/Bajo"
    
    return (
        f"Puntaje Movilidad: {puntaje_movilidad}. "
        f"Puntaje Humedad: {puntaje_humedad}. "
        f"Suma parcial: {subtotal}. "
        f"Nivel de alerta estimado: {nivel_riesgo}."
    )
    
modelo = ChatGoogleGenerativeAI(
    model=nombre_modelo,
    api_key=clave,
    temperature=0,
    timeout=20,
    max_retries=0,
)

herramientas = [consultar_base_clinica, evaluar_escala_braden]
    
instrucciones = (
    "Eres un asistente clínico experto para la aplicación NurseFlow. Responde en español. "
    "Para consultar protocolos, rangos de signos vitales, LPP o heridas, usa consultar_base_clinica. "
    "Para evaluar riesgo parcial de LPP mediante puntajes, usa evaluar_escala_braden. "
    "Si el usuario menciona un protocolo por nombre o código y pide una evaluación, "
    "consulta primero la base clínica correspondiente. "
    "Si el usuario proporciona puntajes explícitos, puedes evaluar directamente. "
    "No inventes datos clínicos, escalas ni diagnósticos médicos. "
    "Si falta información, pídela. "
    "Si el protocolo no existe, informa eso sin inventar resultados. "
    "Para un saludo, responde directamente sin usar herramientas. "
    "Solo entregas información de protocolos, guías y apoyo a la gestión de enfermería."
)

prompt = ChatPromptTemplate.from_messages([
    ("system", instrucciones),
    ("human", "{entrada}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agente = create_tool_calling_agent(
    llm=modelo,
    tools=herramientas,
    prompt=prompt,
)

ejecutor = AgentExecutor(
    agent=agente,
    tools=herramientas,
    return_intermediate_steps=True,
    verbose=False,
    max_iterations=4,
)

def probar(entrada: str):
    print("\nCONSULTA:", entrada)

    resultado = ejecutor.invoke({"entrada": entrada})
    pasos = resultado["intermediate_steps"]

    print("\nTRAZA DE HERRAMIENTAS:")

    if not pasos:
        print("No se utilizaron herramientas.")
        
    for numero, (accion, observacion) in enumerate(pasos, start=1):
        print(f"\nPaso {numero}")
        print("Herramienta:", accion.tool)
        print("Argumentos:", accion.tool_input)
        print("Observación:", observacion)

    print("\nRESPUESTA FINAL:")
    
    salida = resultado["output"]
    
    if isinstance(salida, str):
        print(salida)
    else:
        texto = "\n".join(
            bloque["text"]
            for bloque in salida
            if isinstance(bloque, dict)
            and bloque.get("type") == "text"
            and isinstance(bloque.get("text"), str)
        )
        print(texto)
        
if __name__ == "__main__":
    print("Asistente Clínico - NurseFlow")
    
    nombres = ", ".join(
        item["nombre"]
        for item in BASE_CLINICA.values()
    )
    
    print("Módulos disponibles:", nombres)
    print("Escribe 'salir' para terminar.")
    
    while True:
        entrada = input("\nConsulta clínica: ").strip()
        
        if entrada.lower() == "salir":
            break
            
        if not entrada:
            continue
            
        probar(entrada)