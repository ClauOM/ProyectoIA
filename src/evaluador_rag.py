
from datetime import date
from pathlib import Path
from rag_indexer import cargar_vectorstore


# =====================================================
# 1. MÉTRICA: PRECISIÓN
# =====================================================

def precision_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float:
    """
    De los chunks recuperados, ¿qué fracción es relevante?
    """

    if not ids_recuperados:
        return 0.0

    acertados = [
        i for i in ids_recuperados
        if i in ids_relevantes
    ]

    return len(acertados) / len(ids_recuperados)


# =====================================================
# 2. MÉTRICA: EXHAUSTIVIDAD (RECALL)
# =====================================================

def recall_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float | None:
    """
    De todos los chunks relevantes conocidos,
    ¿qué fracción logró recuperar el sistema?
    """

    if not ids_relevantes:
        return None

    acertados = [
        i for i in ids_recuperados
        if i in ids_relevantes
    ]

    return len(acertados) / len(ids_relevantes)


# =====================================================
# 3. MÉTRICA: F1 SCORE
# =====================================================

def f1_score(precision: float, recall: float | None) -> float:
    """
    Media armónica entre precisión y exhaustividad.
    """

    if recall is None or (precision + recall) == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)


# =====================================================
# 4. EVALUACIÓN DE RECUPERACIÓN
# =====================================================

def evaluar_recuperacion(retriever, casos: list[dict], k: int = 3):

    resultados = []

    for caso in casos:

        # Consultar al retriever
        chunks = retriever.invoke(caso["pregunta"])

        # Extraer IDs de los chunks recuperados
        ids_recuperados = [c.id for c in chunks]

        # Calcular métricas
        p = precision_at_k(
            ids_recuperados,
            caso["ids_relevantes"]
        )

        r = recall_at_k(
            ids_recuperados,
            caso["ids_relevantes"]
        )

        f1 = f1_score(p, r)

        resultados.append({
            "pregunta": caso["pregunta"],
            "ids_recuperados": ids_recuperados,
            "precision": p,
            "recall": r,
            "f1": f1
        })

    return resultados


# =====================================================
# 5. GUARDAR REPORTE
# =====================================================

def guardar_reporte(
    ruta_archivo: str,
    resultados: list[dict],
    k: int,
    chunk_size: int = 250,
    chunk_overlap: int = 35
):

    with open(ruta_archivo, "w", encoding="utf-8") as archivo:

        archivo.write("EVALUACIÓN RAG - NURSE FLOW\n")
        archivo.write(f"Fecha: {date.today()}\n")

        archivo.write(
            f"Configuración: k={k}, "
            f"chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}\n\n"
        )

        for r in resultados:

            recall_txt = (
                "n/a" if r["recall"] is None
                else f"{r['recall']:.2f}"
            )

            archivo.write(
                f"P={r['precision']:.2f} | "
                f"R={recall_txt} | "
                f"F1={r['f1']:.2f}\n"
            )

            archivo.write(f"Pregunta: {r['pregunta']}\n")
            archivo.write(
                f"IDs recuperados: {r['ids_recuperados']}\n\n"
            )

    print(f"\nReporte guardado en: {ruta_archivo}")


# =====================================================
# 6. EJECUCIÓN PRINCIPAL
# =====================================================

