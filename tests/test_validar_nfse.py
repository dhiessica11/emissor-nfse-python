import tempfile
import unittest
from pathlib import Path
from lxml import etree
from validar_nfse_restrita import localizar_xsd, validar_documento, resumo_nao_sensivel

NS = "http://www.sped.fazenda.gov.br/nfse"
SCHEMA = f"""<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
 targetNamespace="{NS}" xmlns:n="{NS}" elementFormDefault="qualified">
 <xs:element name="NFSe"><xs:complexType><xs:sequence>
 <xs:element name="infNFSe"><xs:complexType><xs:sequence>
 <xs:element name="nNFSe" type="xs:string" />
 </xs:sequence></xs:complexType></xs:element>
 </xs:sequence></xs:complexType></xs:element>
 </xs:schema>"""
XML = f'<NFSe xmlns="{NS}"><infNFSe><nNFSe>1234</nNFSe></infNFSe></NFSe>'.encode()


class ValidarNFSeTests(unittest.TestCase):
    def test_localiza_esquema_nfse(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "NFSe_v1.01.xsd"
            path.write_text(SCHEMA)
            self.assertEqual(localizar_xsd(dirname), path)

    def test_valida_xml_e_resume_sem_dados_pessoais(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "NFSe_v1.01.xsd"
            path.write_text(SCHEMA)
            root = validar_documento(XML, path)
            self.assertEqual(resumo_nao_sensivel(root)["numero_nfse"], "1234")

    def test_recusa_xml_invalido(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "NFSe_v1.01.xsd"
            path.write_text(SCHEMA)
            with self.assertRaises((etree.DocumentInvalid, ValueError)):
                validar_documento(f'<DPS xmlns="{NS}"/>'.encode(), path)


if __name__ == "__main__":
    unittest.main()
