from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RetinalEvaluation(Base):
    __tablename__ = "evaluacion_retiniana"

    id_evaluacion: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_paciente: Mapped[int] = mapped_column(
        ForeignKey("paciente.id_paciente"),
        nullable=False
    )

    id_medico: Mapped[int] = mapped_column(
        ForeignKey("medico.id_medico"),
        nullable=False
    )

    id_establecimiento: Mapped[int] = mapped_column(
        ForeignKey("establecimiento.id_establecimiento"),
        nullable=False
    )

    fecha_evaluacion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    ojo_evaluado: Mapped[str] = mapped_column(
        String(2),
        nullable=False
    )

    observacion_medica: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    prioridad_sugerida: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDIENTE"
    )

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    fecha_finalizacion: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )