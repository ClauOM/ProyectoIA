BANCO_DE_PROMPTS = [
    {
        "nombre": "evaluar_signos_vitales",
        "pregunta": "PA adulto: reposo 5 min, normal <120/80 mmHg. Si sistólica >180 o diastólica >110 con síntomas, avisar al médico.",
        "system_instruction": (
            "Asistente clínico. Analiza el protocolo de signos vitales "
            "y devuelve un JSON estricto con las claves: "
            "'parametro_evaluado' (string), 'rango_normal' (string) y 'criterio_alerta' (string)."
        ),
        "ejemplo_usuario": "PA adulto: reposo 5 min, normal <120/80 mmHg. Si sistólica >180 o diastólica >110 con síntomas, avisar al médico.",
        "claves_esperadas": ["parametro_evaluado", "rango_normal", "criterio_alerta"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "parametro_evaluado": { "type": "STRING" },
                "rango_normal": { "type": "STRING" },
                "criterio_alerta": { "type": "STRING" }
            },
            "required": ["parametro_evaluado", "rango_normal", "criterio_alerta"]
        },
    },
    {
        "nombre": "clasificar_lpp",
        "pregunta": "Eritema no blanqueable en sacro, Braden alto. Requiere colchón antiescaras y cambios de posición cada 2 horas.",
        "system_instruction": (
            "Asistente clínico experto en piel. Analiza el caso de Lesión por Presión (LPP) "
            "y devuelve un JSON con las claves: "
            "'categoria_lpp' (string), 'medida_preventiva_clave' (string) y 'frecuencia_cambio_posicion' (string)."
        ),
        "ejemplo_usuario": "Eritema no blanqueable en sacro, Braden alto. Requiere colchón antiescaras y cambios de posición cada 2 horas.",
        "claves_esperadas": ["categoria_lpp", "medida_preventiva_clave", "frecuencia_cambio_posicion"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "categoria_lpp": { "type": "STRING" },
                "medida_preventiva_clave": { "type": "STRING" },
                "frecuencia_cambio_posicion": { "type": "STRING" }
            },
            "required": ["categoria_lpp", "medida_preventiva_clave", "frecuencia_cambio_posicion"]
        },
    },
    {
        "nombre": "plan_curacion_heridas",
        "pregunta": "Herida operatoria: lavado con suero 0.9%, gasa estéril y cinta hipoalergénica. Usar técnica estéril.",
        "system_instruction": (
            "Asistente clínico experto en heridas. Analiza el protocolo "
            "y devuelve un JSON con las claves: "
            "'tipo_herida' (string), 'insumos_requeridos' (lista de strings) y 'tipo_tecnica' (string: 'Limpia' o 'Estéril')."
        ),
        "ejemplo_usuario": "Herida operatoria: lavado con suero 0.9%, gasa estéril y cinta hipoalergénica. Usar técnica estéril.",
        "claves_esperadas": ["tipo_herida", "insumos_requeridos", "tipo_tecnica"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "tipo_herida": { "type": "STRING" },
                "insumos_requeridos": {
                    "type": "ARRAY",
                    "items": { "type": "STRING" }
                },
                "tipo_tecnica": { "type": "STRING" }
            },
            "required": ["tipo_herida", "insumos_requeridos", "tipo_tecnica"]
        },
    }
]