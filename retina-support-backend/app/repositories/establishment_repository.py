from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.establishment import Establishment


def get_establishment_by_code(
    db: Session,
    codigo_institucional: str
) -> Establishment | None:

    normalized_code = (
        codigo_institucional
        .strip()
        .upper()
    )

    statement = select(
        Establishment
    ).where(
        Establishment.codigo_institucional
        == normalized_code
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_establishments(
    db: Session
) -> list[Establishment]:

    statement = (
        select(Establishment)
        .order_by(
            Establishment.fecha_registro.desc(),
            Establishment.id_establecimiento.desc()
        )
    )

    return list(
        db.execute(statement)
        .scalars()
        .all()
    )

def get_establishment_by_id(
    db: Session,
    id_establecimiento: int
) -> Establishment | None:

    statement = select(
        Establishment
    ).where(
        Establishment.id_establecimiento
        == id_establecimiento
    )

    return db.execute(
        statement
    ).scalar_one_or_none()