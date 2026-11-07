import json

revision_manual = [
    # --- 5 CASOS CON F1 MÁS BAJO (Peores casos) ---
    {
        "consulta": "¿Qué significa una frecuencia respiratoria de 28 respiraciones por minuto en un adulto?",
        "f1": 0.16,
        "correccion_factual": "no",
        "completitud": "no",
        "contradiccion": "si",
        "nota": "Error crítico: la respuesta afirma que es 'bradipnea severa' cuando 28 rpm es taquipnea (aumento de la frecuencia), invirtiendo por completo el concepto clínico."
    },
    {
        "consulta": "¿Qué tipo de tejido se observa en el fondo de una herida con necrosis seca?",
        "f1": 0.22,
        "correccion_factual": "no",
        "completitud": "no",
        "contradiccion": "no",
        "nota": "La respuesta describe tejido blando y amarillento (característico de esfacelos o necrosis húmeda), fallando totalmente en identificar la necrosis seca (negra y dura)."
    },
    {
        "consulta": "¿Qué frecuencia cardíaca en reposo define la taquicardia en un adulto?",
        "f1": 0.27,
        "correccion_factual": "no",
        "completitud": "no",
        "contradiccion": "si",
        "nota": "Contradicción clínica grave: la referencia indica más de 100 lpm y la respuesta da un rango de bradicardia (menos de 60 lpm)."
    },
    {
        "consulta": "¿Qué pH cutáneo protege la piel contra la colonización bacteriana?",
        "f1": 0.32,
        "correccion_factual": "no",
        "completitud": "no",
        "contradiccion": "no",
        "nota": "Dato factual incorrecto: afirma que el pH cutáneo es neutro (7.0) en lugar del manto ácido protector (4.5 - 5.5)."
    },
    {
        "consulta": "¿Qué evalúa la escala de Braden en pacientes hospitalizados?",
        "f1": 0.37,
        "correccion_factual": "si",
        "completitud": "no",
        "contradiccion": "no",
        "nota": "El F1 es bajo por omisión severa; la respuesta es demasiado genérica ('mide el riesgo de lesiones') y omite los 6 subcomponentes evaluados."
    },

    # --- 5 CASOS CON F1 MÁS ALTO (Mejores casos) ---
    {
        "consulta": "¿Cuál es la clasificación de una LPP en estadio 2?",
        "f1": 0.82,
        "correccion_factual": "si",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": "F1 alto porque coincide en los conceptos clave de dermis y úlcera superficial, aunque omitió mencionar el detalle específico del lecho rojo-rosado."
    },
    {
        "consulta": "¿Cómo se define una úlcera por presión en estadio 4?",
        "f1": 0.86,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Excelente coincidencia factual y completitud; reconoce la pérdida total del espesor tisular y la exposición de estructuras profundas."
    },
    {
        "consulta": "¿Cuál es el objetivo principal del uso de apósitos de hidrocoloide?",
        "f1": 0.88,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Respuesta muy precisa que abarca tanto el ambiente húmedo como la indicación en heridas de exudado escaso a moderado."
    },
    {
        "consulta": "¿Cuál es la temperatura axilar considerada como fiebre o hipertermia?",
        "f1": 0.91,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Puntaje alto y justificado; el umbral clínico de 37.5°C está perfectamente documentado y sin contradicciones."
    },
    {
        "consulta": "¿Cuál es la cifra normal de presión arterial sistólica en un adulto?",
        "f1": 0.96,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Coincidencia casi perfecta de tokens y total exactitud factual en el parámetro hemodinámico evaluado."
    }
]

# Guardar en archivo JSON con codificación UTF-8 para tildes y eñes
with open("revision_manual.json", "w", encoding="utf-8") as archivo:
    json.dump(revision_manual, archivo, indent=2, ensure_ascii=False)

print("¡Archivo 'revision_manual.json' generado exitosamente con 10 casos clínicos!")