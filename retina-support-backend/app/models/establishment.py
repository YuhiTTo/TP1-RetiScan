from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Establishment(Base):
    __tablename__ = "establecimiento"

    __table_args__ = (
        UniqueConstraint(
            "codigo_institucional",
            name="uq_establecimiento_codigo_institucional"
        ),
    )

    id_establecimiento: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    codigo_institucional: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    nombre: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    ruc: Mapped[str | None] = mapped_column(
        String(11),
        nullable=True
    )

    direccion: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    distrito: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    telefono: Mapped[str] = mapped_column(
        String(20),
        nullable=False
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