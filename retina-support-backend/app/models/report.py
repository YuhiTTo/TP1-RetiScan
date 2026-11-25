from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Report(Base):
    __tablename__ = "reporte"

    id_reporte: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_evaluacion: Mapped[int] = mapped_column(
        ForeignKey("evaluacion_retiniana.id_evaluacion"),
        unique=True,
        nullable=False
    )

    ruta_pdf_s3: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    fecha_generacion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
