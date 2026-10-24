from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.doctor import Doctor


def get_doctor_by_full_name(
    db: Session,
    establishment_id: int,
    full_name: str
) -> Doctor | None:

    normalized_name = " ".join(
        full_name.strip().split()
    ).lower()

    statement = select(Doctor).where(
        Doctor.id_establecimiento == establishment_id,
        Doctor.estado.is_(True),
        func.lower(
            func.concat(
                Doctor.nombres,
                " ",
                Doctor.apellidos
            )
        ) == normalized_name
    )

    return db.execute(
        statement
    ).scalar_one_or_none()