#!/usr/bin/env python3
"""Conferência local da NFS-e retornada pela SEFIN em produção restrita.

Somente leitura. Não usa certificado, não faz GET/POST e não altera o XML.
"""
import argparse
import hashlib
from pathlib import Path
import sys
from lxml import etree

NAMESPACE = "http://www.sped.fazenda.gov.br/nfse"
NS = {"n": NAMESPACE}


def localizar_xsd(pasta):
    pasta = Path(pasta)
    candidatos = sorted(
        path for path in pasta.rglob("*.xsd")
        if path.name.lower().startswith("nfse_v")
    )
    if len(candidatos) != 1:
        raise ValueError(
            f"Esperado exatamente um XSD principal NFSe_v*.xsd; encontrados: {len(candidatos)}. "
            "Informe --xsd com o arquivo correto."
        )
    return candidatos[0]


def validar_documento(xml, caminho_xsd):
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
    root = etree.fromstring(xml, parser=parser)
    if root.tag != f"{{{NAMESPACE}}}NFSe":
        raise ValueError("Raiz NFSe/namespace inesperados")
    schema = etree.XMLSchema(etree.parse(str(caminho_xsd), parser=parser))
    schema.assertValid(root)
    return root


def resumo_nao_sensivel(root):
    def valor(xpath):
        result = root.xpath(xpath, namespaces=NS)
        if not result:
            return "não informado"
        item = result[0]
        return str(item if isinstance(item, str) else (item.text or "não informado"))

    return {
        "numero_nfse": valor("./n:infNFSe/n:nNFSe/text()"),
        "competencia": valor(".//n:DPS/n:infDPS/n:dCompet/text()"),
        "valor_servico": valor(".//n:DPS/n:infDPS/n:valores/n:vServPrest/n:vServ/text()"),
        "valor_liquido": valor("./n:infNFSe/n:valores/n:vLiq/text()"),
        "municipio_gerador": valor("./n:infNFSe/n:cLocIncid/text()"),
    }


def main():
    ap = argparse.ArgumentParser(description="Confere XML da NFS-e contra XSD oficial, sem envio")
    ap.add_argument("--xml", required=True)
    ap.add_argument("--pasta-xsd", required=True)
    ap.add_argument("--xsd", help="XSD principal da NFS-e, se a identificação automática não funcionar")
    args = ap.parse_args()
    try:
        xml_path = Path(args.xml).resolve()
        xsd = Path(args.xsd).resolve() if args.xsd else localizar_xsd(args.pasta_xsd)
        xml = xml_path.read_bytes()
        root = validar_documento(xml, xsd)
        print("Resultado: XML DA NFS-e APROVADO NO XSD OFICIAL")
        print("XSD:", xsd.name)
        print("Arquivo local:", xml_path)
        print("SHA256:", hashlib.sha256(xml).hexdigest())
        for name, value in resumo_nao_sensivel(root).items():
            print(name + ":", value)
        print("Conferência fiscal e assinatura digital do XML da NFS-e ainda exigem verificação específica.")
        print("Nenhuma operação de rede realizada.")
        return 0
    except Exception as exc:
        print("Validação da NFS-e não concluída:", type(exc).__name__, str(exc)[:400], file=sys.stderr)
        print("Nenhum documento transmitido.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
