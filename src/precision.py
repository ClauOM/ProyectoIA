from collections import Counter
from pipeline_limpieza import *
from cliente import *
import json


def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre referencia y respuesta."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    coincidencias = contar_coincidencias(
        tokens_referencia, tokens_respuesta
    )

    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    resultado = {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }

    return resultado

def calcular_metricas(texto_referencia, texto_respuesta):
    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)
    
    return calcular_precision_cobertura_f1(
        tokens_referencia, tokens_respuesta
    )

casos = [
    (
        "¿Cuál es el protocolo de valoración para la presión arterial sistólica elevada?",
        "Si la presión arterial sistólica es mayor a 140 mmHg, se debe reportar inmediatamente como elevación tensional, verificar reposo previo de 5 minutos y registrar el evento en el sistema.",
    ),
    (
        "¿Cómo se registra una LPP en estadio 3 en la región sacra?",
        "Se debe documentar con el estadio 3, ubicación en región sacra, registrar las dimensiones en centímetros (largo x ancho x profundidad), evaluar el tipo de tejido presente (ej. granulación o esfacelo) y reportar el nivel de exudado.",
    ),
    (
        "¿Cuál es el manejo inicial ante una herida quirúrgica con signos de infección?",
        "Se debe verificar el estado de los bordes (eritematosos o macerados), documentar la presencia de signos de infección, evaluar la necesidad de cultivo y notificar al médico tratante para la revisión de la cobertura o indicación de tratamiento.",
    ),
]
resultados = []

for consulta, referencia in casos:
    respuesta = consultar_modelo(consulta, system_instruction="Responde en español con una definición breve, en una sola oración de máximo 15 palabras. Sin listas, ejemplos ni introducciones.")
    
    metricas = calcular_metricas(referencia, respuesta)
    
    print("Consulta:", consulta)
    print("Respuesta:", respuesta)
    print("Métricas:", metricas)
    
    resultados.append({
        "consulta": consulta,
        "respuesta": respuesta,
        **metricas,
    })
    
resultados = sorted(resultados, key=lambda r: r["f1"])

with open(
    "resultados_metricas.json", "w", encoding="utf-8"
) as archivo:
    json.dump(resultados, archivo, indent=2, ensure_ascii=False)

def resumir_metricas(resultados):
    if not resultados:
        return {
            "precision_promedio": 0,
            "cobertura_promedio": 0,
            "f1_promedio": 0,
        }
    n = len(resultados)
    return {
        "precision_promedio": sum(
            r["precision"] for r in resultados
        ) / n,
        "cobertura_promedio": sum(
            r["cobertura"] for r in resultados
        ) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }
    
print("Promedios")
print(resumir_metricas(resultados))
    
peores_casos = sorted(resultados, key=lambda r: r["f1"])

for caso in peores_casos[:3]:
    print(caso["consulta"], caso["f1"])
    
    
# referencia = procesar_texto(
#     "Python es un lenguaje de programación interpretado."
# )

# texto_respuesta = consultar_modelo("¿Qué es Python?",
#                                    system_instruction="Responde en español con una definición breve, en una sola oración de máximo 15 palabras. Sin listas, ejemplos ni introducciones.")

# respuesta = procesar_texto(texto_respuesta)
# resultado = calcular_precision_cobertura_f1(referencia, respuesta)

# print("Respuesta:", texto_respuesta)
# print("Tokens de referencia:", len(referencia))
# print("Tokens de respuesta:", len(respuesta))
# print(resultado)

