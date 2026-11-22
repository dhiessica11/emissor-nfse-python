import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from emissor.core import (
    ValidationError, carrega_clientes, cnpj_valido,
    competencia_valida, conectar, gravar_simulacoes, status,
)

ROOT = Path(__file__).resolve().parents[1]
EXEMPLO = ROOT / "config" / "clientes.exemplo.json"


class CoreTests(unittest.TestCase):
    def test_cnpj(self):
        self.assertTrue(cnpj_valido("11.222.333/0001-81"))
        self.assertFalse(cnpj_valido("11.222.333/0001-82"))
        self.assertFalse(cnpj_valido("00.000.000/0000-00"))

    def test_competencia(self):
        self.assertEqual(competencia_valida("2026-11"), "2026-11")
        for invalid in ("2026-13", "2026-00", "26-11", "abcd-11"):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                competencia_valida(invalid)

    def test_cadastro_publico(self):
        clients = carrega_clientes(EXEMPLO)
        self.assertEqual(len(clients), 8)
        self.assertEqual(len({c["cnpj"] for c in clients}), 8)

    def test_oito_clientes_obrigatorios(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "clientes.json"
            file.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValidationError):
                carrega_clientes(file)

    def test_cadastro_sem_unidade(self):
        with tempfile.TemporaryDirectory() as temp:
            clients = json.loads(EXEMPLO.read_text(encoding="utf-8"))
            del clients[0]["unidade"]
            file = Path(temp) / "clientes.json"
            file.write_text(json.dumps(clients), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "unidade"):
                carrega_clientes(file)

    def test_valor_negativo_bloqueado(self):
        with tempfile.TemporaryDirectory() as temp:
            clients = json.loads(EXEMPLO.read_text(encoding="utf-8"))
            clients[0]["valor"] = "-1.00"
            file = Path(temp) / "clientes.json"
            file.write_text(json.dumps(clients), encoding="utf-8")
            with self.assertRaises(ValidationError):
                carrega_clientes(file)

    def test_simulacao_e_idempotencia(self):
        clients = carrega_clientes(EXEMPLO)
        with tempfile.TemporaryDirectory() as temp:
            db = conectar(Path(temp) / "historico.sqlite3")
            gravar_simulacoes(db, clients, "2026-11")
            gravar_simulacoes(db, clients, "2026-11")
            self.assertTrue(all(status(db, c["id"], "2026-11") == "SIMULADA" for c in clients))
            db.close()

    def test_transmitida_nao_pode_virar_simulada(self):
        clients = carrega_clientes(EXEMPLO)
        with tempfile.TemporaryDirectory() as temp:
            db = conectar(Path(temp) / "historico.sqlite3")
            with db:
                db.execute(
                    "INSERT INTO emissao(cliente_id, competencia, estado, atualizado_em) VALUES(?,?,?,?)",
                    (clients[0]["id"], "2026-11", "TRANSMITIDA", "2026-11-22T00:00:00Z"),
                )
            with self.assertRaisesRegex(ValidationError, "consulte o portal"):
                gravar_simulacoes(db, clients, "2026-11")
            self.assertIsNone(status(db, clients[1]["id"], "2026-11"))
            db.close()

    def test_previa_cli_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            run = subprocess.run(
                [sys.executable, str(ROOT / "emitir.py"), "--competencia", "2026-12",
                 "--cadastro", str(EXEMPLO), "--db", str(Path(temp) / "historico.sqlite3")],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("Total: R$ 800.00", run.stdout)
            self.assertIn("NÃO EMITE NOTAS", run.stdout)

    def test_cancelamento_cli_sem_registro(self):
        with tempfile.TemporaryDirectory() as temp:
            db_file = Path(temp) / "historico.sqlite3"
            run = subprocess.run(
                [sys.executable, str(ROOT / "emitir.py"), "--competencia", "2026-12",
                 "--vencimento", "2027-01-01", "--simular",
                 "--cadastro", str(EXEMPLO), "--db", str(db_file)],
                input="NAO\n", text=True, capture_output=True, check=False,
            )
            self.assertEqual(run.returncode, 1, run.stderr)
            self.assertIn("Cancelado.", run.stdout)
            db = conectar(db_file)
            self.assertEqual(db.execute("SELECT count(*) FROM emissao").fetchone()[0], 0)
            db.close()


if __name__ == "__main__":
    unittest.main()
