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
            observacion_medica=None,
        )

        self.set_results(self.evaluation, None)

        self.results_patch = patch(
            "app.services.report_update_service."
            "get_ai_evaluation_results",
            return_value={},
        )

        self.results = self.results_patch.start()
        self.addCleanup(self.results_patch.stop)

    def set_results(self, *values):
        self.db.execute.side_effect = [
            SimpleNamespace(
                scalar_one_or_none=lambda value=value: value
            )
            for value in values
        ]

    def save(self, text):
        return save_medical_observation(
            db=self.db,
            establishment_id=1,
            evaluation_id=1,
            observation=text,
        )

    def test_registrar_observacion(self):
        with patch(
            "app.services.report_update_service.upload_report_pdf"
        ) as upload:
            result = self.save("Primera observacion")

        self.assertEqual(
            result.observacion_medica,
            "Primera observacion",
        )
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(self.evaluation)
        upload.assert_not_called()

    def test_modificar_observacion(self):
        self.evaluation.observacion_medica = "Anterior"

        result = self.save("Actualizada")

        self.assertEqual(
            result.observacion_medica,
            "Actualizada",
        )
        self.db.commit.assert_called_once()

    def test_evaluacion_inexistente(self):
        self.set_results(None)

        with self.assertRaises(MedicalObservationNotFoundError):
            self.save("Intento de prueba")

        self.db.commit.assert_not_called()
        self.results.assert_not_called()

    def test_resultados_ia_no_disponibles(self):
        self.results.side_effect = AIResultsNotAvailableError()

        with self.assertRaises(
            MedicalObservationResultsNotAvailableError
        ):
            self.save("Intento de prueba")

        self.db.commit.assert_not_called()

    def test_evaluacion_pendiente(self):
        self.evaluation.estado = "PENDIENTE"
        self.evaluation.observacion_medica = "Original"

        with self.assertRaises(MedicalObservationNotFinalizedError):
            self.save("Intento de modificacion")

        self.assertEqual(
            self.evaluation.observacion_medica,
            "Original",
        )
        self.db.commit.assert_not_called()
        self.results.assert_not_called()

    def test_guardar_observacion_sin_cambios(self):
        self.evaluation.observacion_medica = "Misma observacion"

        with patch(
            "app.services.report_update_service.upload_report_pdf"
        ) as upload:
            result = self.save("Misma observacion")

        self.assertEqual(
            result.observacion_medica,
            "Misma observacion",
        )
        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()
        upload.assert_not_called()

    def test_actualizar_reporte_existente(self):
        self.evaluation.observacion_medica = "Anterior"

        old_path = (
            "s3://bucket-prueba/reportes/1/reporte-"
            + "a" * 32 + ".pdf"
        )
        new_path = (
            "s3://bucket-prueba/reportes/1/reporte-"
            + "b" * 32 + ".pdf"
        )

        report = SimpleNamespace(
            id_evaluacion=1,
            ruta_pdf_s3=old_path,
            version=1,
            fecha_generacion=None,
        )

        self.set_results(self.evaluation, report)

        with (
            patch(
                "app.services.report_update_service.prepare_report_data",
                return_value=(object(), b"imagen"),
            ) as prepare,
            patch(
                "app.services.report_update_service.generate_report_pdf",
                return_value=b"%PDF-1.4",
            ),
            patch(
                "app.services.report_update_service.upload_report_pdf",
                return_value=new_path,
            ) as upload,
            patch(
                "app.services.report_update_service.delete_report_pdf"
            ) as delete,
        ):
            result = self.save("Observacion actualizada")

        self.assertEqual(
            result.observacion_medica,
            "Observacion actualizada",
        )
        self.assertEqual(report.version, 2)
        self.assertEqual(report.ruta_pdf_s3, new_path)
        self.assertIsNotNone(report.fecha_generacion)

        prepare.assert_called_once_with(
            db=self.db,
            establishment_id=1,
            evaluation_id=1,
            report_version=2,
        )

        upload.assert_called_once()
        delete.assert_called_once_with(old_path)
        self.db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
