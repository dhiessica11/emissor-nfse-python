#!/usr/bin/env python3
"""Teste somente leitura de mTLS com o ambiente oficial de produção restrita.

Não gera, transmite, cancela ou substitui NFS-e.
"""
import argparse
import getpass
import os
from pathlib import Path
import tempfile

import requests
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, NoEncryption, pkcs12,
)

BASE = "https://sefin.producaorestrita.nfse.gov.br/SefinNacional"


def main():
    parser = argparse.ArgumentParser(description="Consulta somente leitura usando A1 local")
    parser.add_argument("--certificado", required=True, help="P12 privado no Mac")
    parser.add_argument("--municipio", required=True, help="Código IBGE com sete dígitos")
    args = parser.parse_args()
    if not args.municipio.isdigit() or len(args.municipio) != 7:
        parser.error("Informe código IBGE de 7 dígitos.")
    password = getpass.getpass("Senha do certificado A1: ")
    try:
        key, cert, chain = pkcs12.load_key_and_certificates(
            Path(args.certificado).read_bytes(), password.encode("utf-8")
        )
        if not key or not cert:
            raise ValueError("Certificado A1 sem chave privada ou certificado")
        with tempfile.TemporaryDirectory(prefix="nfse-mtls-") as temp:
            key_file = Path(temp) / "key.pem"
            certificate_file = Path(temp) / "cert.pem"
            for file, blob in (
                (key_file, key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())),
                (certificate_file, cert.public_bytes(Encoding.PEM) +
                 b"".join(c.public_bytes(Encoding.PEM) for c in (chain or []))),
            ):
                fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as dest:
                    dest.write(blob)
            endpoint = f"{BASE}/parametros_municipais/{args.municipio}/convenio"
            with requests.Session() as sess:
                response = sess.get(
                    endpoint, cert=(str(certificate_file), str(key_file)),
                    timeout=(10, 30), verify=True, allow_redirects=False,
                    headers={"Accept": "application/json"},
                )
            print("Endpoint: produção restrita (consulta somente leitura)")
            print("Status HTTP:", response.status_code)
            if response.status_code == 200:
                print("Consulta recebida pelo servidor.")
            else:
                print("Resposta não confirmada como sucesso. Verifique autorização, certificado e parâmetros.")
                print("Não serão exibidos dados fiscais nem credenciais.")
            return 0 if response.status_code == 200 else 1
    except (ValueError, OSError, requests.RequestException) as exc:
        print("Falha de conexão/credencial:", type(exc).__name__)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
