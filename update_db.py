import rag
import uuid
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    try:
        client = rag.get_chroma_client()
        try:
            client.delete_collection("pdf_documents")
            print("Collection deleted successfully.")
        except ValueError:
            print("Collection did not exist yet.")
    except Exception as e:
        print("Could not delete collection:", e)

    with open("manual_oferta_educativa.md", "r", encoding="utf-8") as f:
        text = f.read()

    chunks = rag.chunk_text(text)
    if not chunks:
        print("No chunks found!")
        sys.exit(1)

    collection = rag.get_collection()
    filename = "manual_oferta_educativa.md"
    ids = [f"{filename}-{uuid.uuid4()}" for _ in chunks]
    metadatas = [{"source": filename} for _ in chunks]

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Successfully processed {filename}. Stored {len(chunks)} chunks.")

if __name__ == "__main__":
    main()
