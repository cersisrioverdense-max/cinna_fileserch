import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from google import genai
from google.genai import types
from pypdf import PdfReader
import uuid

def get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    return genai.Client(api_key=api_key)

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        client = get_genai_client()
        model = 'gemini-embedding-2'
        embeddings = []
        for text in input:
            result = client.models.embed_content(
                model=model,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            embeddings.append(result.embeddings[0].values)
        return embeddings

class GeminiQueryEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        client = get_genai_client()
        model = 'gemini-embedding-2'
        embeddings = []
        for text in input:
            result = client.models.embed_content(
                model=model,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            embeddings.append(result.embeddings[0].values)
        return embeddings

def get_chroma_client():
    # Initialize ChromaDB client (persistent)
    db_path = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
    return chromadb.PersistentClient(path=db_path)

def get_collection():
    client = get_chroma_client()
    embedding_function = GeminiEmbeddingFunction()
    return client.get_or_create_collection(
        name="pdf_documents",
        embedding_function=embedding_function
    )

def extract_text_from_file(file_path: str) -> str:
    if file_path.lower().endswith('.pdf'):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    else:
        # For .md, .txt, etc.
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def process_and_store_document(file_path: str, filename: str):
    text = extract_text_from_file(file_path)
    chunks = chunk_text(text)
    
    if not chunks:
        return 0

    collection = get_collection()
    
    ids = [f"{filename}-{uuid.uuid4()}" for _ in chunks]
    metadatas = [{"source": filename} for _ in chunks]
    
    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    return len(chunks)

def query_rag(question: str, history: list = None, n_results: int = 15):
    if history is None:
        history = []
        
    collection = get_collection()
    query_embedding_function = GeminiQueryEmbeddingFunction()
    
    # Generate query embeddings manually
    query_embeddings = query_embedding_function([question])
    
    # Retrieve relevant documents
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results
    )
    
    documents = results['documents'][0] if results['documents'] else []
    context = "\n\n".join(documents)
    
    # Generate answer with Gemini
    client = get_genai_client()
    
    # Format history
    history_text = ""
    if history:
        history_text = "Historial de conversación previa:\n"
        for msg in history:
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            history_text += f"{role}: {msg['content']}\n"
        history_text += "\n"
    
    prompt = f"""Eres el asistente virtual del Colegio de Estudios Superiores Rioverdense (CESR) y la UDEP.

INSTRUCCIÓN CRÍTICA PARA EL SALUDO:
Si el mensaje ACTUAL del usuario es ÚNICAMENTE un saludo (ej. "hola", "buenos días") y NO HAY historial de conversación previo, debes responder EXACTAMENTE y SOLO con el siguiente mensaje:
"¡Hola! Soy el asistente virtual del CESR, ¿sobre qué te gustaría información? Preparatoria escolarizada, Prepa sabatina, Licenciaturas?"

Si ya hay historial de conversación, NO repitas el mensaje de bienvenida genérico, adapta tu respuesta al contexto de la charla.
Si el usuario menciona CUALQUIER tema específico, como "prepa", "preparatoria", "licenciatura", "costos", "inscripción", etc., ENTONCES DEBES IGNORAR la instrucción del saludo de bienvenida y responder a su consulta basándote ÚNICAMENTE en el siguiente contexto.

FORMATO DE RESPUESTA ESTRICTO PARA WHATSAPP:
- La respuesta debe ser natural, conversacional y muy amigable.
- PROHIBIDO usar Markdown estándar. NO uses doble asterisco (**texto**) porque WhatsApp no lo entiende. 
- Si quieres resaltar algo en negrita para WhatsApp, usa un SOLO asterisco (*texto*). 
- NO uses numerales (#) para títulos, ni guiones (-) ni números (1. 2.) para las listas.
- Para hacer listas, usa un punto de viñeta (•) o un emoji pequeño y limpio (🔸 o ✅) al inicio de cada línea. Evita saturar el mensaje con demasiados emojis grandes.
- Resume la información, no mandes bloques enormes de texto. Sé claro y ve al grano.

INSTRUCCIÓN CRÍTICA - TRANSFERENCIA A HUMANO:
Si el usuario expresa CUALQUIERA de estas intenciones (aunque no use estas palabras exactas):
- Quiere hablar con una persona real, un humano, un asesor, alguien de la escuela
- Quiere que lo llamen o contacten
- Pide un número de teléfono para llamar a la escuela
- Dice que prefiere hablar con alguien directamente
- Expresa frustración y quiere atención personalizada

ENTONCES debes:
1. Responder amablemente que ya avisarás a un asesor para que lo contacte.
2. Incluir OBLIGATORIAMENTE el tag exacto [[CONTACT_HUMAN]] en tu respuesta (puede estar en cualquier parte del texto, el sistema lo detectará automáticamente).
NO menciones ningún número de teléfono en la respuesta, el asesor se encargará de contactar al usuario.

{history_text}
Context:
{context}

Question: {question}"""
    
    response = client.models.generate_content(
        model='gemini-flash-lite-latest',
        contents=prompt
    )
    return {
        "answer": response.text,
        "context_used": documents
    }
