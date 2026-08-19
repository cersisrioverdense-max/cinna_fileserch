import httpx

# 1. Asegúrate de tener tu manual en formato MD o PDF en esta misma carpeta
document_filename = "manual_oferta_educativa.md" 

# 2. Esta es la URL de tu servidor en Railway para subir documentos
url = "https://web-production-fa961.up.railway.app/upload-document/"

print(f"Intentando subir {document_filename} al servidor...")

try:
    with open(document_filename, "rb") as f:
        # Puedes usar application/octet-stream o text/markdown
        files = {"file": (document_filename, f, "text/markdown")}
        response = httpx.post(url, files=files, timeout=60.0)

    print(f"\nRespuesta del servidor (Código {response.status_code}):")
    print(response.json())
except FileNotFoundError:
    print(f"\n¡ERROR! No se encontró el archivo '{document_filename}'.")
except Exception as e:
    print(f"\nOcurrió un error: {e}")
