import httpx
import asyncio

async def test_webhook():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "12345",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "524871558316",
                                    "id": "wamid.123",
                                    "timestamp": "1630000000",
                                    "type": "text",
                                    "text": {
                                        "body": "qué es Cinnamoroll?"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    print("Sending POST request to webhook...")
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/webhook", json=payload)
        print("Webhook response status:", response.status_code)
        print("Webhook response body:", response.json())

if __name__ == "__main__":
    asyncio.run(test_webhook())
