#!/usr/bin/env python3
"""Baixa e extrai com segurança os XSD oficiais de produção restrita.

Uso somente local. Nunca envia XML fiscal nem abre arquivos de certificado.
"""
import argparse
import hashlib
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zipfile import ZipFile, BadZipFile
import io

SOURCE = ("https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/"
          "producao-restrita/esquemas_prod_restrita_20261020.zip")
MAX_DOWNLOAD = 30 * 1024 * 1024
MAX_FILE = 15 * 1024 * 1024
MAX_TOTAL = 100 * 1024 * 1024


def baixar(url=SOURCE):
    if url != SOURCE:
        raise ValueError("Fonte diferente da URL oficial fixada")
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 EmissorNFSe/0.1"})
    with urlopen(req, timeout=40) as response:
        if response.geturl() != SOURCE:
            raise ValueError("Redirecionamento para endereço não autorizado")
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError("Pacote ultrapassa limite de download")
    return data


def extrair_seguro(data, folder):
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    total = 0
    extracted = []
    with ZipFile(io.BytesIO(data)) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            path = Path(item.filename)
            if (path.is_absolute() or ".." in path.parts or
                not path.suffix.lower() == ".xsd"):
                continue
            if item.file_size > MAX_FILE:
                raise ValueError("Arquivo XSD excessivamente grande")
            total += item.file_size
            if total > MAX_TOTAL:
                raise ValueError("Pacote excede tamanho permitido")
            # Recusa sobrescrita e evita entradas de diretório contidas no ZIP.
            relative = Path(*path.parts)
            target = folder / relative
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with archive.open(item) as src:
                flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
                fd = os.open(target, flags, 0o600)
                with os.fdopen(fd, "wb") as dest:
                    actual = 0
                    while True:
                        chunk = src.read(65536)
                        if not chunk:
                            break
                        actual += len(chunk)
                        if actual > MAX_FILE:
                            raise ValueError("XSD excede limite de leitura")
                        dest.write(chunk)
            extracted.append(target)
    if not extracted:
        raise ValueError("Pacote não contém arquivos XSD")
    return extracted


def main():
    parser = argparse.ArgumentParser(description="Baixar XSD oficial da produção restrita")
    parser.add_argument("--destino", required=True, help="Pasta privada, fora do GitHub")
    args = parser.parse_args()
    try:
        print("Origem oficial:", SOURCE)
        payload = baixar()
        digest = hashlib.sha256(payload).hexdigest()
        found = extrair_seguro(payload, args.destino)
        print("SHA256 do ZIP:", digest)
        print("Arquivos XSD extraídos:", len(found))
        print("Candidatos ao esquema principal da DPS:")
        for path in found:
            if "dps" in path.name.lower():
                print(" ", path)
        print("Inspecione o pacote e escolha o XSD da DPS com dependências presentes.")
        print("Nenhum certificado, XML privado ou nota foi enviado.")
        return 0
    except (OSError, HTTPError, URLError, BadZipFile, ValueError) as exc:
        print("Falha no pacote de XSD:", type(exc).__name__, str(exc)[:200], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
