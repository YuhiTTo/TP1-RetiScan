import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.schemas.evaluation import EvaluationFinalizeRequest
from app.services.ai_results_service import AIResultsNotAvailableError
from app.services.evaluation_finalization_service import (
    EvaluationFinalizationNotFoundError,
    EvaluationAlreadyFinalizedError,
    EvaluationInvalidStateError,
    EvaluationFinalizationResultsNotAvailableError,
    finalize_evaluation,
)


class TestFinalizationSchema(unittest.TestCase):

    def test_observacion_opcional(self):
        data = EvaluationFinalizeRequest()
        self.assertIsNone(data.observacion_medica)

    def test_observacion_vacia(self):
        for text in ("", "   "):
            data = EvaluationFinalizeRequest(
                observacion_medica=text
            )
            self.assertIsNone(data.observacion_medica)

    def test_observacion_valida(self):
        data = EvaluationFinalizeRequest(
            observacion_medica="  Observacion de prueba  "
        )
        self.assertEqual(
            data.observacion_medica,
            "Observacion de prueba"
        )

    def test_limite_caracteres(self):
        data = EvaluationFinalizeRequest(
            observacion_medica="A" * 1000
        )
        self.assertEqual(len(data.observacion_medica), 1000)

        with self.assertRaises(ValidationError):
            EvaluationFinalizeRequest(
                observacion_medica="A" * 1001
            )


class TestFinalizationService(unittest.TestCase):

    def setUp(self):
        self.db = Mock()
        self.evaluation = SimpleNamespace(
            id_evaluacion=42,
            id_establecimiento=10,
            estado="PENDIENTE",
            observacion_medica=None,
            fecha_finalizacion=None,
        )

        self.db.execute.return_value.scalar_one_or_none.return_value = (
            self.evaluation
        )

        self.results_patch = patch(
            "app.services.evaluation_finalization_service."
            "get_ai_evaluation_results"
        )

        self.results = self.results_patch.start()
        self.addCleanup(self.results_patch.stop)

    def finalize(self, observation=None):
        return finalize_evaluation(
            db=self.db,
            establishment_id=10,
            evaluation_id=42,
            observation=observation
        )

    def test_finalizar_con_observacion(self):
        result = self.finalize("Observacion inicial")

        self.assertEqual(result.estado, "FINALIZADA")
        self.assertEqual(
            result.observacion_medica,
            "Observacion inicial"
        )
        self.assertIsInstance(
            result.fecha_finalizacion,
            datetime
        )

        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(
            self.evaluation
        )

        self.results.assert_called_once_with(
            db=self.db,
            establishment_id=10,
            evaluation_id=42
        )

    def test_finalizar_sin_observacion(self):
        result = self.finalize()

        self.assertEqual(result.estado, "FINALIZADA")
        self.assertIsNone(result.observacion_medica)
        self.db.commit.assert_called_once()

    def test_evaluacion_inexistente(self):
        self.db.execute.return_value.scalar_one_or_none.return_value = None

        with self.assertRaises(
            EvaluationFinalizationNotFoundError
        ):
            self.finalize("Intento")

        self.db.commit.assert_not_called()
        self.results.assert_not_called()

    def test_evaluacion_ya_finalizada(self):
        self.evaluation.estado = "FINALIZADA"

        with self.assertRaises(
            EvaluationAlreadyFinalizedError
        ):
            self.finalize("Intento")

        self.db.commit.assert_not_called()
        self.results.assert_not_called()

    def test_estado_no_permitido(self):
        self.evaluation.estado = "CANCELADA"

        with self.assertRaises(
            EvaluationInvalidStateError
        ):
            self.finalize("Intento")

        self.db.commit.assert_not_called()
        self.results.assert_not_called()

    def test_resultados_ia_incompletos(self):
        self.results.side_effect = AIResultsNotAvailableError()

        with self.assertRaises(
            EvaluationFinalizationResultsNotAvailableError
        ):
            self.finalize("Intento")

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_error_al_guardar(self):
        self.db.commit.side_effect = RuntimeError(
            "Error simulado de persistencia"
        )

        with self.assertRaises(RuntimeError):
            self.finalize("Intento")

        self.db.rollback.assert_called_once()

    def test_consulta_por_establecimiento_con_bloqueo(self):
        self.finalize("Prueba")

        statement = self.db.execute.call_args.args[0]

        sql = str(
            statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True}
            )
        )

        self.assertIn("FOR UPDATE", sql)
        self.assertIn("id_evaluacion = 42", sql)
        self.assertIn("id_establecimiento = 10", sql)


if __name__ == "__main__":
    unittest.main()
