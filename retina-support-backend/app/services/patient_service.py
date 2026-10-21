from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.repositories.patient_repository import (
    get_patient_by_document,
    get_patient_by_id,
    search_patients
)
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientAlreadyExistsError(Exception):
    pass

class PatientNotFoundError(Exception):
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

def get_patient(
    db: Session,
    establishment_id: int,
    patient_id: int
) -> Patient:

    patient = get_patient_by_id(
        db=db,
        establishment_id=establishment_id,
        patient_id=patient_id
    )

    if patient is None:
        raise PatientNotFoundError()

    return patient

def update_patient(
    db: Session,
    establishment_id: int,
    patient_id: int,
    data: PatientUpdate
) -> Patient:

    patient = get_patient_by_id(
        db=db,
        establishment_id=establishment_id,
        patient_id=patient_id
    )

    if patient is None:
        raise PatientNotFoundError()

    update_data = data.model_dump(exclude_unset=True)

    # No permitir vaciar campos obligatorios
    required_fields = {
        "numero_documento",
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        "sexo"
    }

    for field in required_fields:
        if field in update_data and update_data[field] is None:
            raise ValueError(
                f"El campo {field} no puede ser nulo."
            )

    # Si cambia el documento, verificar que no exista otro
    if "numero_documento" in update_data:
        new_document = update_data["numero_documento"].strip()

        existing_patient = get_patient_by_document(
            db=db,
            establishment_id=establishment_id,
            document_number=new_document
        )

        if (
            existing_patient is not None
            and existing_patient.id_paciente != patient.id_paciente
        ):
            raise PatientAlreadyExistsError()

        update_data["numero_documento"] = new_document

    # Normalización de textos
    for field in (
        "nombres",
        "apellidos",
        "sexo",
        "telefono",
        "direccion"
    ):
        if field in update_data and update_data[field] is not None:
            update_data[field] = update_data[field].strip()

    if "correo" in update_data and update_data["correo"] is not None:
        update_data["correo"] = str(
            update_data["correo"]
        ).strip().lower()

    for field, value in update_data.items():
        setattr(patient, field, value)

    try:
        db.commit()
        db.refresh(patient)

        return patient

    except IntegrityError:
        db.rollback()
        raise