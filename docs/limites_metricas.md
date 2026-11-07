# Límites de la métrica de evaluación

## Qué mide
Coincidencia léxica de tokens (palabras exactas y repeticiones) entre la respuesta generada por el asistente clínico y la referencia oficial, calculando precisión, cobertura y puntaje F1.

## Modos de falla conocidos
- **Inversión de conceptos clínicos (Negaciones o términos opuestos):** Respuestas que confunden taquicardia con bradicardia o taquipnea con bradipnea pueden obtener puntajes F1 bajos pero con un riesgo clínico extremo debido a la contradicción directa de valores vitales. Ejemplo: consulta sobre frecuencia respiratoria, f1=0.16.
- **Datos numéricos y umbrales erróneos:** Rangos de signos vitales (como presiones arteriales o pH cutáneo) alterados pueden puntuar moderadamente si comparten la estructura gramatical, ocultando un error factual peligroso.
- **Omisión de componentes de escalas clínicas:** Instrumentos de valoración (como la escala de Braden) con F1 bajo por simplificación excesiva de sus criterios principales.

## Muestra revisada
10 casos analizados a mano (los 5 con menor F1 y los 5 con mayor F1), seleccionados a partir de un conjunto total de 20 respuestas generadas el 2026-10-30.

## Recomendación de uso
Utilizar las métricas automáticas (F1) exclusivamente para comparar volúmenes de respuestas y desempeño global entre distintas versiones del modelo de lenguaje. **Revisar siempre de forma manual y rigurosa** cualquier respuesta generada por el pipeline que involucre rangos de signos vitales, clasificación de lesiones por presión (LPP), umbrales hemodinámicos o pautas de tratamiento clínico.