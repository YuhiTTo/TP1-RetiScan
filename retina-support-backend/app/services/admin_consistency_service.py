from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.admin_consistency_repository import (
    load_admin_consistency_evaluations,
    load_latest_admin_consistency_ai,
)
from app.schemas.admin_consistency import (
    AdminConsistencyIssue,
    AdminConsistencyItem,
    AdminConsistencyPage,
    AdminConsistencySummary,
)


EXPECTED_OBJECTIVES = frozenset({
    "RETINOPATIA_DIABETICA",
    "GLAUCOMA",
})

STATUS_PRIORITY = {
    "REQUIERE_ATENCION": 0,
    "EN_PROCESO": 1,
    "CONSISTENTE": 2,
}


def _has_complete_ai_results(
    evaluation: Mapping[str, Any],
    analysis_rows: list[dict],
) -> bool:
    """Replica los criterios de disponibilidad de IA existentes."""

    if evaluation.get("estado_retinografia") != "ANALIZADA":
        return False

    if not analysis_rows:
        return False

    if any(
        row.get("estado_analisis") != "COMPLETADO"
        for row in analysis_rows
    ):
        return False

    objectives_found = set()

    for row in analysis_rows:
        objective = row.get("objetivo_modelo")

        if objective not in EXPECTED_OBJECTIVES:
            continue

        if (
            row.get("estado_ejecucion") != "COMPLETADO"
            or row.get("id_resultado") is None
            or objective in objectives_found
        ):
            return False

        objectives_found.add(objective)

    return objectives_found == EXPECTED_OBJECTIVES


def classify_admin_consistency(
    evaluation: Mapping[str, Any],
    analysis_rows: list[dict],
) -> AdminConsistencyItem:
    """Aplica CONS-01 a CONS-05 sin modificar registros."""

    state = evaluation["estado_evaluacion"]

    if state not in ("PENDIENTE", "FINALIZADA"):
        raise ValueError(
            f"Estado de evaluacion no contemplado: {state}"
        )

    establishment_id = evaluation["id_establecimiento"]
    issues = []

    # CONS-01: paciente y establecimiento.
    if (
        evaluation.get("paciente_id_encontrado") is None
        or evaluation.get("paciente_establecimiento_id")
        != establishment_id
    ):
        issues.append(
            AdminConsistencyIssue(
                codigo="CONS-01",
                descripcion=(
                    "La asociación del paciente con el "
                    "establecimiento es inconsistente."
                ),
            )
        )

    # CONS-02: medico y establecimiento.
    if (
        evaluation.get("medico_id_encontrado") is None
        or evaluation.get("medico_establecimiento_id")
        != establishment_id
    ):
        issues.append(
            AdminConsistencyIssue(
                codigo="CONS-02",
                descripcion=(
                    "La asociación del médico con el "
                    "establecimiento es inconsistente."
                ),
            )
        )

    if state == "FINALIZADA":

        # CONS-03: fecha de finalizacion.
        if evaluation.get("fecha_finalizacion") is None:
            issues.append(
                AdminConsistencyIssue(
                    codigo="CONS-03",
                    descripcion=(
                        "Evaluación finalizada sin fecha "
                        "de finalización."
                    ),
                )
            )

        # CONS-05: retinografia asociada.
        if evaluation.get("id_retinografia") is None:
            issues.append(
                AdminConsistencyIssue(
                    codigo="CONS-05",
                    descripcion=(
                        "Evaluación finalizada sin "
                        "retinografía asociada."
                    ),
                )
            )

        # CONS-04: solo se evalua si hay retinografia.
        elif not _has_complete_ai_results(
            evaluation, analysis_rows
        ):
            issues.append(
                AdminConsistencyIssue(
                    codigo="CONS-04",
                    descripcion=(
                        "Los resultados del análisis IA "
                        "vigente no están completos "
                        "o disponibles."
                    ),
                )
            )

    if issues:
        consistency = "REQUIERE_ATENCION"
    elif state == "PENDIENTE":
        consistency = "EN_PROCESO"
    else:
        consistency = "CONSISTENTE"

    return AdminConsistencyItem(
        id_evaluacion=evaluation["id_evaluacion"],
        id_establecimiento=establishment_id,
        establecimiento=(
            evaluation.get("establecimiento")
            or "Establecimiento no disponible"
        ),
        consistencia=consistency,
        incidencias=issues,
    )


def _audit_all_evaluations(
    db: Session,
) -> list[AdminConsistencyItem]:
    """Consulta y clasifica evaluaciones de solo lectura."""

    evaluations = load_admin_consistency_evaluations(db)

    retinography_ids = sorted({
        row["id_retinografia"]
        for row in evaluations
        if (
            row["estado_evaluacion"] == "FINALIZADA"
            and row["id_retinografia"] is not None
        )
    })

    analysis_rows = load_latest_admin_consistency_ai(
        db, retinography_ids
    )

    analyses_by_retinography = defaultdict(list)

    for row in analysis_rows:
        analyses_by_retinography[
            row["id_retinografia"]
        ].append(row)

    items = [
        classify_admin_consistency(
            evaluation=row,
            analysis_rows=analyses_by_retinography.get(
                row["id_retinografia"], []
            ),
        )
        for row in evaluations
    ]

    items.sort(
        key=lambda item: (
            STATUS_PRIORITY[item.consistencia],
            -item.id_evaluacion,
        )
    )

    return items


def list_admin_consistency(
    db: Session,
    page: int = 1,
    page_size: int = 8,
) -> AdminConsistencyPage:
    """Devuelve resultados paginados para US-22."""

    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError("Paginacion invalida.")

    items = _audit_all_evaluations(db)
    total = len(items)
    start = (page - 1) * page_size

    return AdminConsistencyPage(
        items=items[start:start + page_size],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


def summarize_admin_consistency(
    db: Session,
) -> AdminConsistencySummary:
    """Cuenta registros revisados y con incidencias."""

    items = _audit_all_evaluations(db)

    return AdminConsistencySummary(
        registros_revisados=len(items),
        con_incidencias=sum(
            bool(item.incidencias) for item in items
        ),
    )
