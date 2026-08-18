import httpx
import asyncio
import json

async def check_ngrok_traffic():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("http://127.0.0.1:4040/api/requests/http")
            if res.status_code == 200:
                data = res.json()
                requests = data.get("requests", [])
                if not requests:
                    print("No requests found in Ngrok.")
                for req in requests[:5]:
                    print(f"[{req['response']['status_code']}] {req['request']['method']} {req['request']['uri']}")
            else:
                print("Failed to get ngrok API:", res.status_code)
    except Exception as e:
        print("Error connecting to ngrok:", e)

if __name__ == "__main__":
    asyncio.run(check_ngrok_traffic())
