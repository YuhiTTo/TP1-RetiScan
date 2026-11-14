from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIModel(Base):
    __tablename__ = "modelo_ia"

    id_modelo: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    objetivo: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    ruta_modelo: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVO"
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )
