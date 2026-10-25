from datetime import datetime

from pydantic import BaseModel


class RetinographyResponse(BaseModel):
    id_retinografia: int
    id_evaluacion: int
    nombre_archivo: str
    formato: str
    tamano_bytes: int
    ancho_px: int
    alto_px: int
    ruta_original_s3: str
    estado_validacion: str
    calidad_imagen: str | None
    estado: str
    fecha_carga: datetime