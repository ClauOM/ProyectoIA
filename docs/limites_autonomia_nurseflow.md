# Límites de autonomía: Asistente Clínico NurseFlow

## Herramientas y nivel de riesgo
* `consultar_base_clinica`: **bajo** (es una herramienta de solo lectura que busca protocolos locales de signos vitales, LPP y heridas; no modifica ningún dato ni ejecuta acciones externas).
* `evaluar_escala_braden`: **bajo** (realiza un cálculo matemático local con los puntajes entregados para estimar un nivel de riesgo parcial; no emite diagnósticos médicos definitivos).
* `actualizar_registro_clinico`: **alto** (escribe, modifica y persiste información directamente en las fichas clínicas oficiales de los pacientes; un error o alucinación del modelo en esta herramienta tiene un impacto crítico legal y sobre la seguridad asistencial).

## Herramientas que requieren aprobación humana
* `actualizar_registro_clinico`: Requiere aprobación humana obligatoria mediante la función interactiva `esperar_aprobacion` basada en validación por consola. La decisión se fundamenta en que el agente opera exclusivamente como apoyo a la gestión de enfermería y jamás debe alterar registros médicos sin la validación explícita del profesional responsable de turno.

## Revisión de trazas
* **Frecuencia:** Semanal en etapas de desarrollo y posterior a cada actualización de prompts del sistema.
* **Qué se busca:**
  * Uso repetido de la misma herramienta de consulta de forma consecutiva (bucles o ambigüedad en los argumentos).
  * Ausencia de registros de aprobación en las trazas de la herramienta `actualizar_registro_clinico`.
  * Respuestas finales del asistente que no coincidan con las observaciones entregadas por las herramientas (alucinaciones de datos clínicos).

## Qué hacer ante un comportamiento inesperado
1. **Desactivar temporalmente** la herramienta involucrada comentándola en la lista de herramientas del script de Python.
2. **Inspeccionar el archivo de trazas** (`docs/trazas_agente.jsonl`) utilizando un script de lectura para identificar la entrada del usuario y los argumentos erróneos.
3. **Reforzar las instrucciones del sistema (*system prompt*)** en el código del agente para delimitar de manera más estricta el dominio clínico.
4. **Actualizar los esquemas Pydantic** de las herramientas para asegurar validaciones estrictas en los datos de entrada.
5. **Reejecutar las pruebas** y comprobar el correcto funcionamiento y registro antes de volver a producción.