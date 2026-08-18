from fastapi import FastAPI
from api import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Gemini PDF RAG API",
    description="An API to upload PDFs and ask questions using Gemini and ChromaDB",
    version="1.0.0"
)

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Gemini PDF RAG API. Visit /docs to test the endpoints."}
