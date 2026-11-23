
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter

# Texto de ejemplo aplicado a los protocolos clínicos de NurseFlow
texto = (
    "CONTROL DE SIGNOS VITALES: La frecuencia cardíaca normal en adultos "
    "en reposo es de 60 a 100 latidos por minuto. La frecuencia respiratoria "
    "normal es de 12 a 20 respiraciones por minuto.\n\n"

    "LESIONES POR PRESIÓN (LPP): La escala de Braden permite evaluar el riesgo "
    "de desarrollar lesiones por presión. Las medidas preventivas incluyen "
    "cambios de posición individualizados, higiene e hidratación de la piel.\n\n"

    "MANEJO DE HERIDAS: La valoración de una herida considera su localización, "
    "dimensiones, profundidad, tejido presente y cantidad de exudado. "
    "También se debe evaluar el estado de la piel alrededor de la lesión.\n\n"

    "SIGNOS DE INFECCIÓN EN HERIDAS: La presencia de secreción purulenta, "
    "aumento del dolor, eritema, calor local y fiebre pueden indicar una "
    "posible infección. Se debe informar al equipo clínico para su evaluación."
)


# Chunking de tamaño fijo (CharacterTextSplitter)
print("**** CHUNK FIJO - NURSE FLOW ****")

splitter_fijo = CharacterTextSplitter(
    separator=".",
    chunk_size=110,
    chunk_overlap=0
)

chunks_fijo = splitter_fijo.split_text(texto)

for i, chunk in enumerate(chunks_fijo):
    print(f"*** Chunk {i} ({len(chunk)} caracteres) ***")
    print(chunk)


print("\n**** CHUNK RECURSIVO - NURSE FLOW ****")

# Chunking recursivo (RecursiveCharacterTextSplitter)
splitter_recursivo = RecursiveCharacterTextSplitter(
    chunk_size=110,
    chunk_overlap=20
)

chunks_recursivo = splitter_recursivo.split_text(texto)

for i, chunk in enumerate(chunks_recursivo):
    print(f"*** Chunk {i} ({len(chunk)} caracteres) ***")
    print(chunk)
