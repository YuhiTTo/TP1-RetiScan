from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.establishment import Establishment


def get_establishment_by_code(
    db: Session,
    codigo_institucional: str
) -> Establishment | None:

    statement = select(Establishment).where(
        Establishment.codigo_institucional
        == codigo_institucional.strip().upper()
    )

    return db.execute(
        statement
    ).scalar_one_or_none()