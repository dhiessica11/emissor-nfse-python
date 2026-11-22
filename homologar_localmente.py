#!/usr/bin/env python3
"""Valida uma DPS de teste com A1 e esquemas oficiais, SEM transmitir NFS-e.

Os dados privados e o certificado nunca são enviados para serviços externos;
apenas o pacote XSD público é baixado do Portal gov.br.
"""
import argparse
from base64 import b64encode
import getpass
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
from lxml import etree
from signxml import XMLVerifier

from baixar_esquemas_restritos import baixar, extrair_seguro
from preparar_dps_referencia import extrair_dados
from emissor.homologacao import construir_dps, assinar_dps, validar_xsd, empacotar


def salvar_novo(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as dest:
        dest.write(data)


def main():
    parser = argparse.ArgumentParser(description="Homologação estrutural LOCAL, sem POST")
    parser.add_argument("--xml-referencia", required=True, help="NFS-e XML antiga, privada")
    parser.add_argument("--certificado", required=True, help="Arquivo A1 (.p12) privado")
    parser.add_argument("--competencia", required=True, help="Nova competência AAAA-MM-DD")
    parser.add_argument("--vencimento", required=True, help="Novo vencimento DD/MM/AAAA")
    parser.add_argument("--serie", type=int, required=True, help="Série API entre 1 e 49999")
    parser.add_argument("--numero-dps", type=int, required=True, help="Número novo, não utilizado")
    parser.add_argument("--pasta-privada", required=True, help="Pasta fora do GitHub")
    args = parser.parse_args()
    try:
        target = Path(args.pasta_privada).resolve()
        repo = Path(__file__).resolve().parent
        if target == repo or repo in target.parents:
            raise ValueError("Pasta privada deve ficar fora do repositório GitHub")
        if target.exists() and any(target.iterdir()):
            raise ValueError("Pasta de execução deve estar vazia para não sobrescrever resultados")
        target.mkdir(parents=True, exist_ok=True, mode=0o700)
        target.chmod(0o700)
        data = extrair_dados(
            Path(args.xml_referencia).read_bytes(), args.serie, args.numero_dps,
            args.competencia, args.vencimento
        )
        xml = construir_dps(data)
        password = getpass.getpass("Senha A1 (oculta, não armazenada): ")
        p12_bytes = Path(args.certificado).read_bytes()
        _key, certificate, _chain = pkcs12.load_key_and_certificates(
            p12_bytes, password.encode("utf-8")
        )
        if certificate is None:
            raise ValueError("PKCS#12 sem certificado válido para leitura")
        now = datetime.now(timezone.utc)
        if not certificate.not_valid_before_utc <= now <= certificate.not_valid_after_utc:
            raise ValueError("Certificado fora do período de validade")
        signed = assinar_dps(xml, p12_bytes, password)
        XMLVerifier().verify(
            signed, x509_cert=certificate.public_bytes(Encoding.PEM),
            id_attribute="Id",
        )
        print("Assinatura criptográfica: válida com A1 local")
        schema_dir = target / "xsd-oficial"
        print("Baixando o pacote oficial de XSD 20/10/2026...")
        packed_xsd = baixar()
        found = extrair_seguro(packed_xsd, schema_dir)
        print("SHA256 ZIP oficial:", hashlib.sha256(packed_xsd).hexdigest())
        candidates = [x for x in found if x.name.lower().startswith("dps") and x.suffix.lower() == ".xsd"]
        if not candidates:
            candidates = [x for x in found if "dps" in x.name.lower()]
        if not candidates:
            raise ValueError("Nenhum esquema da DPS identificado no ZIP; confira os arquivos")
        issues = []
        valid_schema = None
        for candidate in sorted(candidates):
            try:
                validar_xsd(signed, candidate)
                valid_schema = candidate
                break
            except (etree.XMLSchemaError, etree.DocumentInvalid, etree.XMLSyntaxError, OSError) as exc:
                issues.append((candidate.name, str(exc)[:300]))
        if valid_schema is None:
            print("ASSINATURA OK, MAS XML REPROVADO NOS XSD DA DPS.")
            for filename, issue in issues[:3]:
                print("XSD:", filename, "Erro:", issue)
            print("Nenhum documento foi transmitido. Corrija o XML antes do envio.")
            return 3
        print("XSD oficial validado:", valid_schema)
        salvar_novo(target / "dps.json", json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        salvar_novo(target / "dps-assinada.xml", signed)
        salvar_novo(target / "requisicao-restrita.json",
                     json.dumps(empacotar(signed), indent=2).encode("utf-8"))
        print("RESULTADO: HOMOLOGAÇÃO ESTRUTURAL LOCAL APROVADA")
        print("ID da DPS:", etree.fromstring(signed).find("{http://www.sped.fazenda.gov.br/nfse}infDPS").get("Id"))
        print("Documentos privados armazenados em:", target)
        print("NENHUMA NFS-e transmitida. A API SEFIN ainda deverá validar regras de negócio.")
        return 0
    except Exception as exc:
        print("VALIDAÇÃO INCOMPLETA:", type(exc).__name__, str(exc)[:350], file=sys.stderr)
        print("Nenhuma DPS enviada à SEFIN.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
