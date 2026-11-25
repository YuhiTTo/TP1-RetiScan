import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.api.routes.evaluations import list_patient_evaluations
from app.services.ai_results_service import AIResultsNotAvailableError
from app.services.evaluation_service import EvaluationPatientNotFoundError


class TestUS19HistoryEndpoint(unittest.TestCase):

    def setUp(self):
        self.db = Mock()
        self.db.get.return_value = SimpleNamespace(
            nombres="Carlos",
            apellidos="Prueba"
        )
        self.account = SimpleNamespace(
            id_establecimiento=1
        )

    def evaluation(self, estado="FINALIZADA"):
        return SimpleNamespace(
            id_evaluacion=4,
            id_paciente=1,
            id_medico=1,
            id_establecimiento=1,
            fecha_evaluacion="2026-11-15",
            ojo_evaluado="OD",
            observacion_medica=None,
            prioridad_sugerida="BAJA",
            estado=estado,
            fecha_creacion="2026-11-15",
            fecha_finalizacion=None
        )

    def ai_results(self):
        return {
            "retinopatia_diabetica": {
                "resultado": "Sin indicios de Retinopatía Diabética",
                "confianza": 0.9435707330703735
            },
            "glaucoma": {
                "resultado": "Bajo riesgo de Glaucoma",
                "confianza": 0.8142898550709973
            }
        }

    @patch("app.api.routes.evaluations.get_ai_evaluation_results")
    @patch("app.api.routes.evaluations.get_patient_evaluations")
    def test_finalizada_con_resultados(self, get_evaluations, get_ai):
        get_evaluations.return_value = [self.evaluation()]
        get_ai.return_value = self.ai_results()

        response = list_patient_evaluations(
            patient_id=1,
            db=self.db,
            current_account=self.account
        )

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["estado"], "FINALIZADA")
        self.assertEqual(
            response[0]["retinopatia_diabetica"]["confianza"],
            0.9435707330703735
        )
        self.assertEqual(
            response[0]["glaucoma"]["resultado"],
            "Bajo riesgo de Glaucoma"
        )

        get_ai.assert_called_once_with(
            db=self.db,
            establishment_id=1,
            evaluation_id=4
        )

    @patch("app.api.routes.evaluations.get_ai_evaluation_results")
    @patch("app.api.routes.evaluations.get_patient_evaluations")
    def test_pendiente_con_resultados(self, get_evaluations, get_ai):
        get_evaluations.return_value = [
            self.evaluation(estado="PENDIENTE")
        ]
        get_ai.return_value = self.ai_results()

        response = list_patient_evaluations(
            patient_id=1,
            db=self.db,
            current_account=self.account
        )

        self.assertEqual(response[0]["estado"], "PENDIENTE")
        self.assertIsNotNone(
            response[0]["retinopatia_diabetica"]
        )
        self.assertIsNotNone(response[0]["glaucoma"])

    @patch("app.api.routes.evaluations.get_ai_evaluation_results")
    @patch("app.api.routes.evaluations.get_patient_evaluations")
    def test_evaluacion_sin_analisis(self, get_evaluations, get_ai):
        get_evaluations.return_value = [
            self.evaluation(estado="PENDIENTE")
        ]
        get_ai.side_effect = AIResultsNotAvailableError()

        response = list_patient_evaluations(
            patient_id=1,
            db=self.db,
            current_account=self.account
        )

        self.assertIsNone(
            response[0]["retinopatia_diabetica"]
        )
        self.assertIsNone(response[0]["glaucoma"])

    @patch("app.api.routes.evaluations.get_patient_evaluations")
    def test_paciente_inexistente(self, get_evaluations):
        get_evaluations.side_effect = EvaluationPatientNotFoundError()

        with self.assertRaises(HTTPException) as context:
            list_patient_evaluations(
                patient_id=999,
                db=self.db,
                current_account=self.account
            )

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
