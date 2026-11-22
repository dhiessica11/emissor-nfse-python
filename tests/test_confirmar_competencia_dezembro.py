import unittest
from confirmar_competencia_dezembro import confirmar_competencia


class ConfirmarCompetenciaTests(unittest.TestCase):
    def setUp(self):
        self.docs = []
        for i in range(3, 11):
            self.docs.append({
                "tipo": "RASCUNHO_DPS_NAO_EMITIVEL",
                "situacao": "PENDENTE_VALIDACAO_FISCAL_E_DATAS",
                "unidade": f"Unidade {i}",
                "competencia_mes_confirmada": "2026-12",
                "vencimento": "2026-12-20",
                "id_dps_proposto_nao_reservado": f"PROPOSTO-{i}",
                "dados_preparatorios": {
                    "numero_dps": 900000 + i,
                    "tomador_cnpj": f"FICTICIO-{i}",
                    "valor": "500.00",
                    "competencia": None,
                    "data_emissao": None,
                },
                "pendencias_bloqueantes": [
                    "Confirmar dia da competência para dezembro/2026",
                    "Informar data real de emissão somente na execução futura",
                    "Validar enquadramento contratual e tributação de dezembro",
                ],
            })

    def test_confirma_oito_sem_data_emissao(self):
        novos = confirmar_competencia(self.docs)
        self.assertEqual(len(novos), 8)
        for novo, anterior in zip(novos, self.docs):
            self.assertEqual(novo["dados_preparatorios"]["competencia"], "2026-12-20")
            self.assertIsNone(novo["dados_preparatorios"]["data_emissao"])
            self.assertIsNone(anterior["dados_preparatorios"]["competencia"])
            self.assertEqual(novo["situacao"], "COMPETENCIA_CONFIRMADA_EMISSAO_E_FISCAL_PENDENTES")

    def test_nao_aceita_documentos_ja_datados(self):
        self.docs[0]["dados_preparatorios"]["competencia"] = "2026-12-20"
        with self.assertRaises(ValueError):
            confirmar_competencia(self.docs)

    def test_rejeita_numero_repetido(self):
        self.docs[1]["dados_preparatorios"]["numero_dps"] = 900003
        with self.assertRaises(ValueError):
            confirmar_competencia(self.docs)

    def test_rejeita_quantidade_errada(self):
        with self.assertRaises(ValueError):
            confirmar_competencia(self.docs[:7])


if __name__ == "__main__":
    unittest.main()
