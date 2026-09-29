from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.patient import Patient


def get_patient_by_document(
    db: Session,
    establishment_id: int,
    document_number: str
) -> Patient | None:

    statement = select(Patient).where(
        Patient.id_establecimiento == establishment_id,
        Patient.numero_documento == document_number.strip()
    )

    return db.execute(
        statement
    ).scalar_one_or_none()

def search_patients(
    db: Session,
    establishment_id: int,
    search: str
) -> list[Patient]:

    search_value = search.strip()

    statement = (
        select(Patient)
        .where(
            Patient.id_establecimiento == establishment_id,
            or_(
                Patient.numero_documento.ilike(
                    f"%{search_value}%"
                ),
                Patient.nombres.ilike(
                    f"%{search_value}%"
                ),
                Patient.apellidos.ilike(
                    f"%{search_value}%"
                )
            )
        )
        .order_by(
            Patient.apellidos,
            Patient.nombres
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )