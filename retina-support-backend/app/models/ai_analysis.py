from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIAnalysis(Base):
    __tablename__ = "analisis_ia"

    id_analisis: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_retinografia: Mapped[int] = mapped_column(
        ForeignKey("retinografia.id_retinografia"),
        nullable=False
    )

    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDIENTE"
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
