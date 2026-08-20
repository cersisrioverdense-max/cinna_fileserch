import os
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_whatsapp_message(to_number: str, message_body: str):
    # Wappfly requiere el formato número@s.whatsapp.net
    if "@" not in to_number:
        to_number = f"{to_number}@s.whatsapp.net"
        
    token = os.environ.get("WAPPFLY_API_TOKEN")
    
    if not token:
        logger.error("Falta WAPPFLY_API_TOKEN en el .env")
        return False
        
    url = "https://wappfly.com/api/messages/send"
    
    headers = {
        "X-API-Token": token,
        "Content-Type": "application/json; charset=utf-8"
    }
    
    data = {
        "jid": to_number,
        "text": message_body
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"Mensaje enviado exitosamente a {to_number}")
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Respuesta de Wappfly: {e.response.text}")
            return False
