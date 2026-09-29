from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Patient(Base):
    __tablename__ = "paciente"

    __table_args__ = (
        UniqueConstraint(
            "id_establecimiento",
            "numero_documento",
            name="uq_paciente_establecimiento_documento"
        ),
    )

    id_paciente: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_establecimiento: Mapped[int] = mapped_column(
        ForeignKey("establecimiento.id_establecimiento"),
        nullable=False
    )

    numero_documento: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    nombres: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    apellidos: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    fecha_nacimiento: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    sexo: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    telefono: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    correo: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    direccion: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    estado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )