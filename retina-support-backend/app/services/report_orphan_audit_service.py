"""Auditoria de PDFs de reportes potencialmente huerfanos.

No elimina ni modifica archivos de Amazon S3.
"""

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import Report


REPORT_KEY_PATTERN = re.compile(
    r"reportes/[1-9][0-9]*/reporte-[0-9a-f]{32}\.pdf"
)


def find_orphan_report_objects(
    db: Session,
    s3_client,
    bucket: str,
    minimum_age_hours: int = 48,
) -> list[dict]:
    """Encuentra objetos antiguos sin referencia activa en PostgreSQL."""

    if not bucket:
        raise ValueError("Se requiere un bucket valido.")

    if minimum_age_hours < 24:
        raise ValueError(
            "La antiguedad minima debe ser de 24 horas."
        )

    active_paths = set(
        db.execute(
            select(Report.ruta_pdf_s3)
        ).scalars().all()
    )

    cutoff = datetime.now(timezone.utc) - timedelta(
        hours=minimum_age_hours
    )

    paginator = s3_client.get_paginator("list_objects_v2")

    candidates = []

    for page in paginator.paginate(
        Bucket=bucket,
        Prefix="reportes/",
    ):
        for obj in page.get("Contents", []):
            key = obj.get("Key")
            last_modified = obj.get("LastModified")

            if not isinstance(key, str):
                continue

            if not REPORT_KEY_PATTERN.fullmatch(key):
                continue

            if (
                not isinstance(last_modified, datetime)
                or last_modified.tzinfo is None
            ):
                continue

            if last_modified > cutoff:
                continue

            s3_path = f"s3://{bucket}/{key}"

            if s3_path in active_paths:
                continue

            candidates.append({
                "s3_path": s3_path,
                "last_modified": last_modified.isoformat(),
                "size_bytes": obj.get("Size"),
            })

    return sorted(
        candidates,
        key=lambda item: item["s3_path"],
    )
