import base64
import gzip
import unittest
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from lxml import etree
from signxml import XMLVerifier

from emissor.homologacao import (
    NAMESPACE, id_dps, construir_dps, assinar_dps, empacotar,
)


def dados_ficticios():
    return {
        "municipio_emissor": "5003702", "prestador_cnpj": "11222333000181",
        "tomador_cnpj": "11222333000181",
        "tomador_razao_social": "EMPRESA DEMONSTRATIVA FICTICIA",
        "municipio_tomador": "5003702", "cep_tomador": "79800000",
        "logradouro_tomador": "RUA DE TESTE", "numero_endereco_tomador": "10",
        "bairro_tomador": "CENTRO", "municipio_prestacao": "5003702",
        "codigo_servico": "010701", "codigo_nbs": "115011000",
        "descricao_servico": "PRESTACAO DE SERVICO - EXEMPLO",
        "valor": "100.00", "serie": "1", "numero_dps": 900001,
        "competencia": "2026-11-22", "data_emissao": "2026-11-22T12:00:00-04:00",
        "op_simp_nac": "3", "reg_ap_trib_sn": "2", "reg_esp_trib": "0",
        "trib_issqn": "1", "ret_issqn": "1",
        "cst_pis_cofins": "00", "ret_pis_cofins": "0",
        "percentual_total_tributos_sn": "2.00",
    }


class HomologacaoTests(unittest.TestCase):
    def test_id_dps_eh_estavel(self):
        d = dados_ficticios()
        identifier = id_dps(d["municipio_emissor"], d["prestador_cnpj"],
                            d["serie"], d["numero_dps"])
        self.assertEqual(len(identifier), 45)
        self.assertTrue(identifier.startswith("DPS50037022"))
        with self.assertRaises(ValueError):
            id_dps("invalid", d["prestador_cnpj"], "1", 1)
        with self.assertRaises(ValueError):
            id_dps(d["municipio_emissor"], d["prestador_cnpj"], "70000", 1)

    def test_gera_xml_e_pacote(self):
        document = construir_dps(dados_ficticios())
        root = etree.fromstring(document)
        self.assertEqual(root.get("versao"), "1.01")
        ns = {"nf": NAMESPACE}
        self.assertEqual(root.findtext(".//nf:vServ", namespaces=ns), "100.00")
        self.assertEqual(root.findtext(".//nf:tpAmb", namespaces=ns), "2")
        ver_aplic = root.findtext(".//nf:verAplic", namespaces=ns)
        self.assertLessEqual(len(ver_aplic), 20)
        self.assertEqual(ver_aplic, "EmissorNFSePy_0.1")
        packed = empacotar(document)
        self.assertEqual(gzip.decompress(base64.b64decode(packed["dpsXmlGZipB64"])), document)

    def test_valor_invalido(self):
        data = dados_ficticios()
        data["valor"] = "-1.00"
        with self.assertRaises(ValueError):
            construir_dps(data)

    def test_assinatura_xml_com_certificado_ficticio(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CERTIFICADO FICTICIO PARA TESTES")])
        now = datetime.now(timezone.utc)
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject).issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=1))
            .sign(key, hashes.SHA256())
        )
        p12 = pkcs12.serialize_key_and_certificates(
            b"teste", key, certificate, None,
            serialization.BestAvailableEncryption(b"senha-ficticia"),
        )
        original = construir_dps(dados_ficticios())
        signed = assinar_dps(original, p12, "senha-ficticia")
        XMLVerifier().verify(signed, x509_cert=certificate.public_bytes(serialization.Encoding.PEM), id_attribute="Id")
        self.assertIn(b"Signature", signed)


if __name__ == "__main__":
    unittest.main()
