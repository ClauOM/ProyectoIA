# Decisión de arquitectura: elección de modelo

Fecha de la comparación: martes 20 de octubre 2026
Nombre de mi miniaplicación: NurseFlow

## Modelo elegido

Elegí el modelo: Gemini 3.8 flash

Mi aplicación sirve para consultar, estructurar y validar protocolos clínicos automatizados (como control de signos vitales, valoración de lesiones por presión y pautas de curación de heridas) a través de una API para el personal de salud.

Los requisitos que necesito para cumplir son: 

- Requisito 1: Cumplimiento estricto de esquemas JSON (`responseSchema`) para enviar respuestas estructuradas directamente al backend sin errores de parseo.
- Requisito 2: Baja latencia en las respuestas para permitir consultas ágiles en flujos de atención clínica.
- Requisito 3: Alta precisión en la interpretación y extracción de datos médicos y guías de actuación.

## Diagrama de arquitectura

[Diagrama de arquitectura] = {docs/diagrama_arquitectura.png}

## Comparación de candidatos

Estas son las preguntas con las cuales se estudiaron ambos modelos:

- Preguntas y/o condiciones

1. ¿Mantiene la estructura JSON requerida en múltiples ejecuciones sin romper el esquema?
2. ¿Ofrece un tiempo de respuesta rápido e ininterrumpido adecuado para uso clínico?
3. ¿Comprende correctamente la terminología técnica de enfermería y parámetros de salud?

| Criterio | Gemini 3.8 flash | Gemini 3.5 flash |
| --- | --- | --- |
| Tarifa de entrada por uso de millon Tokens | $0.075 USD | $0.075 USD | 
| Tarifa de salida por eso de millon Tokens | $0.30 USD | $0.30 USD |
| Latencias de observadas en segundos | 1.1s, 1.3s, 1.2s | 1.8s, 2.4s, 1.9s |
| Latencias promedio en segundos | 1.2s | 2.0s |
| Calidad para nuestra miniaplicación | Excelente; 100% de consistencia en estructuras JSON y precisión en datos médicos. | Aceptable, pero con mayor variación en el formato de las claves JSON. |

Fuente de las tarifas:

- Modelo A: Documentación oficial de Google AI for Developers
- Modelo B: Documentación oficial de Google AI for Developers

Observacion para sobre las pruebas: Se realizaron rondas de 3 repeticiones por cada prompt del banco mediante un script de prueba automatizado para verificar la consistencia del JSON y la latencia real.

## Justificación

Elegí el modelo Gemini 3.8 flash porque en las pruebas de consistencia respondió siempre dentro de la estructura JSON esperada sin fallar el parseo y registró una latencia promedio menor (1.2 segundos), lo que asegura respuestas rápidas y confiables para las consultas de la API.

## Alternativa descartada y por qué

Descarté el o los modelos Gemini 3.5 flash (y Gemini 3.6 flash lite) porque presentaron mayor variabilidad en los tiempos de respuesta y en ocasiones alteraron la estructura de las claves esperadas, lo que obligaba a gestionar más excepciones de validación en el backend.