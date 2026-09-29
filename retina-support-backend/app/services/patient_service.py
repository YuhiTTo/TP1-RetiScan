from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.repositories.patient_repository import (
    get_patient_by_document,
    search_patients
)
from app.schemas.patient import PatientCreate


class PatientAlreadyExistsError(Exception):
    pass


def create_patient(
    db: Session,
    establishment_id: int,
    data: PatientCreate
) -> Patient:

    document_number = data.numero_documento.strip()

    existing_patient = get_patient_by_document(
        db=db,
        establishment_id=establishment_id,
        document_number=document_number
    )

    if existing_patient is not None:
        raise PatientAlreadyExistsError()

    patient = Patient(
        id_establecimiento=establishment_id,
        numero_documento=document_number,
        nombres=data.nombres.strip(),
        apellidos=data.apellidos.strip(),
        fecha_nacimiento=data.fecha_nacimiento,
        sexo=data.sexo.strip(),
        telefono=(
            data.telefono.strip()
            if data.telefono
            else None
        ),
        correo=(
            data.correo.strip().lower()
            if data.correo
            else None
        ),
        direccion=(
            data.direccion.strip()
            if data.direccion
            else None
        ),
        estado=True
    )

    try:
        db.add(patient)
        db.commit()
        db.refresh(patient)

        return patient

    except IntegrityError:
        db.rollback()
        raise

def find_patients(
    db: Session,
    establishment_id: int,
    search: str
) -> list[Patient]:

    return search_patients(
        db=db,
        establishment_id=establishment_id,
        search=search
    )