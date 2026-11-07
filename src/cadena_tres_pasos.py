from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo
from langchain_core.prompts import PromptTemplate #Plantilla -> Prompt dinámico
from langchain_core.output_parsers import StrOutputParser #Parsea la respuesta y la transforma en solo textos
from langchain_core.prompts import ChatPromptTemplate #Plantilla que incluye rol del sistema e instrucción

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash") #temperature= 0 - 1

plantilla_extraccion = PromptTemplate.from_template("Lee el siguiente reporte clínico y extrae los 3 puntos clave correspondientes a: 1. Signos vitales, 2. Estado de LPP (lesiones por presión) y 3. Estado de heridas. Escribe uno por línea, sin desarrollarlos en exceso: \n\n {texto}")

paso_extraccion = plantilla_extraccion | modelo | StrOutputParser()

texto_prueba = (
    "Paciente adulto mayor postrado, se recibe lúcido. "
    "Al control de signos vitales presenta Presión Arterial de 135/85 mmHg, "
    "Frecuencia Cardíaca de 78 lpm, Frecuencia Respiratoria de 18 rpm, "
    "Saturación de Oxígeno del 96% ambiental y Temperatura de 36.5 °C. "
    "En la evaluación tegumentaria se observa LPP en región sacra estadio 2, "
    "de 3x2 cm con tejido de granulación y escaso exudado seroso. "
    "Además, presenta herida quirúrgica limpia en miembro inferior izquierdo "
    "de 5 cm con bordes bien afrontados y sin signos de infección local."
)

# puntos = paso_extraccion.invoke(
#     {"texto": texto_prueba}
# )

# print(puntos)

plantilla_simplificacion = PromptTemplate.from_template("Reescribe estos puntos utilizando terminología clínica y lenguaje técnico adecuado para personal de salud, en formato de viñetas markdown y sin introducción: \n\n{puntos}")

paso_simplificacion = plantilla_simplificacion | modelo | StrOutputParser()

# simple = paso_simplificacion.invoke(
#     {"puntos": puntos}
# )

# print(simple)

plantilla_formato = PromptTemplate.from_template("Convierte este texto en una lista de viñetas markdown de máximo 3 líneas, sin introducción: \n\n{texto_simple}")

paso_formato = plantilla_formato | modelo | StrOutputParser()

# formato = paso_formato.invoke(
#     {"texto_simple": simple}
# )

# print(formato)

#Sintaxis lambda -> lambda argumentos: expresion
cadena_tres_pasos = (
    plantilla_extraccion
    | modelo
    | StrOutputParser()
    | (lambda puntos: {"puntos": puntos})
    | plantilla_simplificacion
    | modelo
    | StrOutputParser()
    | (lambda simple: {"texto_simple": simple})
    | plantilla_formato
    | modelo
    | StrOutputParser()
)

respuesta = cadena_tres_pasos.invoke(
    {"texto": texto_prueba} #El diccionario que corresponde al primer paso/acción inicial
) 

print(respuesta)
