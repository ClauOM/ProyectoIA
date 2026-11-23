
import contextvars  # Genera una variable de contexto
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import sys
import uuid

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

from rag_indexer import cargar_vectorstore, formatear_contexto


"""
Contextvars: crea una variable de contexto.

Permite aislar el identificador de cada consulta,
incluso cuando existen diferentes tareas o procesos.
"""

trace_id_var = contextvars.ContextVar("trace_id", default=None)


# Transforma cada evento de log en un objeto JSON de una sola línea
class JsonFormatter(logging.Formatter):

    def format(self, record):

        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "msg": record.getMessage(),
            "sistema": "NurseFlow",
            "trace_id": trace_id_var.get()
        }

        # Si se envía información adicional (extra_data), la agregamos
        if hasattr(record, "extra_data"):
            payload.update(record.extra_data)

        return json.dumps(payload, ensure_ascii=False)


# Configuración del logger de NurseFlow
logger = logging.getLogger("nurseflow_rag_pipeline")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())

archivo_handler = RotatingFileHandler(
    "nurseflow_rag_logs.jsonl",
    encoding="utf-8",
    maxBytes=5_000_000,
    backupCount=3
)

archivo_handler.setFormatter(JsonFormatter())

logger.handlers = [handler, archivo_handler]
logger.propagate = False


# Generar una huella digital SHA-256 del texto
# Permite identificar documentos sin almacenar su contenido original
def generar_huella(texto: str) -> str:

    return hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()[:12]


"""
FUNCIONAMIENTO:

BaseCallbackHandler permite detectar eventos de LangChain:
- Cuando comienza la cadena.
- Cuando comienza la búsqueda de protocolos.
- Cuando termina la recuperación de documentos.
- Cuando comienza Gemini.
- Cuando termina la generación de respuestas.
"""


class HandlerDeTrazabilidad(BaseCallbackHandler):

    # 1. Inicio de la cadena principal
    def on_chain_start(
        self, serialized, inputs, *, run_id,
        parent_run_id=None, **kwargs
    ):

        if parent_run_id is None:

            logger.info(
                "inicio_cadena_nurseflow",
                extra={
                    "extra_data": {
                        "root_run_id": str(run_id)
                    }
                }
            )


    # CICLO DE VIDA DEL RETRIEVER
    # Se ejecuta antes de realizar la búsqueda vectorial
    def on_retriever_start(
        self, serialized, query, *, run_id,
        parent_run_id=None, metadata=None, **kwargs
    ):

        logger.info(
            "inicio_busqueda_protocolos",
            extra={
                "extra_data": {
                    "run_id": str(run_id),
                    "parent_run_id": str(parent_run_id),
                    "query_len": len(query),
                    "query_hash": generar_huella(query),
                    "meta_trace": (metadata or {}).get("trace_id")
                }
            }
        )


    # Se ejecuta después de recuperar los chunks
    def on_retriever_end(
        self, documents, *, run_id,
        parent_run_id=None, **kwargs
    ):

        # Generar huellas digitales de los protocolos recuperados
        docs_huellas = [
            generar_huella(d.page_content)
            for d in documents
        ]

        # Identificar las áreas clínicas de los documentos recuperados
        areas_clinicas = [
            d.metadata.get("area", "No especificada")
            for d in documents
        ]

        logger.info(
            "fin_busqueda_protocolos",
            extra={
                "extra_data": {
                    "n_documents": len(documents),
                    "huellas_docs": docs_huellas,
                    "areas_clinicas": areas_clinicas
                }
            }
        )


    # CICLO DE VIDA DEL MODELO GEMINI
    # Se ejecuta antes de enviar los mensajes al modelo
    def on_chat_model_start(
        self, serialized, messages, *, run_id,
        parent_run_id=None, **kwargs
    ):

        logger.info(
            "inicio_generacion_respuesta",
            extra={
                "extra_data": {
                    "run_id": str(run_id),
                    "parent_run_id": str(parent_run_id),
                    "n_prompts": len(messages)
                }
            }
        )


    # Se ejecuta cuando termina la generación de respuesta
    def on_llm_end(
        self, response, *, run_id,
        parent_run_id=None, **kwargs
    ):

        # Obtener el texto generado por Gemini
        texto_salida = response.generations[0][0].text

        logger.info(
            "fin_generacion_respuesta",
            extra={
                "extra_data": {
                    "chars_respuesta": len(texto_salida),
                    "respuesta_hash": generar_huella(texto_salida)
                }
            }
        )


