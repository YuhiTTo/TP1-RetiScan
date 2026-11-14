
# US-16 — Regla de sugerencia de prioridad de atención
# Matriz propuesta para el prototipo RetiScan.
# Pendiente de validación clínica.

RD_PRIORITIES = {
    "Sin indicios de Retinopatía Diabética": "BAJA",
    "Leve": "BAJA",
    "Moderada": "MEDIA",
    "Severa": "ALTA",
    "Proliferativa": "ALTA",
}

GLAUCOMA_PRIORITIES = {
    "Bajo riesgo de Glaucoma": "BAJA",
    "Alto riesgo de Glaucoma": "ALTA",
}

PRIORITY_ORDER = {
    "BAJA": 1,
    "MEDIA": 2,
    "ALTA": 3,
}


def calculate_suggested_priority(
    rd_result: str | None,
    glaucoma_result: str | None
) -> str | None:
    """
    Calcula la prioridad sugerida a partir de ambos
    resultados automatizados.

    Retorna None si falta algún resultado o si
    alguna categoría no está reconocida.
    """

    if rd_result not in RD_PRIORITIES:
        return None

    if glaucoma_result not in GLAUCOMA_PRIORITIES:
        return None

    rd_priority = RD_PRIORITIES[rd_result]
    glaucoma_priority = GLAUCOMA_PRIORITIES[glaucoma_result]

    return max(
        rd_priority,
        glaucoma_priority,
        key=lambda priority: PRIORITY_ORDER[priority]
    )
