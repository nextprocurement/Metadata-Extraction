import os
import re
import xml.etree.ElementTree as ET
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# -----------------------------
# ✅ Load environment variables
# -----------------------------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = API_KEY

# -----------------------------
# ✅ Initialize Flask
# -----------------------------
app = Flask(__name__)

# -----------------------------
# ✅ Load and initialize LLM and embeddings
# -----------------------------
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# -----------------------------
# ✅ Prompt Template
# -----------------------------
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

**Formato**:
- Usa texto literal del documento.
- Organiza las respuestas con encabezados claros para cada categoría.

Contexto: {context}

Pregunta: {question}
"""

prompt = PromptTemplate(template=prompt_template, input_variables=["context"])

# -----------------------------
# ✅ Helper functions
# -----------------------------

def format_content(text):
    """
    Formats the input text. If it's XML, extracts its content. Also cleans problematic characters.
    """
    try:
        # Validate and clean text
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
        text = text.strip()

        if text.startswith("<"):
            c_et = ET.fromstring(text)
            return ET.tostring(c_et, method='text', encoding='utf-8').decode('utf-8')
        
        return text
    except Exception:
        return text  # Return the original text if parsing fails

def create_documents(text):
    """
    Splits the text into manageable chunks.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=2048, chunk_overlap=256)
    chunks = splitter.split_text(text)
    return [Document(page_content=chunk) for chunk in chunks]

def divide_by_categories(texto):
    """
    Divides the result into specific categories.
    """
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
                resultado[key] = seccion.replace(f"### {encabezado}", "").strip()
    
    return resultado

def clean_text(text):
    """
    Cleans the text by removing unwanted characters.
    """
    return re.sub(r'[^\w\s.,-]', '', text)

# -----------------------------
# ✅ API Endpoint
# -----------------------------
@app.route("/extract_metadata", methods=["POST"])
def extract_metadata():
    """
    Endpoint to extract metadata from a text sent in the JSON request.
    """
    data = request.get_json()

    # Validate that the text was provided
    if not data or 'text' not in data or not isinstance(data['text'], str):
        return jsonify({"error": "Invalid input. Provide a valid 'text' field."}), 400

    text = data['text']

    formatted_text = format_content(text)
    if not formatted_text:
        return jsonify({"error": "Invalid text format"}), 400

    docs = create_documents(formatted_text)
    if not docs:
        return jsonify({"error": "Empty content after processing"}), 400

    # FAISS embeddings
    vector_storage = FAISS.from_documents(docs, embeddings)
    retriever = vector_storage.as_retriever()

    # Pipeline
    result_chain = (
        RunnableParallel(context=retriever, question=RunnablePassthrough())
        | prompt
        | model
        | StrOutputParser()
    )

    try:
        context = "\n".join([doc.page_content for doc in docs])
        result_text = result_chain.invoke(context)

        # ✅ Remove `procurement_id` and `doc_name` from the response
        result_dict = divide_by_categories(clean_text(result_text))

        return jsonify(result_dict), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 502

# -----------------------------
# ✅ Run Flask app
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
