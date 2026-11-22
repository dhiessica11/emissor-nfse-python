import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from datetime import date

from painel_local import preparar_lote, painel_html, listar_lotes
from instalar_atalho_mac import instalar


class PainelLocalTests(unittest.TestCase):
    def setUp(self):
        self.clientes = [
            {"id": str(i), "unidade": f"Restaurante {i}",
             "cnpj": f"{i:014d}", "razao_social": f"Empresa de teste {i}",
             "campos_fiscais": {"codigo": "DEMO"}}
            for i in range(1, 9)
        ]
        self.campos = {"competencia": "2026-12-01", "vencimento": "2026-12-20",
                       "descricao": "Serviço de tecnologia da informação"}
        self.campos.update({f"valor_{i}": "500.00" for i in range(8)})

    def test_salva_oito_previas_sem_emissao(self):
        with TemporaryDirectory() as td:
            manifest = preparar_lote(self.campos, self.clientes, Path(td))
            self.assertEqual(manifest["quantidade"], 8)
            self.assertEqual(manifest["total"], "4000.00")
            self.assertEqual(manifest["situacao"], "PREVIA_NAO_EMITIDA")
            for doc in manifest["documentos"]:
                self.assertIsNone(doc["data_emissao"])
                self.assertIsNone(doc["numero_dps"])
            self.assertEqual(len(list(Path(td).glob("lotes-painel/*/manifesto.json"))), 1)
            self.assertEqual(len(listar_lotes(Path(td))), 1)

    def test_recusa_competencia_e_valor_invalidos(self):
        with TemporaryDirectory() as td:
            self.campos["competencia"] = "2026-12-33"
            with self.assertRaises(ValueError):
                preparar_lote(self.campos, self.clientes, Path(td))
            self.campos["competencia"] = "2026-12-01"
            self.campos["valor_0"] = "-1"
            with self.assertRaises(ValueError):
                preparar_lote(self.campos, self.clientes, Path(td))
            self.assertFalse((Path(td) / "lotes-painel").exists())

    def test_recusa_tomador_duplicado(self):
        with TemporaryDirectory() as td:
            self.clientes[1]["cnpj"] = self.clientes[0]["cnpj"]
            with self.assertRaises(ValueError):
                preparar_lote(self.campos, self.clientes, Path(td))

    def test_escapa_html_de_cliente(self):
        self.clientes[0]["unidade"] = "<script>alert(1)</script>"
        html = painel_html(self.clientes, [], "token")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("transmitir_teste_restrito.py", html)

    def test_instala_atalho_executavel(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            projeto = root / "projeto"
            (projeto / ".venv/bin").mkdir(parents=True)
            (projeto / ".venv/bin/python").write_text("")
            (projeto / "painel_local.py").write_text("")
            mesa = root / "Desktop"
            mesa.mkdir()
            caminho = instalar(mesa, projeto)
            self.assertTrue(caminho.exists())
            self.assertTrue(caminho.stat().st_mode & 0o100)
            with self.assertRaises(FileExistsError):
                instalar(mesa, projeto)


if __name__ == "__main__":
    unittest.main()
