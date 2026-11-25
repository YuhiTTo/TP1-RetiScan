from typing import Literal

from pydantic import BaseModel


ConsistencyStatus = Literal[
    "CONSISTENTE",
    "EN_PROCESO",
    "REQUIERE_ATENCION",
]

ConsistencyCode = Literal[
    "CONS-01",
    "CONS-02",
    "CONS-03",
    "CONS-04",
    "CONS-05",
]


class AdminConsistencyIssue(BaseModel):
    codigo: ConsistencyCode
    descripcion: str


class AdminConsistencyItem(BaseModel):
    id_evaluacion: int
    id_establecimiento: int
    establecimiento: str
    consistencia: ConsistencyStatus
    incidencias: list[AdminConsistencyIssue]


class AdminConsistencyPage(BaseModel):
    items: list[AdminConsistencyItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminConsistencySummary(BaseModel):
    registros_revisados: int
    con_incidencias: int
