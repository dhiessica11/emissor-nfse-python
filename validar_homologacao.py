#!/usr/bin/env python3
"""Validação LOCAL de DPS com XSD e A1. Não possui código de transmissão HTTP."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import sys

from emissor.homologacao import construir_dps, validar_xsd, assinar_dps, empacotar


def main():
    parser = argparse.ArgumentParser(
        description="Valida e assina uma DPS localmente, sem transmitir NFS-e."
    )
    parser.add_argument("--dados", required=True, help="JSON privado; nunca publique.")
    parser.add_argument("--xsd", required=True, help="XSD oficial da DPS (produção restrita).")
    parser.add_argument("--certificado", required=True, help="Arquivo A1 .p12 privado.")
    parser.add_argument("--saida", required=True, help="Diretório privado dos artefatos.")
    args = parser.parse_args()
    try:
        doc = json.loads(Path(args.dados).read_text(encoding="utf-8"))
        xml = construir_dps(doc)
        # O XSD pode exigir Signature; validamos o documento completo assinado.
        senha = getpass.getpass("Senha do certificado A1 (não será gravada): ")
        assinado = assinar_dps(xml, Path(args.certificado).read_bytes(), senha)
        validar_xsd(assinado, args.xsd)
        from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
        from signxml import XMLVerifier
        _, cert, _ = pkcs12.load_key_and_certificates(
            Path(args.certificado).read_bytes(), senha.encode('utf-8')
        )
        XMLVerifier().verify(assinado, x509_cert=cert.public_bytes(Encoding.PEM), id_attribute='Id')
        payload = empacotar(assinado)
        target = Path(args.saida)
        target.mkdir(mode=0o700, parents=True, exist_ok=True)
        if target.is_symlink():
            raise ValueError("Diretório de saída não pode ser link simbólico.")
        target.chmod(0o700)
        for filename, data in (
            ("dps-assinada.xml", assinado),
            ("requisicao-homologacao.json", json.dumps(payload, indent=2).encode("utf-8")),
        ):
            path = target / filename
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            fd = os.open(path, flags, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
        print("XML validado no XSD indicado e assinado localmente.")
        print("SHA-256 do XML assinado:", hashlib.sha256(assinado).hexdigest())
        print("Arquivos criados em", target)
        print("NENHUM documento foi transmitido. Confira a versão do XSD e o leiaute vigente.")
        return 0
    except Exception as exc:
        print(f"Falha local: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
