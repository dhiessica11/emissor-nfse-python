#!/usr/bin/env python3
"""Extrai localmente o XML de uma NFS-e retornada pela SEFIN restrita.

Somente leitura do JSON, sem HTTP, sem alterar documentos fiscais.
O XML e o resumo privado são criados fora do repositório.
"""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

from lxml import etree

NAMESPACE = "http://www.sped.fazenda.gov.br/nfse"
MAX_GZIP = 2_000_000
MAX_XML = 10_000_000


def extrair_resposta(registro):
    if registro.get("http_status") != 201 or registro.get("ambiente") != "PRODUCAO_RESTRITA":
        raise ValueError("Registro não confirma emissão HTTP 201 em produção restrita")
    body = registro.get("body")
    if not isinstance(body, str):
        raise ValueError("Corpo HTTP não encontrado")
    resposta = json.loads(body)
    if str(resposta.get("tipoAmbiente")) != "2":
        raise ValueError("Resposta não pertence à produção restrita")
    if resposta.get("erros"):
        raise ValueError("Resposta da SEFIN contém erros")
    token = resposta.get("nfseXmlGZipB64")
    chave = resposta.get("chaveAcesso")
    if not isinstance(token, str) or not token or not isinstance(chave, str) or not chave:
        raise ValueError("Resposta incompleta: chave ou XML ausente")
    blob = base64.b64decode(token, validate=True)
    if len(blob) > MAX_GZIP:
        raise ValueError("Pacote comprimido acima do limite de segurança")
    with gzip.GzipFile(fileobj=__import__("io").BytesIO(blob)) as gz:
        xml = gz.read(MAX_XML + 1)
    if len(xml) > MAX_XML:
        raise ValueError("XML acima do limite de segurança")
    root = etree.fromstring(xml, parser=etree.XMLParser(
        resolve_entities=False, no_network=True, load_dtd=False,
        huge_tree=False, remove_blank_text=False
    ))
    if root.tag != f"{{{NAMESPACE}}}NFSe":
        raise ValueError("XML não possui raiz NFSe no namespace oficial")
    # Verificação estrutural simples, não substitui validação pelo XSD da NFSe.
    if root.find(f"{{{NAMESPACE}}}infNFSe") is None:
        raise ValueError("infNFSe ausente no XML")
    return resposta, xml


def gravar_privado(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)


def main():
    parser = argparse.ArgumentParser(description="Extrai XML retornado pela SEFIN, sem envio")
    parser.add_argument("--resposta", required=True, help="JSON privado de resposta HTTP 201")
    parser.add_argument("--saida", required=True, help="Novo arquivo XML privado, fora do Git")
    args = parser.parse_args()
    try:
        source = Path(args.resposta).resolve()
        target = Path(args.saida).resolve()
        repo = Path(__file__).resolve().parent
        if target == repo or repo in target.parents:
            raise ValueError("Não salvar XML fiscal dentro do repositório público")
        registro = json.loads(source.read_text(encoding="utf-8"))
        response, xml = extrair_resposta(registro)
        gravar_privado(target, xml)
        print("Ambiente: PRODUÇÃO RESTRITA")
        print("NFS-e XML extraído e armazenado em:", target)
        print("Tamanho XML:", len(xml), "bytes")
        print("SHA256:", hashlib.sha256(xml).hexdigest())
        print("Chave de acesso recebida: SIM (não exibida)")
        print("Atenção: validação XSD da NFS-e e conferência fiscal ainda pendentes.")
        print("Nenhuma operação de rede executada.")
        return 0
    except Exception as exc:
        print("Falha ao extrair NFS-e:", type(exc).__name__, str(exc)[:160], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
