import unittest
from datetime import date

from auditar_data_emissao_dezembro import avaliar_data


class AuditoriaDatasTests(unittest.TestCase):
    def test_primeiro_de_dezembro_bloqueado(self):
        ok, msg = avaliar_data(date(2026, 12, 1))
        self.assertFalse(ok)
        self.assertIn("E0015", msg)

    def test_dezenove_de_dezembro_bloqueado(self):
        ok, _ = avaliar_data(date(2026, 12, 19))
        self.assertFalse(ok)

    def test_vinte_de_dezembro_cronologicamente_possivel(self):
        ok, _ = avaliar_data(date(2026, 12, 20))
        self.assertTrue(ok)

    def test_depois_da_competencia_cronologicamente_possivel(self):
        ok, _ = avaliar_data(date(2026, 12, 21))
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
