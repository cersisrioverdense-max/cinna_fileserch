import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def check_meta_config():
    token = os.environ.get("META_API_TOKEN")
    phone_id = os.environ.get("META_PHONE_NUMBER_ID")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Checking phone number configuration...")
    async with httpx.AsyncClient() as client:
        waba_id = "1332056119013320"
        print(f"Checking webhooks for WABA {waba_id}...")
        res2 = await client.get(f"https://graph.facebook.com/v25.0/{waba_id}/subscribed_apps", headers=headers)
        print("Subscribed apps:", res2.json())

if __name__ == "__main__":
    asyncio.run(check_meta_config())
