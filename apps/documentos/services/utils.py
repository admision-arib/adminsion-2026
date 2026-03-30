import os


def construir_nombre_documento(tipo_codigo: str, numero_documento: str, archivo) -> str:
    _, extension = os.path.splitext(archivo.name)
    extension = extension.lower() if extension else ".bin"
    return f"{tipo_codigo}_{numero_documento}{extension}"