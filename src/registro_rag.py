
import time
import json
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from rag_indexer import cargar_vectorstore, formatear_contexto

load_dotenv()

# =====================================================
# CONFIGURACIÓN NURSE FLOW
# =====================================================

CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_DB = CARPETA_PROYECTO / "vectorstore_nurseflow"

RUTA_JSONL = CARPETA_PROYECTO / "registros_latencia_costo.jsonl"

MODELO = "gemini-3.6-flash"

# Tarifas de referencia del ejemplo de la profesora.
# Verificar que correspondan al modelo utilizado.
TARIFA_ENTRADA = 0.3
TARIFA_SALIDA = 2.5


# =====================================================
# PROMPT DE NURSE FLOW
# =====================================================

PROMPT_TEMPLATE = """Eres NurseFlow, un asistente de consulta de protocolos
y guías clínicas de enfermería.

Responde la pregunta utilizando EXCLUSIVAMENTE la información
del contexto proporcionado.

Cita la fuente de cada afirmación utilizando su número entre
corchetes, por ejemplo [1], [2].

Si el contexto no contiene información suficiente para responder,
indícalo explícitamente. No inventes procedimientos, diagnósticos,
valores clínicos ni recomendaciones.

Entrega respuestas claras, ordenadas y con lenguaje técnico
de enfermería, pero fácil de comprender.

Recuerda que NurseFlow es una herramienta de apoyo a la consulta
clínica y no reemplaza la valoración profesional ni los protocolos
institucionales vigentes.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:
"""


# =====================================================
# 1. MEDICIÓN DE LATENCIA
# =====================================================

@contextmanager
def medir(tiempos: dict, etapa: str):

    inicio = time.perf_counter()

    try:
        yield
    finally:
        tiempos[etapa] = time.perf_counter() - inicio


# =====================================================
# 2. CÁLCULO DE COSTOS
# =====================================================

def calcular_costo(
    tokens_entrada: int,
    tokens_salida: int,
    tarifa_entrada_x1M: float = TARIFA_ENTRADA,
    tarifa_salida_x1M: float = TARIFA_SALIDA
) -> float:

    costo_entrada = (
        tokens_entrada / 1000000
    ) * tarifa_entrada_x1M

    costo_salida = (
        tokens_salida / 1000000
    ) * tarifa_salida_x1M

    return round(costo_entrada + costo_salida, 6)


# =====================================================
# 3. REGISTRAR CONSULTA RAG
# =====================================================

def registrar_consulta(vectorstore, pregunta: str, k: int = 3) -> dict:

    tiempos = {}

    chat_model = ChatGoogleGenerativeAI(
        model=MODELO
    )

    # ETAPA 1: Recuperación de información
    with medir(tiempos, "embed_y_busqueda"):

        retriever = vectorstore.as_retriever(
            search_kwargs={"k": k}
        )

        chunks = retriever.invoke(pregunta)

    # ETAPA 2: Construcción del prompt
    with medir(tiempos, "armado_prompt"):

        contexto, citas = formatear_contexto(chunks)

        prompt = PROMPT_TEMPLATE.format(
            contexto=contexto,
            pregunta=pregunta
        )

    # ETAPA 3: Generación de respuesta
    with medir(tiempos, "generacion"):

        respuesta = chat_model.invoke(prompt)

    # Obtener tokens reales informados por Gemini
    metadata = getattr(respuesta, "usage_metadata", None)

    tokens_reales = (
        dict(metadata) if metadata else None
    )

    costo_usd = None

    if tokens_reales is not None:

        tokens_entrada = tokens_reales.get("input_tokens")
        tokens_salida = tokens_reales.get("output_tokens")

        if tokens_entrada is not None and tokens_salida is not None:

            costo_usd = calcular_costo(
                tokens_entrada=tokens_entrada,
                tokens_salida=tokens_salida
            )

    # Factor de crecimiento del prompt
    factor_crecimiento = (
        round(len(prompt) / len(pregunta), 1)
        if pregunta else 0
    )

    # Construcción del registro
    registro = {

        "sistema": "NurseFlow",

        "timestamp": datetime.now(timezone.utc).isoformat(),

        "modelo": MODELO,

        "pregunta": pregunta,

        "k": k,

        "n_chunks_recuperados": len(chunks),

        "ids_recuperados": [
            chunk.id for chunk in chunks
        ],

        "respuesta_generada": respuesta.content,

        "citas_disponibles": citas,

        "tiempo_ms": {
            etapa: round(segundos * 1000, 2)
            for etapa, segundos in tiempos.items()
        },

        "tiempo_total_ms": round(
            sum(tiempos.values()) * 1000, 2
        ),

        "factor_crecimiento": f"{factor_crecimiento}x",

        "tokens": tokens_reales,

        "costo_estimado_usd": costo_usd
    }

    return registro


# =====================================================
# 4. GUARDAR REGISTRO JSONL
# =====================================================

def guardar_registro_jsonl(
    registro: dict,
    ruta_archivo=RUTA_JSONL
):

    with open(ruta_archivo, "a", encoding="utf-8") as archivo:

        archivo.write(
            json.dumps(registro, ensure_ascii=False) + "\n"
        )

    print(f"Registro guardado en: {ruta_archivo}")


# =====================================================
# 5. EJECUCIÓN PRINCIPAL
# =====================================================

if __name__ == "__main__":

    print("======================================")
    print(" MEDICIÓN DE LATENCIA Y COSTOS")
    print(" NURSE FLOW")
    print("======================================")

    # Cargar base vectorial
    vs = cargar_vectorstore(str(CARPETA_DB))

    total_chunks = vs._collection.count()

    print("Chunks disponibles:", total_chunks)

    if total_chunks == 0:
        raise ValueError("La base vectorial está vacía.")

    # Tres preguntas diferentes
    preguntas = [

        "¿Cuáles son los valores de referencia habituales "
        "de los signos vitales en adultos?",

        "¿Qué medidas debe implementar enfermería para "
        "prevenir las lesiones por presión?",

        "¿Qué aspectos debe evaluar enfermería durante "
        "la valoración de una herida?"
    ]

    # PRUEBA 1: Tres preguntas con K=3
    print("\n===== PRUEBAS CON K=3 =====")

    for numero, pregunta in enumerate(preguntas, start=1):

        print(f"\nConsulta {numero}: {pregunta}")

        registro = registrar_consulta(
            vs,
            pregunta,
            k=3
        )

        guardar_registro_jsonl(registro)

        print("Chunks recuperados:", registro["n_chunks_recuperados"])
        print("Latencia total:", registro["tiempo_total_ms"], "ms")
        print("Tokens:", registro["tokens"])
        print("Costo estimado:", registro["costo_estimado_usd"])

    # PRUEBA 2: MISMA PREGUNTA CON K=6
    print("\n===== COMPARACIÓN CON K=6 =====")

    pregunta_comparacion = preguntas[0]

    registro_k6 = registrar_consulta(
        vs,
        pregunta_comparacion,
        k=6
    )

    guardar_registro_jsonl(registro_k6)

    print("Pregunta:", pregunta_comparacion)
    print("K utilizado: 6")
    print("Chunks recuperados:", registro_k6["n_chunks_recuperados"])
    print("Latencia total:", registro_k6["tiempo_total_ms"], "ms")
    print("Tokens:", registro_k6["tokens"])
    print("Costo estimado:", registro_k6["costo_estimado_usd"])

    print("\n======================================")
    print(" EVALUACIÓN FINALIZADA")
    print("======================================")

    print("Archivo de resultados:", RUTA_JSONL)
