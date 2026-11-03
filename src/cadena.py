from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo
from langchain_core.prompts import PromptTemplate #Plantilla -> Promp dinámico
from langchain_core.output_parsers import StrOutputParser #Parsea la respuesta y la transforma en solo texto
from langchain_core.prompts import ChatPromptTemplate #Plantilla que incluye rol del sistema e instrucción

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
#respuesta = modelo.invoke("¿Qué es un token?")
#print(respuesta.content)

#f-strings
plantilla = PromptTemplate.from_template(
    "Explica el concepto de {tema} en un parrafo, para alguien que recién comienza en {area}."
)

#prompt = plantilla.invoke(
#    {"tema": "tokenización", "area": "procesamiento de texto"}
#)

#print(prompt.text)

cadena_simple = plantilla | modelo | StrOutputParser()

respuesta = cadena_simple.invoke(
    {"tema": "embeddings", "area": "búsqueda semántica"}
)

print(respuesta)

plantilla_conrol = ChatPromptTemplate.from_messages([
    ("system", "Eres un experto en el área correspondiente, vas a responder siempre con texto simple ára el usurio."),
    ("human", "Explica el concepto de {tema} en un párrafo, para alguien que recién comienza en el {area}")
])