
# ==================================================
# MATRIZ DE RIESGOS - NURSEFLOW
# ==================================================

# --------------------------------------------------
# CALCULAR PUNTAJE
# --------------------------------------------------

def puntaje_riesgo(probabilidad, impacto):

    return probabilidad * impacto

# --------------------------------------------------
# CLASIFICAR RIESGO
# --------------------------------------------------

def categoria_riesgo(puntaje):

    if puntaje >= 15:
        return "CRITICO"

    if puntaje >= 9:
        return "ALTO"

    if puntaje >= 4:
        return "MEDIO"

    return "BAJO"

# --------------------------------------------------
# IDENTIFICAR SI ESTA AL LIMITE
# --------------------------------------------------

def esta_en_el_limite(probabilidad, impacto):

    categoria_actual = categoria_riesgo(
        puntaje_riesgo(probabilidad, impacto)
    )

    vecinos = [
        (probabilidad + 1, impacto),
        (probabilidad - 1, impacto),
        (probabilidad, impacto + 1),
        (probabilidad, impacto - 1)
    ]

    for p2, i2 in vecinos:

        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue

        categoria_vecina = categoria_riesgo(
            puntaje_riesgo(p2, i2)
        )

        if categoria_vecina != categoria_actual:
            return True

    return False

# ==================================================
# RIESGOS IDENTIFICADOS EN NURSEFLOW
# ==================================================

mis_riesgos = [

    {
        "riesgo": (
            "Inyección de prompt mediante un documento "
            "recuperado desde la base vectorial"
        ),
        "probabilidad": 4,
        "impacto": 4,
        "mitigacion": (
            "Detección de patrones sospechosos y delimitación "
            "del contexto recuperado"
        )
    },

    {
        "riesgo": (
            "Uso de un protocolo de enfermería desactualizado "
            "que entregue información clínica no vigente"
        ),
        "probabilidad": 3,
        "impacto": 5,
        "mitigacion": (
            "Revisión de fecha y vigencia del archivo "
            "registro_usuario.txt antes de actualizar la "
            "base de conocimiento. Control manual por formalizar."
        )
    },

    {
        "riesgo": (
            "Recuperación de documentos insuficientes o "
            "no pertinentes para responder una consulta clínica"
        ),
        "probabilidad": 4,
        "impacto": 3,
        "mitigacion": (
            "Recuperación RAG desde Chroma y revisión de "
            "trazas y cantidad de documentos recuperados "
        )
    },

    {
        "riesgo": (
            "Generación de una respuesta clínica con información "
            "que no está respaldada por el contexto recuperado"
        ),
        "probabilidad": 3,
        "impacto": 4,
        "mitigacion": (
            "Instrucciones del prompt para responder solo "
            "con el contexto, reconocer información insuficiente "
            "y citar fuentes"
        )
    },

    {
        "riesgo": (
            "Exposición de información confidencial de pacientes "
            "en consultas o registros del sistema"
        ),
        "probabilidad": 2,
        "impacto": 5,
        "mitigacion": (
            "Evitar incorporar datos identificables de pacientes "
            "en las pruebas y revisar los registros de trazabilidad. "
            "Control de privacidad por reforzar."
        )
    },

    {
        "riesgo": (
            "Activación de una nueva versión del prompt "
            "sin revisión ni autorización humana"
        ),
        "probabilidad": 2,
        "impacto": 2,
        "mitigacion": (
            "Registro de huellas de versiones y aprobación humana "
            "mediante interrupt() de LangGraph"
        )
    }

]

# ==================================================
# CALCULAR PUNTAJE Y CATEGORIA DE CADA RIESGO
# ==================================================

for r in mis_riesgos:

    r["puntaje"] = puntaje_riesgo(
        r["probabilidad"],
        r["impacto"]
    )

    r["categoria"] = categoria_riesgo(
        r["puntaje"]
    )

    r["al_limite"] = esta_en_el_limite(
        r["probabilidad"],
        r["impacto"]
    )

# ==================================================
# MOSTRAR MATRIZ ORDENADA POR PUNTAJE
# ==================================================

print("\n===== MATRIZ DE RIESGOS NURSEFLOW =====\n")

for r in sorted(
    mis_riesgos,
    key=lambda x: -x["puntaje"]
):

    marca = " [AL LIMITE]" if r["al_limite"] else ""

    print(
        f"{r['categoria']:8} "
        f"({r['puntaje']:2}) - "
        f"{r['riesgo']}{marca}"
    )

    print(
        f"  Probabilidad: {r['probabilidad']}"
    )

    print(
        f"  Impacto: {r['impacto']}"
    )

    print(
        f"  Mitigación: {r['mitigacion']}"
    )

    print()

# ==================================================
# SUPERVISION HUMANA PARA RIESGOS ALTOS Y CRITICOS
# ==================================================

supervision_riesgos = {

    "Inyección de prompt mediante un documento recuperado desde la base vectorial":
        "Revisar manualmente el documento marcado antes de incorporarlo nuevamente a la base.",

    "Uso de un protocolo de enfermería desactualizado que entregue información clínica no vigente":
        "Solicitar revisión de vigencia por un profesional responsable antes de utilizar el protocolo.",

    "Recuperación de documentos insuficientes o no pertinentes para responder una consulta clínica":
        "Revisar los documentos recuperados y no utilizar la respuesta como orientación clínica hasta verificar la fuente.",

    "Generación de una respuesta clínica con información que no está respaldada por el contexto recuperado":
        "Revisión de la respuesta por un profesional de enfermería antes de utilizarla en una decisión clínica.",

    "Exposición de información confidencial de pacientes en consultas o registros del sistema":
        "Revisión del incidente y de los registros por la persona responsable de privacidad o seguridad."
}

print("\n===== SUPERVISION DE RIESGOS ALTOS Y CRITICOS =====\n")

for r in mis_riesgos:

    if r["categoria"] in ("ALTO", "CRITICO"):

        print("Riesgo:", r["riesgo"])

        print(
            "Acción de supervisión:",
            supervision_riesgos[r["riesgo"]]
        )

        print()

# ==================================================
# IDENTIFICAR RIESGOS QUE REQUIEREN REVISION
# ==================================================

print("\n===== RIESGOS AL LIMITE DE SU CATEGORIA =====\n")

for r in mis_riesgos:

    if r["al_limite"]:

        print(
            "Revisar con otra persona:",
            r["riesgo"]
        )

print("\n===== FIN DE LA MATRIZ DE RIESGOS =====")