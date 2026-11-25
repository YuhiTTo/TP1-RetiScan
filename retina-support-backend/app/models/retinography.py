from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Retinography(Base):
    __tablename__ = "retinografia"

    id_retinografia: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_evaluacion: Mapped[int] = mapped_column(
        ForeignKey("evaluacion_retiniana.id_evaluacion"),
        nullable=False,
        unique=True
    )

    nombre_archivo: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    formato: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    tamano_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    ancho_px: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    alto_px: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    ruta_original_s3: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    estado_validacion: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDIENTE"
    )

    calidad_imagen: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="CARGADA"
    )

    fecha_carga: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )