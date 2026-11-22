#!/usr/bin/env python3
"""Verificação criptográfica LOCAL de XML assinado de NFS-e.

Usa o certificado incorporado APENAS para conferir integridade da assinatura.
Não confia automaticamente no emissor; cadeia ICP-Brasil, revogação e titularidade
não são verificadas neste script. Nenhuma conexão de rede é realizada.
"""
import argparse
from base64 import b64decode
from pathlib import Path
import sys

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding
from lxml import etree
from signxml import XMLVerifier, SignatureConfiguration

XMLDSIG = "http://www.w3.org/2000/09/xmldsig#"
NFSE_NS = "http://www.sped.fazenda.gov.br/nfse"


def verificar_integridade(xml_bytes):
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
    root = etree.fromstring(xml_bytes, parser=parser)
    if root.tag != f"{{{NFSE_NS}}}NFSe":
        raise ValueError("Documento não é NFS-e nacional")
    signatures = root.xpath("./ds:Signature", namespaces={"ds": XMLDSIG})
    if len(signatures) != 1:
        raise ValueError("É exigida exatamente uma assinatura XMLDSig direta da NFS-e")
    signature = signatures[0]
    certs = signature.xpath("./ds:KeyInfo/ds:X509Data/ds:X509Certificate/text()",
                           namespaces={"ds": XMLDSIG})
    if len(certs) != 1:
        raise ValueError("Assinatura deve conter exatamente um certificado X.509")
    cert = x509.load_der_x509_certificate(b64decode("".join(certs[0].split()), validate=True))
    # Certificate supplied explicitly: verifies signature mathematics but deliberately
    # does NOT establish trust in the signer or validate the ICP-Brasil chain.
    XMLVerifier().verify(
        root, x509_cert=cert.public_bytes(Encoding.PEM),
        expect_config=SignatureConfiguration(require_x509=True, location="./"),
        id_attribute="Id",
    )
    return True


def main():
    ap = argparse.ArgumentParser(description="Verifica integridade de assinatura XMLDSig local")
    ap.add_argument("--xml", required=True)
    args = ap.parse_args()
    try:
        xml = Path(args.xml).read_bytes()
        verificar_integridade(xml)
        print("INTEGRIDADE CRIPTOGRÁFICA DA ASSINATURA: VÁLIDA")
        print("Origem do certificado: incorporado ao próprio XML")
        print("CONFIANÇA NA AUTORIDADE EMISSORA: NÃO VERIFICADA")
        print("Cadeia ICP-Brasil / revogação / identidade do emissor: PENDENTES")
        print("Nenhuma operação de rede realizada.")
        return 0
    except Exception as exc:
        print("Validação da assinatura não concluída:", type(exc).__name__, str(exc)[:300],
              file=sys.stderr)
        print("Nenhuma operação de rede realizada.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
