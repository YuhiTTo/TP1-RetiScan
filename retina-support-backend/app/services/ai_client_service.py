import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


class AIServiceConnectionError(Exception):
    pass


class AIServiceAnalysisError(Exception):
    pass


def request_ai_analysis(
    evaluation_id: int,
    s3_path: str
) -> dict:

    url = (
        settings.ai_service_url.rstrip("/")
        + "/api/v1/analyze"
    )

    payload = {
        "id_evaluacion": evaluation_id,
        "ruta_s3": s3_path
    }

    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urlopen(
            request,
            timeout=180
        ) as response:

            content = response.read().decode(
                "utf-8"
            )

            return json.loads(content)

    except HTTPError as error:

        detail = error.read().decode(
            "utf-8",
            errors="replace"
        )

        raise AIServiceAnalysisError(
            detail
        ) from error

    except (
        URLError,
        TimeoutError
    ) as error:

        raise AIServiceConnectionError(
            "No se pudo establecer comunicación "
            "con el Servicio IA."
        ) from error
