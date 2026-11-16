import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pydantic import ValidationError

from app.schemas.evaluation import MedicalObservationUpdate
from app.services.medical_observation_service import (
    MedicalObservationNotFoundError,
    MedicalObservationResultsNotAvailableError,
    MedicalObservationNotFinalizedError,
    save_medical_observation,
)
from app.services.ai_results_service import AIResultsNotAvailableError


class TestMedicalObservationSchema(unittest.TestCase):

    def test_elimina_espacios(self):
        data = MedicalObservationUpdate(
            observacion_medica="  Observacion de prueba  "
        )
        self.assertEqual(
            data.observacion_medica,
            "Observacion de prueba"
        )

    def test_limite_de_caracteres(self):
        data = MedicalObservationUpdate(
            observacion_medica="A" * 1000
        )
        self.assertEqual(len(data.observacion_medica), 1000)

        with self.assertRaises(ValidationError):
            MedicalObservationUpdate(
                observacion_medica="A" * 1001
            )

    def test_observacion_vacia(self):
        with self.assertRaises(ValidationError):
            MedicalObservationUpdate(
                observacion_medica="   "
            )


class TestMedicalObservationService(unittest.TestCase):

    def setUp(self):
        self.db = Mock()
        self.evaluation = SimpleNamespace(
            id_evaluacion=1,
            estado="FINALIZADA",
            observacion_medica=None
        )

        self.lookup_patch = patch(
            "app.services.medical_observation_service."
            "get_evaluation_by_id",
            return_value=self.evaluation
        )

        self.results_patch = patch(
            "app.services.medical_observation_service."
            "get_ai_evaluation_results"
        )

        self.lookup = self.lookup_patch.start()
        self.results = self.results_patch.start()

        self.addCleanup(self.lookup_patch.stop)
        self.addCleanup(self.results_patch.stop)

    def save(self, text):
        return save_medical_observation(
            db=self.db,
            establishment_id=1,
            evaluation_id=1,
            observation=text
        )

    def test_registrar_observacion(self):
        result = self.save("Primera observacion")

        self.assertEqual(
            result.observacion_medica,
            "Primera observacion"
        )
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(
            self.evaluation
        )

    def test_modificar_observacion(self):
        self.evaluation.observacion_medica = "Anterior"

        result = self.save("Actualizada")

        self.assertEqual(
            result.observacion_medica,
            "Actualizada"
        )
        self.db.commit.assert_called_once()

    def test_evaluacion_inexistente(self):
        self.lookup.return_value = None

        with self.assertRaises(
            MedicalObservationNotFoundError
        ):
            self.save("Intento de prueba")

        self.db.commit.assert_not_called()

    def test_resultados_ia_no_disponibles(self):
        self.results.side_effect = (
            AIResultsNotAvailableError()
        )

        with self.assertRaises(
            MedicalObservationResultsNotAvailableError
        ):
            self.save("Intento de prueba")

        self.db.commit.assert_not_called()

    def test_evaluacion_pendiente(self):
        self.evaluation.estado = "PENDIENTE"
        self.evaluation.observacion_medica = "Original"

        with self.assertRaises(
            MedicalObservationNotFinalizedError
        ):
            self.save("Intento de modificacion")

        self.assertEqual(
            self.evaluation.observacion_medica,
            "Original"
        )
        self.db.commit.assert_not_called()
        self.results.assert_not_called()


if __name__ == "__main__":
    unittest.main()
