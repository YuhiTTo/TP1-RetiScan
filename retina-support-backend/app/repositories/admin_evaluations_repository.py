from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.establishment import Establishment
from app.models.evaluation import RetinalEvaluation


def find_admin_evaluations(
    db: Session,
    evaluation_id: int | None,
    establishment_id: int | None,
    estado: str | None,
    page: int,
    page_size: int
):
    filters = []

    if evaluation_id is not None:
        filters.append(
            RetinalEvaluation.id_evaluacion == evaluation_id
        )

    if establishment_id is not None:
        filters.append(
            RetinalEvaluation.id_establecimiento == establishment_id
        )

    if estado is not None:
        filters.append(
            RetinalEvaluation.estado == estado
        )

    count_query = (
        select(func.count(RetinalEvaluation.id_evaluacion))
        .where(*filters)
    )

    total = db.execute(count_query).scalar_one()

    query = (
        select(
            RetinalEvaluation.id_evaluacion,
            RetinalEvaluation.id_establecimiento,
            Establishment.nombre.label("establecimiento"),
            RetinalEvaluation.fecha_evaluacion,
            RetinalEvaluation.ojo_evaluado,
            RetinalEvaluation.estado
        )
        .join(
            Establishment,
            Establishment.id_establecimiento ==
            RetinalEvaluation.id_establecimiento
        )
        .where(*filters)
        .order_by(
            RetinalEvaluation.fecha_evaluacion.desc(),
            RetinalEvaluation.id_evaluacion.desc()
        )
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    items = [
        dict(row)
        for row in db.execute(query).mappings().all()
    ]

    return total, items


def get_admin_evaluations_summary(db: Session):
    query = select(
        func.count(
            RetinalEvaluation.id_evaluacion
        ).label("total_evaluaciones"),

        func.count(RetinalEvaluation.id_evaluacion)
        .filter(
            RetinalEvaluation.estado == "PENDIENTE"
        ).label("evaluaciones_pendientes"),

        func.count(RetinalEvaluation.id_evaluacion)
        .filter(
            RetinalEvaluation.estado == "FINALIZADA"
        ).label("evaluaciones_finalizadas"),

        func.count(
            func.distinct(
                RetinalEvaluation.id_establecimiento
            )
        ).label("establecimientos_con_evaluaciones")
    )

    return dict(db.execute(query).mappings().one())
