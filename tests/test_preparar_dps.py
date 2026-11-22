import unittest
from lxml import etree

from emissor.homologacao import construir_dps, NAMESPACE
from preparar_dps_referencia import extrair_dados
from tests.test_homologacao import dados_ficticios


class ConversaoTests(unittest.TestCase):
    def test_refazer_dps_nova_sem_reutilizar_id(self):
        base = dados_ficticios()
        base["descricao_servico"] = "SUPORTE EM TECNOLOGIA. Vencimento: 01/12/2026"
        previous = construir_dps(base)
        nfse = etree.Element(f"{{{NAMESPACE}}}NFSe", nsmap={None: NAMESPACE})
        nfse.append(etree.fromstring(previous))
        converted = extrair_dados(
            etree.tostring(nfse), 1, 900099, "2026-12-01", "01/01/2027"
        )
        self.assertEqual(converted["serie"], "1")
        self.assertEqual(converted["numero_dps"], 900099)
        self.assertEqual(converted["competencia"], "2026-12-01")
        self.assertIn("Vencimento: 01/01/2027", converted["descricao_servico"])
        self.assertNotIn("Vencimento: 01/12/2026", converted["descricao_servico"])

    def test_impede_serie_reservada_ao_portal_web(self):
        base = dados_ficticios()
        base["descricao_servico"] = "Teste Vencimento: 01/12/2026"
        with self.assertRaises(ValueError):
            extrair_dados(
                construir_dps(base), 70000, 900099, "2026-12-01", "01/01/2027"
            )


if __name__ == "__main__":
    unittest.main()
