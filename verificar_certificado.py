#!/usr/bin/env python3
"""Inspeção local de certificado A1; não faz transmissão nem exporta chave."""
import argparse
import getpass
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arquivo")
    args = parser.parse_args()
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
    except ImportError:
        print("Instale as dependências: pip install -r requirements.txt")
        return 2
    password = getpass.getpass("Senha do A1 (oculta): ")
    try:
        private_key, cert, _chain = pkcs12.load_key_and_certificates(
            Path(args.arquivo).read_bytes(), password.encode()
        )
        if not private_key or not cert:
            raise ValueError("Certificado ou chave privada ausente.")
        print("Titular:", cert.subject.rfc4514_string())
        print("Emissor:", cert.issuer.rfc4514_string())
        print("Início:", cert.not_valid_before_utc.isoformat())
        print("Fim:", cert.not_valid_after_utc.isoformat())
        print("Válido agora:", cert.not_valid_before_utc <= datetime.now(timezone.utc) <= cert.not_valid_after_utc)
        print("Chave privada presente: sim, não exportada")
        return 0
    except Exception as exc:
        print("Falha ao abrir certificado:", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