"""
Cadena RAG de NurseFlow:

Pregunta del usuario
        |
        v
Retriever (búsqueda de protocolos)
        |
        v
Formatear contexto
        |
        v
Prompt clínico
        |
        v
Gemini
        |
        v
Respuesta final
"""


def ejecutar_consulta(vectorstore, pregunta: str, k: int = 3):

    # Crear identificador único para cada consulta
    token = trace_id_var.set(
        f"nurseflow-{uuid.uuid4().hex[:8]}"
    )

    try:

        # Configurar el recuperador de documentos
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": k}
        )

        # Plantilla de instrucciones para NurseFlow
        prompt = ChatPromptTemplate.from_messages([

            (
                "system",
                """Eres NurseFlow, un asistente de consulta de
                protocolos y guías clínicas de enfermería.

                Responde utilizando EXCLUSIVAMENTE la información
                del contexto recuperado.

                Cita la fuente de cada afirmación con su número
                entre corchetes, por ejemplo [1], [2].

                Si el contexto no contiene información suficiente
                para responder, indícalo explícitamente.
                No inventes procedimientos, diagnósticos,
                valores clínicos ni recomendaciones.

                Entrega respuestas claras y organizadas,
                utilizando lenguaje técnico de enfermería
                fácil de comprender.

                NurseFlow es una herramienta de apoyo a la consulta
                clínica y no reemplaza la valoración profesional
                ni los protocolos institucionales vigentes."""
            ),

            (
                "human",
                "Contexto:\n{contexto}\n\nPregunta: {pregunta}"
            )

        ])

        # Instanciar modelo Gemini
        modelo = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite"
        )

        # Formatear los fragmentos recuperados
        runnable_contexto = RunnableLambda(
            lambda chunks: formatear_contexto(chunks)[0]
        )


        """
        FLUJO DE EJECUCIÓN:

        1. Recibe la pregunta del usuario.
        2. Busca los protocolos relacionados en Chroma.
        3. Formatea los fragmentos recuperados.
        4. Incorpora el contexto y la pregunta al prompt.
        5. Envía la información a Gemini.
        6. Extrae la respuesta generada.
        """

        cadena = (

            {
                "contexto": retriever | runnable_contexto,
                "pregunta": RunnablePassthrough()
            }

            | prompt
            | modelo
            | StrOutputParser()

        )

        # Activar el sistema de trazabilidad
        handler = HandlerDeTrazabilidad()

        # Ejecutar la consulta
        resultado = cadena.invoke(

            pregunta,

            config={

                "callbacks": [handler],

                "metadata": {
                    "trace_id": trace_id_var.get()
                }

            }

        )

        # Mostrar la respuesta generada
        print("\n**** RESPUESTA NURSE FLOW ****")
        print(resultado)

        return resultado

    finally:

        # Restablecer el identificador de contexto
        trace_id_var.reset(token)


# EJECUCIÓN PRINCIPAL
if __name__ == "__main__":

    # Carpeta de la base de datos vectorial de NurseFlow
    CARPETA_DB = "vectorstore_nurseflow"

    # Cantidad de fragmentos que recuperará el sistema
    K = 3

    # Cargar base de datos vectorial
    vs = cargar_vectorstore(CARPETA_DB)

    # CONSULTAS DE EJEMPLO PARA NURSE FLOW

    # Control de signos vitales
    pregunta = "¿Cuáles son los valores normales de los signos vitales en adultos?"

    # Lesiones por presión (LPP)
    # pregunta = "¿Qué evalúa la escala de Braden?"

    # Prevención de LPP
    # pregunta = "¿Qué medidas se utilizan para prevenir lesiones por presión?"

    # Manejo de heridas
    # pregunta = "¿Qué características debo evaluar en una herida?"

    # Signos de infección
    # pregunta = "¿Cuáles son los signos de infección de una herida?"

    # Ejecutar consulta con trazabilidad
    ejecutar_consulta(
        vs,
        pregunta,
        K
    )
