"""Teste HTTP integrado do POST do painel, com cadastro local fictício."""
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
import re
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from painel_local import criar_handler


class FormularioHTTPTests(unittest.TestCase):
    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.base = Path(self.pasta.name)
        self.clientes = [
            {"id": str(i), "unidade": f"Unidade {i}",
             "cnpj": f"{i:014d}", "razao_social": f"Empresa teste {i}",
             "campos_fiscais": {"regime": "teste"}} for i in range(1, 9)
        ]
        self.token = "token-de-teste"
        self.mock = patch("painel_local.carrega_clientes", return_value=self.clientes)
        self.mock.start()
        self.addCleanup(self.mock.stop)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), criar_handler(self.token, self.base / "clientes.json", self.base))
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(self.thread.join)
        self.addCleanup(self.pasta.cleanup)
        self.root = f"http://127.0.0.1:{self.server.server_port}"

    def test_post_browser_local_com_origem(self):
        with urlopen(self.root + "/") as r:
            html = r.read().decode()
            self.assertIn('name="token" value="token-de-teste"', html)
        params = {"token": self.token, "competencia": "2026-12-01",
                  "vencimento": "2026-12-20", "descricao": "Serviço de teste do painel"}
        params.update({f"valor_{i}": "500.00" for i in range(8)})
        req = Request(self.root + "/criar", data=urlencode(params).encode(),
                      headers={"Origin": self.root}, method="POST")
        with urlopen(req) as response:
            body = response.read().decode()
            self.assertEqual(response.status, 200)
            self.assertIn("Prévia privada salva", body)
        self.assertEqual(len(list(self.base.glob("lotes-painel/*/manifesto.json"))), 1)

    def test_post_com_token_invalido_rejeitado(self):
        params = {"token": "token-invalido"}
        req = Request(self.root + "/criar", data=urlencode(params).encode(),
                      headers={"Origin": self.root}, method="POST")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 403)
        self.assertIn("Formulário expirado", ctx.exception.read().decode())
        self.assertFalse((self.base / "lotes-painel").exists())

    def test_post_cross_origin_rejeitado(self):
        req = Request(self.root + "/criar", data=b"token=token-de-teste",
                      headers={"Origin": "https://outro-site.example"}, method="POST")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 403)
        self.assertIn("Origem do formulário", ctx.exception.read().decode())
        self.assertFalse((self.base / "lotes-painel").exists())


if __name__ == "__main__":
    unittest.main()
