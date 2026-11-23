from pathlib import Path
from dotenv import load_dotenv  # Importa variables de entorno
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Función para dividir (chunking)
from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Embedding de Gemini
from langchain_chroma import Chroma  # Chroma = vector store
from langchain_core.documents import Document
import os

load_dotenv()

"""
Auditar localmente que no haya chunks vacíos ni duplicados antes de gastar tokens en embeddings.
"""

def verificar_integridad(chunks, corpus_original):

    # Recorrer todos los chunks y buscar fragmentos vacíos
    vacios = [i for i, c in enumerate(chunks) if not c.page_content.strip()]

    # Extraer el texto de cada objeto
    textos = [c.page_content for c in chunks]

    # Set elimina valores repetidos
    hay_duplicados = len(textos) != len(set(textos))

    if vacios:
        raise ValueError(f"Se detectaron chunks vacíos en los índices: {vacios}")

    if hay_duplicados:
        print("Advertencia: Se detectaron chunks duplicados en el corpus.")

    # Sumar caracteres de los chunks y del corpus original
    total_chars_chunks = sum(len(c.page_content) for c in chunks)
    total_chars_corpus = sum(
        len(d.page_content) if isinstance(d, Document) else len(d)
        for d in corpus_original
    )

    print(
        f"Integridad OK | Chunks: {len(chunks)} | "
        f"Caracteres (corpus/chunks): {total_chars_corpus}/{total_chars_chunks}"
    )


"""
Recibir un corpus/texto, dividirlo, calcular el embedding
y guardar el corpus en nuestro vector store.
"""

def indexar_corpus(corpus, persist_directory, chunk_size=200, chunk_overlap=30, es_documento=False):

    # Dividir en fragmentos más pequeños el corpus/texto
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    # División del contenido
    if not es_documento:
        chunks = splitter.create_documents(corpus)
    else:
        chunks = splitter.split_documents(corpus)

    # Verificar integridad de los fragmentos
    verificar_integridad(chunks, corpus)

    # Generar embeddings utilizando Gemini
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    # Guardar los documentos en Chroma
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    return vector_store


"""
Función que abre/carga la carpeta existente del disco para leerla.
No necesita volver a indexar los documentos.
"""

def cargar_vectorstore(persist_directory):

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    return Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )


def eliminar_por_ids(vectorstore, ids_a_borrar):

    vectorstore.delete(ids=ids_a_borrar)


def agregar_documentos(vectorstore, nuevos_textos, prefijo_id, chunk_size=200, chunk_overlap=30):

    # Dividir los nuevos documentos en fragmentos
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    nuevo_chunks = splitter.create_documents(nuevos_textos)

    # Crear los IDs de los nuevos fragmentos
    ids_nuevos = [
        f"{prefijo_id}_{i}" for i in range(len(nuevo_chunks))
    ]

    # Verificar integridad
    verificar_integridad(nuevo_chunks, nuevos_textos)

    try:
        vectorstore.add_documents(
            ids=ids_nuevos,
            documents=nuevo_chunks
        )

        print(
            f"Agregados {len(nuevo_chunks)} chunks "
            f"con el prefijo {prefijo_id}"
        )

    except Exception as error:
        print("Error al agregar nuevos documentos: ", error)


"""
Realiza la búsqueda semántica (por significado, NO POR PALABRA EXACTA)
en el vector store.
Devuelve una lista con los resultados semejantes.
"""

def buscar_similares(vectorstore, pregunta, k=3):

    # Gemini transforma la pregunta en vectores numéricos (embeddings)
    # Chroma recupera los fragmentos con mayor similitud semántica
    resultados = vectorstore.similarity_search_with_score(
        query=pregunta,
        k=k
    )

    # Iterar para imprimir los resultados recuperados
    for i, (doc, score) in enumerate(resultados, start=1):

        print(f"[Resultado {i}] Distancia (score): {score:.4f}")
        print(f"Contenido: {doc.page_content}")

        if doc.metadata:
            print(f"Metadata: {doc.metadata}")

    return resultados


