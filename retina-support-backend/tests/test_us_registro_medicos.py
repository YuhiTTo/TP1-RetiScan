import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import IntegrityError

import app.services.evaluation_service as service
from app.models.doctor import Doctor
from app.models.evaluation import RetinalEvaluation
from app.schemas.evaluation import EvaluationCreate


class TestRegistroAutomaticoMedicos(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

        patient_patch = patch.object(
            service,
            "get_patient_by_id",
            return_value=SimpleNamespace(id_paciente=1)
        )

        doctor_patch = patch.object(
            service,
            "find_doctors_by_full_name",
            return_value=[]
        )

        self.patient_lookup = patient_patch.start()
        self.doctor_lookup = doctor_patch.start()

        self.addCleanup(patient_patch.stop)
        self.addCleanup(doctor_patch.stop)

    def create(self, name="Ana Torres"):
        data = EvaluationCreate(
            fecha_evaluacion=date(2026, 11, 19),
            ojo_evaluado="OD",
            medico_responsable=name
        )

        return service.create_evaluation(
            db=self.db,
            establishment_id=1,
            patient_id=1,
            data=data
        )

    def test_reutiliza_medico_existente(self):
        self.doctor_lookup.return_value = [
            SimpleNamespace(id_medico=2, estado=True)
        ]

        evaluation = self.create()

        self.assertEqual(evaluation.id_medico, 2)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.rollback.assert_not_called()

    def test_registra_medico_nuevo(self):
        def simulate_flush():
            for call in self.db.add.call_args_list:
                obj = call.args[0]
                if isinstance(obj, Doctor):
                    obj.id_medico = 99

        self.db.flush.side_effect = simulate_flush

        evaluation = self.create("Lucia Torres")

        objects = [
            call.args[0]
            for call in self.db.add.call_args_list
        ]

        doctors = [
            obj for obj in objects
            if isinstance(obj, Doctor)
        ]

        self.assertEqual(len(doctors), 1)
        self.assertEqual(doctors[0].nombres, "Lucia")
        self.assertEqual(doctors[0].apellidos, "Torres")
        self.assertEqual(doctors[0].id_establecimiento, 1)
        self.assertEqual(evaluation.id_medico, 99)

        self.db.flush.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.rollback.assert_not_called()

    def test_normaliza_espacios(self):
        self.doctor_lookup.return_value = [
            SimpleNamespace(id_medico=2, estado=True)
        ]

        evaluation = self.create("  ANA   TORRES  ")

        self.assertEqual(evaluation.id_medico, 2)

        self.doctor_lookup.assert_called_once_with(
            db=self.db,
            establishment_id=1,
            full_name="ANA TORRES"
        )

    def test_rechaza_nombre_ambiguo(self):
        self.doctor_lookup.return_value = [
            SimpleNamespace(id_medico=10, estado=True),
            SimpleNamespace(id_medico=11, estado=True)
        ]

        with self.assertRaises(
            service.EvaluationDoctorAmbiguousError
        ):
            self.create()

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()
        self.db.add.assert_not_called()

    def test_rechaza_medico_inactivo(self):
        self.doctor_lookup.return_value = [
            SimpleNamespace(id_medico=2, estado=False)
        ]

        with self.assertRaises(
            service.EvaluationDoctorInactiveError
        ):
            self.create()

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_rechaza_paciente_inexistente(self):
        self.patient_lookup.return_value = None

        with self.assertRaises(
            service.EvaluationPatientNotFoundError
        ):
            self.create("Medico Nuevo")

        self.doctor_lookup.assert_not_called()
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_rollback_si_falla_guardado(self):
        def simulate_flush():
            for call in self.db.add.call_args_list:
                obj = call.args[0]
                if isinstance(obj, Doctor):
                    obj.id_medico = 99

        self.db.flush.side_effect = simulate_flush

        self.db.commit.side_effect = IntegrityError(
            "INSERT",
            {},
            Exception("Error simulado")
        )

        with self.assertRaises(IntegrityError):
            self.create("Medico Nuevo")

        self.assertEqual(self.db.add.call_count, 2)
        self.db.commit.assert_called_once()
        self.db.rollback.assert_called_once()
        self.db.refresh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
