import unittest
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

import app.services.evaluation_service as service
from app.models.doctor import Doctor
from app.models.evaluation import RetinalEvaluation
from app.schemas.evaluation import EvaluationUpdate


class TestEdicionEvaluacion(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

        self.evaluation = RetinalEvaluation(
            id_evaluacion=18,
            id_paciente=1,
            id_medico=10,
            id_establecimiento=1,
            fecha_evaluacion=datetime(2026, 11, 19),
            ojo_evaluado="OD",
            estado="PENDIENTE"
        )

        self.evaluation_query = MagicMock()
        self.evaluation_query.scalar_one_or_none.return_value = (
            self.evaluation
        )

        self.analysis_query = MagicMock()
        self.analysis_query.first.return_value = None

        self.db.execute.side_effect = [
            self.evaluation_query,
            self.analysis_query,
            MagicMock()
        ]

        doctor_patch = patch.object(
            service,
            "find_doctors_by_full_name",
            return_value=[
                SimpleNamespace(
                    id_medico=10,
                    estado=True
                )
            ]
        )

        self.doctor_lookup = doctor_patch.start()
        self.addCleanup(doctor_patch.stop)

    def update(self, name="Ana Torres", eye="OI"):
        data = EvaluationUpdate(
            fecha_evaluacion=date(2026, 11, 18),
            ojo_evaluado=eye,
            medico_responsable=name
        )

        return service.update_evaluation(
            db=self.db,
            establishment_id=1,
            evaluation_id=18,
            data=data
        )

    def test_actualiza_sin_duplicar(self):
        result = self.update()

        self.assertEqual(result.id_evaluacion, 18)
        self.assertEqual(result.id_paciente, 1)
        self.assertEqual(result.ojo_evaluado, "OI")
        self.assertEqual(
            result.fecha_evaluacion.date(),
            date(2026, 11, 18)
        )
        self.assertEqual(result.id_medico, 10)

        self.db.add.assert_not_called()
        self.db.commit.assert_called_once()
        self.db.rollback.assert_not_called()

    def test_registra_medico_nuevo(self):
        self.doctor_lookup.return_value = []

        def simulate_flush():
            doctor = self.db.add.call_args.args[0]
            if isinstance(doctor, Doctor):
                doctor.id_medico = 31

        self.db.flush.side_effect = simulate_flush

        result = self.update("Lucia Torres")

        self.assertEqual(result.id_evaluacion, 18)
        self.assertEqual(result.id_medico, 31)

        doctor = self.db.add.call_args.args[0]
        self.assertIsInstance(doctor, Doctor)
        self.assertEqual(doctor.nombres, "Lucia")
        self.assertEqual(doctor.apellidos, "Torres")

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_evaluacion_inexistente(self):
        self.evaluation_query.scalar_one_or_none.return_value = None

        with self.assertRaises(
            service.EvaluationNotFoundError
        ):
            self.update()

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_rechaza_evaluacion_finalizada(self):
        self.evaluation.estado = "FINALIZADA"

        with self.assertRaises(
            service.EvaluationNotEditableError
        ):
            self.update()

        self.db.commit.assert_not_called()
        self.doctor_lookup.assert_not_called()

    def test_rechaza_analisis_iniciado(self):
        self.analysis_query.first.return_value = (25, "CARGADA", 15)

        with self.assertRaises(
            service.EvaluationNotEditableError
        ):
            self.update()

        self.db.commit.assert_not_called()
        self.doctor_lookup.assert_not_called()

    def test_rechaza_cambio_ojo_con_retinografia(self):
        self.analysis_query.first.return_value = (
            25, "CARGADA", None
        )

        with self.assertRaises(
            service.EvaluationEyeChangeNotAllowedError
        ):
            self.update()

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()
        self.doctor_lookup.assert_not_called()

    def test_permite_otros_datos_con_retinografia(self):
        self.evaluation.ojo_evaluado = "OI"

        self.analysis_query.first.return_value = (
            25, "CARGADA", None
        )

        result = self.update()

        self.assertEqual(result.id_evaluacion, 18)
        self.assertEqual(result.ojo_evaluado, "OI")
        self.assertEqual(
            result.fecha_evaluacion.date(),
            date(2026, 11, 18)
        )

        self.db.commit.assert_called_once()
        self.db.rollback.assert_not_called()

    def test_rechaza_medicos_ambiguos(self):
        self.doctor_lookup.return_value = [
            SimpleNamespace(id_medico=10, estado=True),
            SimpleNamespace(id_medico=11, estado=True)
        ]

        with self.assertRaises(
            service.EvaluationDoctorAmbiguousError
        ):
            self.update()

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_rechaza_medico_inactivo(self):
        self.doctor_lookup.return_value = [
            SimpleNamespace(id_medico=10, estado=False)
        ]

        with self.assertRaises(
            service.EvaluationDoctorInactiveError
        ):
            self.update()

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_rollback_ante_error(self):
        self.db.commit.side_effect = IntegrityError(
            "UPDATE",
            {},
            Exception("Error simulado")
        )

        with self.assertRaises(IntegrityError):
            self.update()

        self.db.rollback.assert_called_once()
        self.db.refresh.assert_not_called()

    def test_validaciones_del_esquema(self):
        with self.assertRaises(ValidationError):
            EvaluationUpdate(
                fecha_evaluacion=date(2026, 11, 19),
                ojo_evaluado="XX",
                medico_responsable="Ana Torres"
            )

        with self.assertRaises(ValidationError):
            EvaluationUpdate(
                fecha_evaluacion=date(2026, 11, 19),
                ojo_evaluado="OD",
                medico_responsable="Ana"
            )


if __name__ == "__main__":
    unittest.main()
