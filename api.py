import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import rag
from fastapi import Request, Response
import httpx
import asyncio
import time
from bot_logic import send_whatsapp_message
router = APIRouter()

message_buffers = {}
user_sessions = {}
DEBOUNCE_TIME = 7.0
SESSION_TIMEOUT = 7200 # 2 hours

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    context_used: list[str]

@router.post("/upload-document/")
async def upload_document(file: UploadFile = File(...)):
    if not (file.filename.endswith('.pdf') or file.filename.endswith('.md') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="Only PDF, MD, and TXT files are supported.")
    
    # Save uploaded file temporarily
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Process and store
        num_chunks = rag.process_and_store_document(tmp_path, file.filename)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
            
    return {"message": f"Successfully processed {file.filename}. Stored {num_chunks} chunks."}

@router.post("/ask/", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        result = rag.query_rag(request.question)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Webhook verification (Wappfly might not need this, but keeping it simple)
    """
    return {"status": "success"}

@router.post("/")
@router.post("/webhook")
async def webhook_events(request: Request):
    """
    Receive incoming messages from Wappfly
    """
    body = await request.json()
    print("====================================")
    print(">>> WAPPFLY WEBHOOK RECIBIDO:", body)
    print("====================================")
    
    # Extract Wappfly message data
    try:
        if body.get("event") == "messages.received":
            data = body.get("data", {})
            
            raw_messages = data.get("messages")
            if isinstance(raw_messages, list) and len(raw_messages) > 0:
                messages = raw_messages[0]
            elif isinstance(raw_messages, dict):
                messages = raw_messages
            else:
                messages = {}

            key = messages.get("key", {})
            
            # Solo procesar si el mensaje NO fue enviado por nosotros mismos
            if key.get("fromMe") is False:
                from_number = key.get("cleanedSenderPn") or key.get("remoteJid")
                msg_text = messages.get("messageBody")
                
                if from_number and msg_text:
                    print(f"-> Recibido fragmento de {from_number}: {msg_text}")
                    
                    if from_number in message_buffers:
                        # Cancelar tarea anterior
                        message_buffers[from_number]["task"].cancel()
                        # Concatenar el mensaje
                        message_buffers[from_number]["text"] += "\n" + msg_text
                    else:
                        message_buffers[from_number] = {"text": msg_text}
                        
                    # Crear nueva tarea para procesar el mensaje con debounce
                    task = asyncio.create_task(process_buffered_message(from_number))
                    message_buffers[from_number]["task"] = task
                    
    except Exception as e:
        print(f"Error al procesar webhook de Wappfly: {e}")
    
    return {"status": "success"}

async def process_buffered_message(from_number: str):
    try:
        # Esperar 7 segundos por si llegan más mensajes
        await asyncio.sleep(DEBOUNCE_TIME)
    except asyncio.CancelledError:
        # Si la tarea se cancela, es porque llegó otro mensaje y se reinició el contador
        return
        
    buffer_data = message_buffers.pop(from_number, None)
    if not buffer_data:
        return
        
    msg_text = buffer_data["text"]
    print(f"-> Procesando mensaje unificado de {from_number}:\n{msg_text}")
    
    # Manejo de la sesión (historial y última interacción)
    current_time = time.time()
    session = user_sessions.get(from_number)
    
    if not session or (current_time - session["last_interaction"] > SESSION_TIMEOUT):
        # Nueva sesión o expirada (pasaron más de 2 horas)
        session = {"last_interaction": current_time, "history": []}
        user_sessions[from_number] = session
    
    session["last_interaction"] = current_time
    history = session["history"]
    
    try:
        # rag.query_rag ahora recibe el historial
        result = await asyncio.to_thread(rag.query_rag, msg_text, history)
        answer = result["answer"]
        
        # Guardar en el historial
        history.append({"role": "user", "content": msg_text})
        history.append({"role": "assistant", "content": answer})
        
        # Mantener solo los últimos 10 mensajes (5 idas y vueltas) para no saturar
        if len(history) > 10:
            session["history"] = history[-10:]
        
        # Detectar si el usuario quiere hablar con un humano
        if "[[CONTACT_HUMAN]]" in answer:
            answer = answer.replace("[[CONTACT_HUMAN]]", "").strip()
            if not answer:
                answer = "Le he avisado a la escuela. Un asesor se pondrá en contacto contigo pronto a este número."
            
            # Avisar a los números de la escuela
            numeros_escuela = ["524871569878", "524871126942"]
            mensaje_alerta = f"🚨 *Alerta de Contacto* 🚨\nEl usuario con número {from_number} quiere hablar con un asesor.\n\nMensaje que envió:\n\"{msg_text}\""
            for num in numeros_escuela:
                await send_whatsapp_message(num, mensaje_alerta)
            
        await send_whatsapp_message(from_number, answer)
    except Exception as e:
        print(f"Error en RAG: {e}")
        await send_whatsapp_message(from_number, "Lo siento, ocurrió un error procesando tu consulta.")