def formatear_contexto(chunks_recuperados):

    lineas = []
    citas = {}

    """
    Ejemplo de información recuperada:

    [
        {
            "page_content": "La frecuencia cardíaca normal en adultos
            en reposo es de 60 a 100 latidos por minuto.",
            "metadata": {
                "fuente": "signos_vitales.txt"
            }
        }
    ]
    """

    for i, doc in enumerate(chunks_recuperados, start=1):

        # Obtener la fuente del protocolo
        fuente = doc.metadata.get("fuente", "desconocida")

        lineas.append(f"[{i}] {doc.page_content}")

        citas[i] = fuente

    contexto = "\n\n".join(lineas)

    return contexto, citas


"""
Inspeccionar los IDs de cada chunk almacenado en Chroma.
"""

def inspeccionar_chunks(vectorstore):

    datos = vectorstore.get()

    total = len(datos["ids"])

    print(f"-- INVENTARIO DE CHUNKS EN NURSEFLOW (Total: {total}) --")

    for i, (chunk_id, texto, meta) in enumerate(
        zip(datos["ids"], datos["documents"], datos["metadatas"]),
        start=1
    ):

        print(f"[{i}] ID: {chunk_id}")
        print(f"Fuente/Meta: {meta}")

        resumen = texto.replace("\n", " ")

        print(f"Contenido: {resumen[:100]}...")



if __name__ == "__main__":

    # Obtener la carpeta principal del proyecto
    CARPETA_PROYECTO = Path(__file__).resolve().parent.parent

    # Ruta del manual de protocolos de NurseFlow
    RUTA_MANUAL = CARPETA_PROYECTO / "manual_de_usuario.txt"

    # Carpeta donde se almacenará la base vectorial
    CARPETA_DB = CARPETA_PROYECTO / "vectorstore_nurseflow"

    print("========== NURSE FLOW ==========")

    # Verificar que exista el manual
    if not RUTA_MANUAL.exists():
        raise FileNotFoundError(
            f"No se encontró el manual: {RUTA_MANUAL}"
        )

    # Leer el manual de protocolos
    with open(RUTA_MANUAL, "r", encoding="utf-8") as f:
        contenido = f.read()

    if not contenido.strip():
        raise ValueError("El manual de NurseFlow está vacío.")

    print("Manual encontrado:", RUTA_MANUAL.name)
    print("Caracteres del manual:", len(contenido))

    # Crear documento con metadatos
    documentos = [
        Document(
            page_content=contenido,
            metadata={
                "fuente": "manual_de_usuario.txt",
                "sistema": "NurseFlow",
                "area": "Enfermería"
            }
        )
    ]

    # Cargar la base vectorial
    vs = cargar_vectorstore(str(CARPETA_DB))

    # Comprobar si ya contiene documentos
    cantidad = vs._collection.count()

    if cantidad == 0:

        print("\nLa base está vacía. Iniciando indexación...")

        vs = indexar_corpus(
            corpus=documentos,
            persist_directory=str(CARPETA_DB),
            chunk_size=250,
            chunk_overlap=35,
            es_documento=True
        )

        print("Indexación completada.")

    else:

        print("\nLa base ya contiene documentos.")
        print("Se utilizará la base existente.")

    # Mostrar cantidad de chunks
    print("\nChunks almacenados:", vs._collection.count())

    # Mostrar los IDs almacenados
    datos = vs.get()

    print("\nIDs almacenados:")
    print(datos["ids"])

    # Consultar los protocolos de enfermería
    pregunta = (
        "¿Cuáles son los valores normales de los signos "
        "vitales en adultos?"
    )

    print("\n========== BÚSQUEDA SEMÁNTICA ==========")

    chunks_recuperados = buscar_similares(
        vs,
        pregunta,
        k=3
    )

    # Crear retriever
    retriever = vs.as_retriever(
        search_kwargs={"k": 3}
    )

    # Recuperar documentos
    resultados = retriever.invoke(pregunta)

    print("\n========== RESULTADOS RECUPERADOS ==========")

    for resultado in resultados:
        print("\n", resultado.page_content)

    # Formatear contexto y obtener citas
    contexto, citas = formatear_contexto(resultados)

    print("\n========== CONTEXTO FORMATEADO ==========")
    print(contexto)

    print("\n========== DICCIONARIO DE CITAS ==========")
    print(citas)

    # Inspeccionar los fragmentos almacenados
    print("\n========== INVENTARIO DE CHUNKS ==========")
    inspeccionar_chunks(vs)

    print("\n========== FIN NURSE FLOW ==========")