if __name__ == "__main__":

    # Configuración de NurseFlow
    CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
    CARPETA_DB = CARPETA_PROYECTO / "vectorstore_nurseflow"

    K = 3

    # Cargar base vectorial
    vs = cargar_vectorstore(str(CARPETA_DB))

    print("====================================")
    print(" EVALUACIÓN RAG - NURSE FLOW")
    print("====================================")

    print("Chunks disponibles:", vs._collection.count())

    if vs._collection.count() == 0:
        raise ValueError(
            "La base vectorial de NurseFlow está vacía."
        )

    # Crear retriever
    retriever = vs.as_retriever(
        search_kwargs={"k": K}
    )

    # =================================================
    # CASOS DE EVALUACIÓN
    # =================================================

    casos_evaluacion = [

        # CASO 1: SIGNOS VITALES
        {
            "pregunta": "¿Cuáles son los valores de referencia habituales de presión arterial, frecuencia cardíaca, frecuencia respiratoria, temperatura y saturación de oxígeno en adultos?",

            "ids_relevantes": {
                "eb6138b2-8cdc-4df5-847d-b28f2170ecd6",
                "74374c20-a23a-446a-90e9-04b4f91d37fe",
                "070bbfc8-c090-4098-bef8-2baddf16c12e",
                "f60a6839-fc1c-4847-80e8-d72c22589c00"
            }
        },

        # CASO 2: ALTERACIONES DE SIGNOS VITALES
        {
            "pregunta": "¿Qué acciones debe realizar enfermería cuando identifica valores alterados en el control de signos vitales?",

            "ids_relevantes": {
                "d76b064e-248a-45e4-a5d2-4442a460f5d4",
                "b0bfa0da-6e2b-4fdf-aa5f-8fce817610e9"
            }
        },

        # CASO 3: PREVENCIÓN DE LPP
        {
            "pregunta": "¿Qué medidas preventivas debe implementar enfermería para evitar lesiones por presión y cómo se evalúa el riesgo mediante la escala de Braden?",

            "ids_relevantes": {
                "d3a1af1d-3277-4431-9ee1-bc67fc5025d0",
                "c657962c-7729-487b-8de0-abc8d2d47718",
                "c100ec49-334b-4d04-982e-f9f26b50a430"
            }
        },

        # CASO 4: CLASIFICACIÓN DE LPP
        {
            "pregunta": "¿Cómo se clasifican las lesiones por presión desde el estadio 1 hasta el estadio 4 y cuáles son las lesiones no clasificables y de tejidos profundos?",

            "ids_relevantes": {
                "e0e88487-6e87-4606-a52d-ddf5c9514f55",
                "1d915302-db0b-431a-b784-391d4eee7938",
                "8f72c418-4848-4d9b-ba4b-0e1baeb807ef",
                "90e3051f-ce4e-46e8-8b37-68e22b177e78"
            }
        },

        # CASO 5: VALORACIÓN DE HERIDAS
        {
            "pregunta": "¿Qué aspectos debe evaluar enfermería al realizar la valoración de una herida, incluyendo localización, dimensiones, lecho, exudado, bordes y dolor?",

            "ids_relevantes": {
                "58e8aa76-3ade-42b0-91d1-0f8f0587959b",
                "6929d698-f096-4340-9fdd-289e8f7f7ba0",
                "7cf7a99c-9cb0-473e-be3b-67def3afd3db"
            }
        },

        # CASO 6: PROCEDIMIENTO DE CURACIÓN
        {
            "pregunta": "¿Cuáles son los pasos generales que debe seguir enfermería para realizar una curación de heridas?",

            "ids_relevantes": {
                "11250bfc-4ee9-4dd8-9fae-b93b357a8d6f",
                "d9934684-66d6-4933-8aff-8a40ac6faa19",
                "6231e445-b6f6-4bd3-9909-b5d5d72621fb",
                "0eae89a3-e600-4b67-9751-6e6e8f118135"
            }
        },

        # CASO 7: SIGNOS DE INFECCIÓN
        {
            "pregunta": "¿Cuáles son los signos de alerta que pueden indicar infección o deterioro de una herida y qué debe hacer enfermería?",

            "ids_relevantes": {
                "02ae95d1-8798-4414-b5dc-d732de2f7991",
                "c8a4e2df-78df-4155-93c3-45f33754301e",
                "7f21b832-f60f-48fe-a408-dbbfdfccf327"
            }
        },

        # CASO 8: REGISTRO CLÍNICO
        {
            "pregunta": "¿Qué información mínima debe quedar registrada después de una intervención de enfermería?",

            "ids_relevantes": {
                "478b50e0-6f91-4676-959d-d3c08e66d58f",
                "e28c2b4c-f80c-4f50-93a2-bb8a2c5bdf5f",
                "282bba69-bbb9-4941-99f5-475d638cbde3",
                "ce34d10f-5ef1-4d5c-9089-027d395c4aa2",
                "1903e00a-ece2-480e-8dfb-ec58ed42e6cc"
            }
        },

        # CASO 9: SEGURIDAD Y RESPONSABILIDAD CLÍNICA
        {
            "pregunta": "¿Qué criterios de seguridad y responsabilidad clínica debe respetar NurseFlow al entregar recomendaciones de enfermería?",

            "ids_relevantes": {
                "09f3c8e1-5b3c-416e-a6ac-2299e75e77bf",
                "cb06eaab-52db-4b9b-9c64-2c05b8d94809",
                "0c19eb83-ea1c-462f-8aa6-7cdf15edce04",
                "adc869fc-dfee-483a-b94f-a7c927582299"
            }
        }
    ]

    # Ejecutar evaluación
    resultados = evaluar_recuperacion(
        retriever,
        casos_evaluacion,
        K
    )

    # Mostrar resultados
    print("\n========== RESULTADOS ==========")

    for resultado in resultados:

        print("\nPregunta:", resultado["pregunta"])
        print("IDs recuperados:", resultado["ids_recuperados"])
        print(f"Precisión: {resultado['precision']:.2f}")
        print("Exhaustividad:", resultado["recall"])
        print(f"F1 Score: {resultado['f1']:.2f}")

    # Guardar reporte
    guardar_reporte(
        str(CARPETA_PROYECTO / "resultados_evaluacion_rag_nurseflow.txt"),
        resultados,
        K,
        chunk_size=250,
        chunk_overlap=35
    )

    print("\nEvaluación RAG de NurseFlow finalizada.")
