import tempfile
import unittest
from pathlib import Path

from emissor.core import (
    ValidationError, carrega_clientes, cnpj_valido,
    competencia_valida, conectar, gravar_simulacoes, status,
)


class CoreTests(unittest.TestCase):
    def test_cnpj(self):
        self.assertTrue(cnpj_valido("11.222.333/0001-81"))
        self.assertFalse(cnpj_valido("11.222.333/0001-82"))
        self.assertFalse(cnpj_valido("00.000.000/0000-00"))

    def test_competencia(self):
        self.assertEqual(competencia_valida("2026-11"), "2026-11")
        with self.assertRaises(ValidationError):
            competencia_valida("2026-13")

    def test_oito_clientes_obrigatorios(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "clientes.json"
            file.write_text("[]")
            with self.assertRaises(ValidationError):
                carrega_clientes(file)

    def test_simulacao(self):
        with tempfile.TemporaryDirectory() as temp:
            db = conectar(Path(temp) / "historico.sqlite3")
            gravar_simulacoes(db, [{"id": "teste"}], "2026-11")
            self.assertEqual(status(db, "teste", "2026-11"), "SIMULADA")
            db.close()


if __name__ == "__main__":
    unittest.main()
