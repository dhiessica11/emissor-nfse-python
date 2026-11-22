import unittest

from preparar_previas_dezembro import (
    COMPETENCIA, VENCIMENTO, DESCRICAO, gerar_previas,
)


class PreviaDezembroTests(unittest.TestCase):
    def setUp(self):
        self.clientes = [{
            "id": f"cliente_{i:02d}", "unidade": f"Unidade {i}",
            "cnpj": f"00000000{i:02d}0001", "razao_social": f"Empresa fictícia {i}",
            "campos_fiscais": {"regime_referencia": "A CONFERIR"},
        } for i in range(1, 9)]

    def test_oito_previas_valor_e_descricao(self):
        previas = gerar_previas(self.clientes)
        self.assertEqual(len(previas), 8)
        for item in previas:
            self.assertEqual(item["valor"], "500.00")
            self.assertEqual(item["competencia"], "2026-12")
            self.assertEqual(item["vencimento"], "2026-12-20")
            self.assertEqual(item["descricao_servico"], DESCRICAO)
            self.assertEqual(item["situacao"], "PREVIA_NAO_TRANSMITIDA")
        self.assertIn("décimo terceiro contratual", DESCRICAO)

    def test_nao_aceita_quantidade_diferente(self):
        with self.assertRaises(ValueError):
            gerar_previas(self.clientes[:7])

    def test_nao_modifica_cadastro(self):
        originais = [dict(c) for c in self.clientes]
        gerar_previas(self.clientes)
        self.assertEqual(self.clientes, originais)


if __name__ == "__main__":
    unittest.main()
