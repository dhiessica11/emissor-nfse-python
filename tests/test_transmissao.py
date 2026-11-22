import unittest
from transmitir_teste_restrito import validar_cnpj_confirmacao


class ConfirmacaoCNPJTests(unittest.TestCase):
    def test_aceita_cnpj_numerico(self):
        self.assertEqual(
            validar_cnpj_confirmacao("11222333000181", "11222333000181"),
            "11222333000181",
        )

    def test_aceita_cnpj_formatado(self):
        self.assertEqual(
            validar_cnpj_confirmacao("11.222.333/0001-81", "11222333000181"),
            "11222333000181",
        )

    def test_rejeita_cnpj_diferente(self):
        with self.assertRaises(ValueError):
            validar_cnpj_confirmacao("11222333000182", "11222333000181")

    def test_rejeita_quantidade_incorreta(self):
        with self.assertRaises(ValueError):
            validar_cnpj_confirmacao("1234", "11222333000181")


if __name__ == "__main__":
    unittest.main()
