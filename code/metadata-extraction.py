import pandas as pd
import xml.etree.ElementTree as ET
import json
import re
import os
import sys
from datetime import datetime
import time
import logging
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# Get the range of data from the arguments
try:
    start_index = int(sys.argv[1])  # Data range start index
    end_index = int(sys.argv[2])    # End of data range index
except (IndexError, ValueError):
    print("Error: Se deben proporcionar los argumentos: índice de inicio y índice de fin.")
    sys.exit(1)

# Cargar claves API desde variables de entorno
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Cargar el DataFrame
df = pd.read_parquet("file.parq")

filtered_df = df[df['doc_name'].str.contains('Pliego_clausulas_administrativas', case=False, na=False)]
df_part = filtered_df.iloc[start_index:end_index]

if df_part.empty:
    print(f"No hay datos para procesar en el rango {start_index} a {end_index}.")
    sys.exit(1)

def format_content(xml_content):
    try:
        c_et = ET.fromstring(xml_content)
        content = ET.tostring(c_et, method='text', encoding='utf-8').decode('utf-8')
        return content
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None

df_part['formatted_content'] = df_part['content'].apply(lambda x: format_content(x.decode('utf-8')) if isinstance(x, bytes) else format_content(x))

model_id = "gpt-4o-mini"
model = ChatOpenAI(model=model_id, temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def create_documents(text):
    spliter = RecursiveCharacterTextSplitter(chunk_size=2048, chunk_overlap=256)
    chunks = spliter.split_text(text)
    return [Document(page_content=chunk) for chunk in chunks]

log_dir = '/folder/'
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, f'metadata_extraction_{start_index}_{end_index}.log'), filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

output_dir = '/folder/'
os.makedirs(output_dir, exist_ok=True)
initial_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = os.path.join(output_dir, f"resultados_{initial_timestamp}_{start_index}_{end_index}.json")

def save_results_to_json(data, filename=filename):
    if os.path.exists(filename):
        with open(filename, 'r+', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
            existing_data.extend(data)
            f.seek(0)
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
    else:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def clean_text(text):
    return re.sub(r'[^\w\s.,-]', '', text)

def divide_by_categories(texto):
    categorias = {
        "criterios_adjudicacion": "Criterios de adjudicación",
        "criterios_solvencia": "Criterios de solvencia",
        "condiciones_especiales": "Condiciones especiales de ejecución"
    }
    resultado = {key: "" for key in categorias}
    patron = "|".join(re.escape(v) for v in categorias.values())
    secciones = re.split(f"(?=### {patron})", texto)
    for seccion in secciones:
        for key, encabezado in categorias.items():
            if encabezado in seccion:
                contenido = seccion.replace(f"### {encabezado}", "").strip()
                resultado[key] = contenido
    return resultado

prompt_template = """
Eres un asistente experto en extraer información de documentos legales. Organiza la información exclusivamente en las categorías solicitadas. Asegúrate de no mezclar información entre secciones. 

1. **Criterios de adjudicación**:
   - Lista únicamente los criterios utilizados para adjudicar el contrato. Incluye subcriterios, puntajes, ponderaciones y criterios de desempate, si están presentes.
   - No incluyas información sobre solvencia o condiciones especiales.

2. **Criterios de solvencia**:
   - **Económica**: Detalla los requisitos financieros (capital, ingresos, etc.).
   - **Técnica**: Describe los requisitos de experiencia, proyectos similares o habilidades técnicas.
   - **Profesional**: Enumera licencias, certificaciones o cualificaciones profesionales necesarias.
   - Si no hay información de solvencia, escribe: "No existen criterios de solvencia en el documento".

3. **Condiciones especiales de ejecución**:
   - **Social**: Igualdad, inclusión o empleo de personas desfavorecidas.
   - **Ética**: Comercio justo, políticas anticorrupción.
   - **Medioambiental**: Sostenibilidad o eficiencia energética.
   - **Otro**: Cualquier condición no incluida en las anteriores.
   - Si no hay condiciones especiales, escribe: "No hay condiciones especiales de ejecución en el documento".

**Reglas**:
- Cada sección debe contener solo la información solicitada.
- Si un criterio o condición no está explícito en el documento, indícalo claramente.
- No incluyas información duplicada ni mezcles secciones.

**Formato**:
- Usa texto literal del documento.
- Organiza las respuestas con encabezados claros para cada categoría.

Contexto: {context}

Pregunta: {question}

"""
prompt = PromptTemplate(template=prompt_template, input_variables=["context"])

results_json = []
retry_wait_time = 3600

for index, row in df_part.iterrows():
    text_test = row['formatted_content']
    procurement_id = row['procurement_id']
    doc_name = row['doc_name']
    docs = create_documents(text_test)
    if not docs:
        continue
    vector_storage = FAISS.from_documents(docs, embeddings)
    retriever = vector_storage.as_retriever()
    result = RunnableParallel(context=retriever, question=RunnablePassthrough())
    parser = StrOutputParser()
    chain = result | prompt | model | parser
    context = "\n".join([doc.page_content for doc in docs])
    while True:
        try:
            result_text = chain.invoke(context)
            result_dict = {"procurement_id": procurement_id, "doc_name": doc_name, **divide_by_categories(clean_text(result_text))}
            results_json.append(result_dict)
            save_results_to_json(results_json)
            results_json = []
            break
        except Exception as e:
            logging.error(f"Error: {e}")
            if "rate_limit_exceeded" in str(e):
                time.sleep(retry_wait_time)
            else:
                break
if results_json:
    save_results_to_json(results_json)
