import unittest

from pydantic import ValidationError

from app.schemas.evaluation import (
    EvaluationHistoryModelResult,
    EvaluationListResponse,
)


class TestUS19HistorySchemas(unittest.TestCase):

    def test_resultado_valido(self):
        result = EvaluationHistoryModelResult(
            resultado="Moderada",
            confianza=0.3937
        )

        self.assertEqual(result.resultado, "Moderada")
        self.assertEqual(result.confianza, 0.3937)

    def test_confianza_limites_validos(self):
        for confidence in (0, 1):
            with self.subTest(confidence=confidence):
                result = EvaluationHistoryModelResult(
                    resultado="Resultado de prueba",
                    confianza=confidence
                )
                self.assertEqual(result.confianza, confidence)

    def test_confianza_negativa_rechazada(self):
        with self.assertRaises(ValidationError):
            EvaluationHistoryModelResult(
                resultado="Moderada",
                confianza=-0.1
            )

    def test_confianza_mayor_a_uno_rechazada(self):
        with self.assertRaises(ValidationError):
            EvaluationHistoryModelResult(
                resultado="Moderada",
                confianza=1.1
            )

    def test_ambas_patologias_en_historial(self):
        fields = EvaluationListResponse.model_fields

        self.assertIn("retinopatia_diabetica", fields)
        self.assertIn("glaucoma", fields)

    def test_resultados_opcionales_en_historial(self):
        fields = EvaluationListResponse.model_fields

        self.assertIsNone(
            fields["retinopatia_diabetica"].default
        )
        self.assertIsNone(
            fields["glaucoma"].default
        )


if __name__ == "__main__":
    unittest.main()
