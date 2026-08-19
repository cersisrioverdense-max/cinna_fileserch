import httpx

# 1. Asegúrate de tener tu manual en formato PDF (NO en .md) en esta misma carpeta
pdf_filename = "manual_oferta_educativa.pdf" 

# 2. Esta es la URL de tu servidor en Railway para subir PDFs
url = "https://web-production-fa961.up.railway.app/upload-pdf/"

print(f"Intentando subir {pdf_filename} al servidor...")

try:
    with open(pdf_filename, "rb") as f:
        files = {"file": (pdf_filename, f, "application/pdf")}
        response = httpx.post(url, files=files, timeout=60.0)

    print(f"\nRespuesta del servidor (Código {response.status_code}):")
    print(response.json())
except FileNotFoundError:
    print(f"\n¡ERROR! No se encontró el archivo '{pdf_filename}'.")
    print("Asegúrate de convertir tu archivo 'manual_oferta_educativa.md' a PDF primero")
    print("y guardarlo en esta misma carpeta con el nombre 'manual_oferta_educativa.pdf'.")
except Exception as e:
    print(f"\nOcurrió un error: {e}")
