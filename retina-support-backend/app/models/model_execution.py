from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ModelExecution(Base):
    __tablename__ = "ejecucion_modelo"

    __table_args__ = (
        UniqueConstraint(
            "id_analisis",
            "id_modelo",
            name="uq_ejecucion_analisis_modelo"
        ),
    )

    id_ejecucion: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_analisis: Mapped[int] = mapped_column(
        ForeignKey("analisis_ia.id_analisis"),
        nullable=False
    )

    id_modelo: Mapped[int] = mapped_column(
        ForeignKey("modelo_ia.id_modelo"),
        nullable=False
    )

    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDIENTE"
    )

    tiempo_inferencia_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    fecha_inicio: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    fecha_fin: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    detalle_error: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )
