from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Account(Base):
    __tablename__ = "cuenta_acceso"

    id_cuenta: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_establecimiento: Mapped[int | None] = mapped_column(
        ForeignKey("establecimiento.id_establecimiento"),
        nullable=True,
        unique=True
    )

    correo_electronico: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    tipo_cuenta: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    nombre_mostrado: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    estado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )