from datetime import datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.establishment import Establishment
from app.models.evaluation import RetinalEvaluation


def get_admin_home_summary(
    db: Session,
    reference_time: datetime | None = None
) -> dict:
    """Consulta actividad administrativa sin datos clinicos."""

    now = reference_time if reference_time is not None else datetime.now()
    since = now - timedelta(days=7)

    recent_condition = and_(
        RetinalEvaluation.fecha_evaluacion >= since,
        RetinalEvaluation.fecha_evaluacion <= now
    )

    query = (
        select(
            Establishment.id_establecimiento,
            Establishment.nombre.label("establecimiento"),
            func.count(
                RetinalEvaluation.id_evaluacion
            ).filter(
                recent_condition
            ).label("evaluaciones_ultimos_7_dias"),
            func.max(
                RetinalEvaluation.fecha_evaluacion
            ).filter(
                RetinalEvaluation.fecha_evaluacion <= now
            ).label("ultima_evaluacion")
        )
        .select_from(Establishment)
        .outerjoin(
            RetinalEvaluation,
            RetinalEvaluation.id_establecimiento ==
            Establishment.id_establecimiento
        )
        .group_by(
            Establishment.id_establecimiento,
            Establishment.nombre
        )
        .order_by(
            Establishment.nombre.asc(),
            Establishment.id_establecimiento.asc()
        )
    )

    rows = db.execute(query).mappings().all()

    activity = [
        {
            "id_establecimiento": row["id_establecimiento"],
            "establecimiento": row["establecimiento"],
            "evaluaciones_ultimos_7_dias":
                row["evaluaciones_ultimos_7_dias"],
            "ultima_evaluacion": row["ultima_evaluacion"]
        }
        for row in rows
    ]

    active = sum(
        item["evaluaciones_ultimos_7_dias"] > 0
        for item in activity
    )

    return {
        "total_establecimientos": len(activity),
        "establecimientos_con_actividad_reciente": active,
        "actividad_establecimientos": activity
    }
