import io
import re
import unicodedata

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


class ServicioGoogleDrive:
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(self):
        try:
            credenciales = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE,
                scopes=self.SCOPES
            )
        except Exception as e:
            raise RuntimeError(f"Error inicializando Google Drive: {e}")

        self.service = build("drive", "v3", credentials=credenciales)
        self.root_folder_id = settings.GOOGLE_DRIVE_ROOT_FOLDER_ID

    @staticmethod
    def normalizar_nombre(nombre: str) -> str:
        nombre = unicodedata.normalize("NFKD", nombre).encode(
            "ascii", "ignore"
        ).decode("ascii")
        nombre = re.sub(r"[^A-Za-z0-9._ -]", "", nombre).strip()
        nombre = re.sub(r"\s+", "-", nombre)
        return nombre[:150]

    def buscar_carpeta(self, nombre: str, parent_id: str):
        query = (
            "mimeType='application/vnd.google-apps.folder' "
            f"and name='{nombre}' "
            f"and '{parent_id}' in parents "
            "and trashed=false"
        )

        response = self.service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            pageSize=10
        ).execute()

        carpetas = response.get("files", [])
        return carpetas[0] if carpetas else None

    def crear_carpeta(self, nombre: str, parent_id: str):
        metadata = {
            "name": nombre,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        return self.service.files().create(
            body=metadata,
            fields="id, name, webViewLink"
        ).execute()

    def obtener_o_crear_carpeta(self, nombre: str, parent_id: str):
        carpeta = self.buscar_carpeta(nombre, parent_id)
        if carpeta:
            return carpeta
        return self.crear_carpeta(nombre, parent_id)

    def crear_estructura_postulante(
        self,
        anio,
        modalidad,
        numero_documento,
        nombres,
        apellido_paterno,
        apellido_materno
    ):
        carpeta_anio = self.obtener_o_crear_carpeta(
            str(anio), self.root_folder_id
        )
        carpeta_modalidad = self.obtener_o_crear_carpeta(
            self.normalizar_nombre(modalidad),
            carpeta_anio["id"]
        )

        nombre_postulante = self.normalizar_nombre(
            f"{numero_documento}-{apellido_paterno}-{apellido_materno}-{nombres}"
        )

        return self.obtener_o_crear_carpeta(
            nombre_postulante,
            carpeta_modalidad["id"]
        )

    def subir_archivo(self, archivo, nombre_destino: str, parent_id: str):
        contenido = archivo.read()
        archivo.seek(0)

        media = MediaIoBaseUpload(
            io.BytesIO(contenido),
            mimetype=getattr(archivo, "content_type", "application/octet-stream"),
            resumable=True,
        )

        metadata = {
            "name": nombre_destino,
            "parents": [parent_id],
        }

        return self.service.files().create(
            body=metadata,
            media_body=media,
            fields="id, name, webViewLink, webContentLink, mimeType"
        ).execute()

    # ✅ ESTA FUNCIÓN DEBE ESTAR AQUÍ
    def descargar_archivo(self, file_id):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        return fh.read()
