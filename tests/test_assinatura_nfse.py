import unittest
from base64 import b64encode
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from lxml import etree
from signxml import XMLSigner, methods

from verificar_assinatura_nfse import verificar_integridade

NS = "http://www.sped.fazenda.gov.br/nfse"


class VerificarAssinaturaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = datetime.now(timezone.utc)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CERTIFICADO TESTE FICTICIO")])
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(days=1))
                .not_valid_after(now + timedelta(days=1))
                .sign(key, __import__("cryptography").hazmat.primitives.hashes.SHA256()))
        cls.key = key
        cls.cert = cert
        root = etree.Element(f"{{{NS}}}NFSe", nsmap={None: NS})
        inf = etree.SubElement(root, f"{{{NS}}}infNFSe")
        inf.set("Id", "NFSeTESTE123")
        etree.SubElement(inf, f"{{{NS}}}nNFSe").text = "1"
        cls.signed = etree.tostring(XMLSigner(method=methods.enveloped).sign(
            root,
            key=key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
            cert=cert.public_bytes(Encoding.PEM),
            reference_uri="#NFSeTESTE123", id_attribute="Id"))

    def test_assinatura_integra(self):
        self.assertTrue(verificar_integridade(self.signed))

    def test_assinatura_interna_da_dps_nao_confunde_assinatura_nfse(self):
        root = etree.Element(f"{{{NS}}}NFSe", nsmap={None: NS})
        inf = etree.SubElement(root, f"{{{NS}}}infNFSe", Id="NFSeCOMDPS")
        dps = etree.SubElement(inf, f"{{{NS}}}DPS")
        etree.SubElement(dps, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed = etree.tostring(XMLSigner(method=methods.enveloped).sign(
            root,
            key=self.key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
            cert=self.cert.public_bytes(Encoding.PEM),
            reference_uri="#NFSeCOMDPS", id_attribute="Id"))
        self.assertTrue(verificar_integridade(signed))

    def test_conteudo_alterado(self):
        altered = self.signed.replace(b"<nNFSe>1</nNFSe>", b"<nNFSe>2</nNFSe>")
        with self.assertRaises(Exception):
            verificar_integridade(altered)

    def test_xml_sem_assinatura(self):
        with self.assertRaises(ValueError):
            verificar_integridade(f'<NFSe xmlns="{NS}"><infNFSe/></NFSe>'.encode())


if __name__ == "__main__":
    unittest.main()
