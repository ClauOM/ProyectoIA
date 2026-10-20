import os
import requests
from dotenv import load_dotenv

load_dotenv()

#Constantes
MODELO = "gemini-3.8-flash"
URL_BASE = "https://generativelanguage.googleapis.com/v1/models/"
API_KEY = os.getenv("GEMINI_API_KEY")

#función para crear la solicitud

def armar_peticion(pregunta): #Pregunta = confirma la conexión
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    url = f"{URL_BASE}{MODELO}:generateContent?key={API_KEY}"
    body = {
        "contents": [
        {
            "parts": [
            {
                "text": pregunta
            }
            ]
        }
        ]
    }
    return url, body

#función envía la petición

def enviar_peticion(url, body): 
    try:
        respuesta = requests.post(url, json=body)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos momentos.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Se agotó el tiempo. Intenta de nuevo en unos momentos")

    if respuesta.status_code !=200:
        raise RuntimeError(f"Error en la petición. Status code: {respuesta.status_code}")
    
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta no llegó en el formato esperado")


#función procesa y extrae dato

def extraer_texto(datos): #Gemini
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no recibe el texto generado en el lugar definitivo.")

def obtener_datos_de_prueba(pregunta): #pregunta = "confirma la conexión"
    url, body = armar_peticion(pregunta) #obtiene url y body
    #url= resultado de armar_peticion
    #body = resultado de armar_peticion
    datos = enviar_peticion(url, body)
    costo = calcular_costo(datos, 0.00000075, 0.00000375)
    print(f"Costo de la petición: ${costo:.6f} USD")
    return extraer_texto(datos)

#"def calcular_costo(datos: dict, precio_entrada: float, precio_salida: float) -> float:
def calcular_costo(datos, precio_entrada, precio_salida):
    #datos = {dict... "usageMetadata"}
    uso = datos["usageMetadata"]
    ...
    uso = {
        "promptTokenCount": 7,
        "candidatesTokenCount": 44,
        "totalTokenCount": 250,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 7
            }
        ],
        "thoughtsTokenCount": 199,
        "serviceTier": "standard"
    }

    tokens_entrada = uso["promptTokenCount"]
    tokens_salida = uso["candidatesTokenCount"]
    tokens_razonamiento = uso["thoughtsTokenCount"]
    costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida  )
    return costo 

try:
    print(obtener_datos_de_prueba("Confirma en una frase corta que esta conexión funciona"))
except (ValueError, RuntimeError) as error:
    print("No se pudo completar la operación: ", error)
