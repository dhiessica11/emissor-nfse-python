import base64
import gzip
import json
import unittest
from extrair_nfse_restrita import extrair_resposta


class ExtracaoNFSeTests(unittest.TestCase):
    def setUp(self):
        self.xml = (b'<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">'
                    b'<infNFSe Id="NFSeTESTE"/></NFSe>')
        self.body = {
            "tipoAmbiente": 2,
            "chaveAcesso": "CHAVE_FICTICIA_TESTE",
            "nfseXmlGZipB64": base64.b64encode(gzip.compress(self.xml)).decode(),
            "alertas": [],
        }
        self.registro = {
            "http_status": 201,
            "ambiente": "PRODUCAO_RESTRITA",
            "body": json.dumps(self.body),
        }

    def test_extrai_xml_de_retorno_valido(self):
        response, xml = extrair_resposta(self.registro)
        self.assertEqual(xml, self.xml)
        self.assertEqual(response["tipoAmbiente"], 2)

    def test_rejeita_resposta_http_sem_autorizacao(self):
        self.registro["http_status"] = 400
        with self.assertRaises(ValueError):
            extrair_resposta(self.registro)

    def test_rejeita_ambiente_de_producao(self):
        self.body["tipoAmbiente"] = 1
        self.registro["body"] = json.dumps(self.body)
        with self.assertRaises(ValueError):
            extrair_resposta(self.registro)

    def test_rejeita_xml_invalido(self):
        self.body["nfseXmlGZipB64"] = base64.b64encode(
            gzip.compress(b'<DPS/>')).decode()
        self.registro["body"] = json.dumps(self.body)
        with self.assertRaises(ValueError):
            extrair_resposta(self.registro)


if __name__ == "__main__":
    unittest.main()
