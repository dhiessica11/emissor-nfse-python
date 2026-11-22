import tempfile
import unittest
from pathlib import Path
import json

from preparar_rascunhos_dps_dezembro import montar_rascunhos, salvar_diretorio_novo


def cnpj_teste(n):
    base = f"{n:08d}0001"
    for pesos in ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
                  [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]):
        v = 11 - sum(int(a) * b for a, b in zip(base, pesos)) % 11
        base += str(0 if v >= 10 else v)
    return base


class RascunhosTests(unittest.TestCase):
    def setUp(self):
        self.fiscal = {
            "municipio_emissor": "5003702",
            "prestador_cnpj": cnpj_teste(91827364),
            "op_simp_nac": "3", "reg_ap_trib_sn": "2",
            "reg_esp_trib": "0", "trib_issqn": "1",
            "ret_issqn": "1", "cst_pis_cofins": "00",
            "ret_pis_cofins": "0", "percentual_total_tributos_sn": "2.00",
        }
        self.cadastro = []
        self.docs = []
        for i in range(1, 9):
            cf = {
                "codigo_tributacao_nacional": "010701",
                "codigo_nbs": "115011000", "municipio_prestacao_ibge": "5003702",
                "iss_retido": False, "regime_referencia": "REVISAR"
            }
            cliente = {
                "id": f"cliente_{i}", "unidade": f"Unidade {i}",
                "cnpj": cnpj_teste(i + 100), "razao_social": f"Empresa fictícia {i}",
                "codigo_ibge_tomador": "5107909", "cep_tomador": "78555900",
                "logradouro_tomador": "TESTE", "numero_endereco_tomador": "1",
                "bairro_tomador": "TESTE", "campos_fiscais": cf,
            }
            self.cadastro.append(cliente)
            self.docs.append({
                "id": cliente["id"], "tomador_cnpj": cliente["cnpj"],
                "tomador_razao_social": cliente["razao_social"],
                "competencia": "2026-12", "vencimento": "2026-12-20",
                "valor": "500.00", "descricao_servico": "Serviços fictícios para teste",
                "situacao": "PREVIA_NAO_TRANSMITIDA",
                "campos_fiscais_referencia": cf,
            })
        self.previas = {
            "tipo": "PREVIA_OFFLINE_SEM_EMISSAO",
            "competencia": "2026-12", "vencimento": "2026-12-20",
            "quantidade": 8, "valor_total": "4000.00",
            "documentos": self.docs,
        }

    def test_oito_rascunhos_sem_datas_e_sem_xml(self):
        docs = montar_rascunhos(self.previas, self.cadastro, self.fiscal, 900003)
        self.assertEqual(len(docs), 8)
        self.assertEqual([d["dados_preparatorios"]["numero_dps"] for d in docs],
                         list(range(900003, 900011)))
        for doc in docs:
            dados = doc["dados_preparatorios"]
            self.assertIsNone(dados["competencia"])
            self.assertIsNone(dados["data_emissao"])
            self.assertEqual(dados["valor"], "500.00")
            self.assertEqual(doc["situacao"], "PENDENTE_VALIDACAO_FISCAL_E_DATAS")

    def test_rejeita_divergencia_cnpj(self):
        self.previas["documentos"][0]["tomador_cnpj"] = cnpj_teste(999)
        with self.assertRaises(ValueError):
            montar_rascunhos(self.previas, self.cadastro, self.fiscal, 900003)

    def test_bloqueia_numeros_anteriores(self):
        with self.assertRaises(ValueError):
            montar_rascunhos(self.previas, self.cadastro, self.fiscal, 900002)

    def test_diretorio_exclusivo_e_permissoes(self):
        docs = montar_rascunhos(self.previas, self.cadastro, self.fiscal, 900003)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "privado"
            salvar_diretorio_novo(dest, docs)
            self.assertEqual(len(list(dest.glob("rascunho-*.json"))), 8)
            self.assertTrue((dest / "manifesto.json").exists())
            self.assertEqual((dest / "rascunho-01.json").stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                salvar_diretorio_novo(dest, docs)


if __name__ == "__main__":
    unittest.main()
