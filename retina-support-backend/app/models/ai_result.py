from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIResult(Base):
    __tablename__ = "resultado_ia"

    id_resultado: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_ejecucion: Mapped[int] = mapped_column(
        ForeignKey("ejecucion_modelo.id_ejecucion"),
        nullable=False,
        unique=True
    )

    resultado: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    nivel_confianza: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
