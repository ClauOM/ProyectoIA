import json
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from banco import BANCO_DE_PROMPTS
from consumir_gemini import armar_peticion, enviar_peticion, extraer_texto, parsear_respuesta_json

registro = {}

try:

    for prompt in BANCO_DE_PROMPTS:
        exitos = 0
        intentos = 3
        for intento in range(intentos):
            url, body = armar_peticion(
                prompt["pregunta"],
                "gemini-3.6-flash", 
                prompt["ejemplo_usuario"], 
                prompt["system_instruction"], 
                prompt["response_schema"]
                )
            respuesta = enviar_peticion(url, body)
            texto = extraer_texto(respuesta)
            try:
                datos = parsear_respuesta_json(texto, prompt["claves_esperadas"])
                exitos += 1
                print(f"Respuesta válida: {datos}")
            except ValueError as error:
                print(f"intento {intento + 1} falló: {error}")
                time.sleep(3)

        print(f"{prompt["nombre"]}: {exitos}/{intentos} respuestas válidas")
        registro[prompt["nombre"]] = {"exitos": exitos, "intentos": intentos}
    #Cuando termine de recorrer los prompts, guardamos el registro en un archivo resultados.json
    with open("src/prompts/registro_resultados.json", "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)

except (ValueError, RuntimeError) as error:
    print(f"No se pudo completar la operación: {error}")
