import asyncio
from dotenv import load_dotenv
load_dotenv()
from bot_logic import send_whatsapp_message

async def main():
    print("Testing WhatsApp send...")
    success = await send_whatsapp_message("524871558316", "Hola, este es un mensaje de prueba desde bot_logic.py")
    print("Success:", success)

if __name__ == "__main__":
    asyncio.run(main())
