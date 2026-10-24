from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Doctor(Base):
    __tablename__ = "medico"

    id_medico: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_establecimiento: Mapped[int] = mapped_column(
        ForeignKey("establecimiento.id_establecimiento"),
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

    estado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )