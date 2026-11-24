
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

# ==================================================
# ESTADO DEL DESPLIEGUE
# ==================================================

class EstadoDespliegue(TypedDict):

    huella_nueva: str
    aprobado: bool

# ==================================================
# NODO 1: PROPONER NUEVA VERSION
# ==================================================

def proponer(estado: EstadoDespliegue):

    print(
        "\nPropuesta de nueva versión del prompt NurseFlow:",
        estado["huella_nueva"]
    )

    return {}

# ==================================================
# NODO 2: SUPERVISION HUMANA
# ==================================================

def supervisar(estado: EstadoDespliegue):

    decision = interrupt({
        "motivo": (
            "Se requiere aprobación humana antes de activar "
            "una nueva versión del prompt clínico de NurseFlow."
        ),
        "huella_propuesta": estado["huella_nueva"]
    })

    return {"aprobado": decision}

# ==================================================
# NODO 3: APLICAR O RECHAZAR
# ==================================================

def aplicar(estado: EstadoDespliegue):

    if estado["aprobado"]:

        print(
            "\nVERSION APROBADA:",
            estado["huella_nueva"],
            "Puede continuar al proceso de despliegue."
        )

    else:

        print(
            "\nVERSION RECHAZADA:",
            estado["huella_nueva"],
            "Se mantiene la versión anterior del prompt."
        )

    return {}

# ==================================================
# CONSTRUIR EL GRAFO
# ==================================================

grafo = StateGraph(EstadoDespliegue)

grafo.add_node("proponer", proponer)
grafo.add_node("supervisar", supervisar)
grafo.add_node("aplicar", aplicar)

grafo.add_edge(START, "proponer")
grafo.add_edge("proponer", "supervisar")
grafo.add_edge("supervisar", "aplicar")
grafo.add_edge("aplicar", END)

# ==================================================
# COMPILAR CON MEMORIA
# ==================================================

app_despliegue = grafo.compile(
    checkpointer=InMemorySaver()
)

# ==================================================
# HUELLA OBTENIDA EN EL PASO 1
# ==================================================

huella = "5e03effc254b"

# ==================================================
# PRUEBA 1: SOLICITAR APROBACION
# ==================================================

print("\n===== PRUEBA DE APROBACION =====")

config = {
    "configurable": {
        "thread_id": "nurseflow-aprobacion-1"
    }
}

resultado = app_despliegue.invoke(
    {
        "huella_nueva": huella,
        "aprobado": False
    },
    config=config
)

print("\n1) Resultado al quedar interrumpido:")
print(resultado)

snapshot = app_despliegue.get_state(config)

print("\n2) Solicitud pendiente de aprobación:")
print(snapshot.interrupts[0].value)

# Reanudar con aprobación humana
resultado = app_despliegue.invoke(
    Command(resume=True),
    config=config
)

print("\n3) Resultado después de aprobar:")
print(resultado)

# ==================================================
# PRUEBA 2: RECHAZAR UNA NUEVA VERSION
# ==================================================

print("\n===== PRUEBA DE RECHAZO =====")

config2 = {
    "configurable": {
        "thread_id": "nurseflow-rechazo-2"
    }
}

resultado = app_despliegue.invoke(
    {
        "huella_nueva": huella,
        "aprobado": False
    },
    config=config2
)

print("\n4) Solicitud de segunda versión:")
print(resultado)

# Reanudar rechazando la propuesta
resultado = app_despliegue.invoke(
    Command(resume=False),
    config=config2
)

print("\n5) Resultado después de rechazar:")
print(resultado)