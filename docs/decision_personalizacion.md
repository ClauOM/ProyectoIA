# Decisión de personalización: NurseFlow

## 1. El problema

NurseFlow es un asistente de consulta de protocolos y procedimientos de enfermería. Su objetivo es entregar respuestas claras y fundamentadas sobre control de signos vitales, prevención de lesiones por presión y valoración y manejo de heridas.

El principal desafío es que las respuestas deben basarse en información clínica documentada, recuperar los fragmentos pertinentes y evitar entregar recomendaciones que no estén respaldadas por los protocolos disponibles.

## 2. Resultado del método de decisión

Para aplicar el método de decisión se evaluaron los cinco criterios establecidos:

- **Información cambia seguido:** False. No se ha comprobado que las fuentes clínicas utilizadas se actualicen al menos una vez al mes.
- **Problema de formato o tono:** False. Todavía no se ha realizado una evaluación formal de 20 respuestas.
- **Dataset grande y de calidad:** False. Actualmente se cuenta con 10 ejemplos etiquetados, cantidad inferior a los 200 requeridos por el criterio.
- **Presupuesto limitado o iterar rápido:** True. El proyecto tiene un presupuesto limitado para realizar entrenamientos y necesita evitar costos adicionales de personalización.
- **Necesita múltiples variantes:** False. Actualmente NurseFlow requiere una sola versión del asistente.

**Resultado de los puntajes:**

- RAG: 2 puntos.
- PEFT: 1 punto.
- Fine-tuning completo: 0 puntos.

La técnica mejor evaluada por el método de decisión es RAG.

## 3. Técnica elegida y por qué

La técnica elegida para NurseFlow es **RAG (Retrieval-Augmented Generation)**.

Esta decisión se fundamenta en que el proyecto necesita consultar información clínica contenida en documentos y protocolos de enfermería, recuperar los fragmentos relacionados con cada pregunta y utilizarlos como contexto para generar respuestas.

Además, NurseFlow ya cuenta con una implementación funcional de RAG utilizando Gemini para generar embeddings, Chroma como base de datos vectorial y un modelo Gemini para elaborar las respuestas.

Se descarta por el momento el fine-tuning completo y PEFT debido a que el proyecto cuenta con un presupuesto limitado y todavía no dispone de un dataset suficientemente grande y validado para justificar el entrenamiento personalizado.

RAG permite actualizar o incorporar nuevos documentos al sistema sin tener que entrenar nuevamente el modelo, lo que resulta conveniente para esta etapa del proyecto.

## 4. Qué necesitaría para ejecutarla

NurseFlow ya cuenta con una implementación inicial de RAG y un corpus documental indexado.

Actualmente se dispone de:

- 1 manual de protocolos y procedimientos de enfermería: `manual_de_usuario.txt`.
- 46 fragmentos o chunks almacenados en Chroma.
- Una base vectorial denominada `vectorstore_nurseflow`.
- Un sistema de recuperación de información que permite consultar los protocolos.
- Un proceso de generación de respuestas utilizando Gemini.

Como trabajo futuro, se considera incorporar más documentos clínicos y protocolos institucionales validados, revisar periódicamente su vigencia y ampliar el corpus documental de acuerdo con las necesidades del proyecto.

No se considera necesario realizar fine-tuning ni PEFT en esta etapa. La estrategia será continuar desarrollando y evaluando RAG, priorizando la calidad de las fuentes, la recuperación de información y la seguridad de las respuestas clínicas.