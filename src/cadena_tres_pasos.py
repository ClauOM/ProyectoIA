"""Módulo de procesamiento en cadena de tres pasos para NurseFlow.
Extrae información clínica clave, la simplifica y la estructura en viñetas de acción.
"""

import argparse
import json
from pathlib import Path

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def construir_cadena(modelo):
    """Conecta tres tareas clínicas secuenciales usando LCEL."""
    
    # Paso 1: Extracción estricta de hallazgos/recomendaciones clínicas
    plantilla_extraer = PromptTemplate.from_template(
        "Eres un asistente clínico experto. Extrae los tres puntos o indicaciones "
        "clínicas más relevantes del siguiente texto normativo o protocolo. "
        "No agregues interpretaciones externas:\n\n{texto}"
    )

    # Paso 2: Traducción a lenguaje claro (accesible para pacientes o familiares)
    plantilla_simplificar = PromptTemplate.from_template(
        "Traduce las siguientes indicaciones clínicas a un lenguaje claro, "
        "empático y sencillo para que un paciente o cuidador sin formación "
        "médica pueda comprenderlas perfectamente, conservando el rigor técnico:\n\n{ideas}"
    )

    # Paso 3: Formateo final en viñetas operativas
    plantilla_formatear = PromptTemplate.from_template(
        "Organiza la explicación anterior en un máximo de tres viñetas claras "
        "de acción o cuidados domiciliarios. "
        "No agregues introducciones ni conclusiones:\n\n{explicacion}"
    )

    # Construcción de la cadena LCEL
    extraer = plantilla_extraer | modelo | StrOutputParser()
    simplificar = plantilla_simplificar | modelo | StrOutputParser()
    formatear = plantilla_formatear | modelo | StrOutputParser()

    cadena = (
        extraer
        | (lambda resultado: {"ideas": resultado})
        | simplificar
        | (lambda resultado: {"explicacion": resultado})
        | formatear
    )

    return cadena


TEXTO_EJEMPLO = """
    Norma de prevención de IAAS: El lavado de manos clínico debe realizarse
    antes y después de la atención de cada paciente mediante fricción con
    preparado de base alcohólica durante 20 a 30 segundos, o con agua y jabón
    antiséptico si las manos están visiblemente sucias o contaminadas con fluidos.
    """


def construir_modelo_simulado():
    """Respuestas prefijadas para pruebas unitarias sin consumir API de Gemini."""
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    respuestas = iter([
        "SIMULADO: 1. Higiene de manos antes y después. 2. Duración 20-30s con alcohol. 3. Agua y jabón si hay suciedad visible.",
        "SIMULADO: Explicación amigable de la norma de higiene para cuidadores.",
        "- SIMULADO: Lavar o desinfectar manos antes y después de cada paciente.\n- SIMULADO: Usar alcohol gel por 30 segundos.\n- SIMULADO: Usar agua y jabón si hay suciedad visible.",
    ])

    def responder(prompt):
        return AIMessage(content=next(respuestas))

    return RunnableLambda(responder)


def construir_modelo_real():
    """Configura el modelo real de Gemini para NurseFlow."""
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI

    # Carga el archivo .env desde la raíz del proyecto
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)
    
    # Usando el modelo actual configurado en tus entornos
    return ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulado", action="store_true", help="Ejecuta sin llamada a la API.")
    parser.add_argument("--archivo", type=Path, help="Ruta al archivo clínico o protocolo en formato TXT.")
    parser.add_argument("--salida", type=Path, help="Ruta para guardar el registro estructurado en JSON.")
    args = parser.parse_args(argv)

    texto = TEXTO_EJEMPLO
    if args.archivo is not None:
        try:
            texto = args.archivo.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            parser.error(f"No se pudo leer el archivo de protocolo: {error}")
            
    if not texto.strip():
        parser.error("El contenido del texto clínico no puede estar vacío.")
        
    if args.salida is not None and args.archivo is not None:
        if args.salida.resolve() == args.archivo.resolve():
            parser.error("La ruta de salida debe ser distinta a la del archivo de entrada.")

    modo = "simulado" if args.simulado else "real"
    if args.simulado:
        print("[NurseFlow] MODO SIMULADO: Usando respuestas predefinidas.")
        modelo = construir_modelo_simulado()
    else:
        print("[NurseFlow] MODO REAL: Consultando motor Gemini de Google GenAI.")
        modelo = construir_modelo_real()

    cadena = construir_cadena(modelo)
    resultado = cadena.invoke({"texto": texto})
    
    print("\n--- RESULTADO NURSEFLOW ---")
    print(resultado)
    print("---------------------------\n")

    if args.salida is not None:
        registro = {
            "modulo": "cadena_tres_pasos_clinico",
            "modo": modo,
            "archivo_entrada": str(args.archivo.resolve()) if args.archivo else None,
            "texto_entrada": texto,
            "resultado_procesado": resultado,
        }
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(
            json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Registro guardado exitosamente en: {args.salida}")


if __name__ == "__main__":
    main()
