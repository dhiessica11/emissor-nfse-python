#!/usr/bin/env python3
"""Envia UM XML assinado apenas à SEFIN PRODUÇÃO RESTRITA após confirmação.

Este programa não acessa a produção fiscal real, não faz retry e exige
XSD oficial, assinatura verificável e registro local exclusivo.
"""
import argparse
import getpass
import json
import os
import re
from pathlib import Path
import sys
from datetime import datetime, timezone

from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
from lxml import etree
from signxml import XMLVerifier

from emissor.cliente_sefin import enviar_request, sessao_certificado
from emissor.homologacao import NAMESPACE, validar_xsd, empacotar


def validar_cnpj_confirmacao(informado, prestador):
    """Confirma o CNPJ do prestador, aceitando pontuação opcional."""
    cnpj = "".join(char for char in informado if char.isdigit())
    if len(cnpj) != 14 or cnpj != prestador:
        raise ValueError("CNPJ informado não corresponde ao prestador da DPS")
    return cnpj


def gravar_exclusivo(path, dados):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(dados, stream, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Teste de uma DPS na PRODUÇÃO RESTRITA")
    parser.add_argument("--xml", required=True, help="DPS assinada, arquivo privado")
    parser.add_argument("--xsd", required=True, help="XSD oficial da DPS na produção restrita")
    parser.add_argument("--certificado", required=True, help="A1 PKCS#12 privado")
    parser.add_argument("--registro", required=True, help="Novo arquivo JSON privado para controle")
    parser.add_argument("--confirmar-cnpj", required=True, help="CNPJ do prestador, apenas para confirmação local")
    args = parser.parse_args()
    try:
        xml = Path(args.xml).read_bytes()
        validar_xsd(xml, args.xsd)
        parser_xml = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(xml, parser=parser_xml)
        ns = {"n": NAMESPACE}
        if root.tag != f"{{{NAMESPACE}}}DPS" or root.get("versao") != "1.01":
            raise ValueError("DPS com namespace/versão incompatíveis")
        if root.findtext(".//n:tpAmb", namespaces=ns) != "2":
            raise ValueError("Bloqueado: tpAmb deve ser 2 (produção restrita)")
        prestador_xml = root.findtext(".//n:prest/n:CNPJ", namespaces=ns)
        validar_cnpj_confirmacao(args.confirmar_cnpj, prestador_xml)
        descricao = root.findtext(".//n:cServ/n:xDescServ", namespaces=ns) or ""
        if any(x in descricao.upper() for x in ("EXEMPLO", "FICTICIO", "FICTÍCI", "DEMONSTRATIV", "NAO TRANSMITIR", "NÃO TRANSMITIR")):
            raise ValueError("Arquivo demonstrativo bloqueado para transmissão")
        serie = root.findtext(".//n:serie", namespaces=ns)
        if not serie or not serie.isdigit() or not 1 <= int(serie) <= 49999:
            raise ValueError("Série fora da faixa permitida para emissão via API (1 a 49999)")
        inf = root.find(f"{{{NAMESPACE}}}infDPS")
        if inf is None or not inf.get("Id"):
            raise ValueError("Identificador da DPS ausente")
        dps_id = inf.get("Id")
        if not re.fullmatch(r"DPS[0-9]{42}", dps_id):
            raise ValueError("Formato do identificador de DPS inválido")
        password = getpass.getpass("Senha do A1 local (não gravada): ")
        _key, cert, _chain = pkcs12.load_key_and_certificates(
            Path(args.certificado).read_bytes(), password.encode("utf-8")
        )
        if cert is None:
            raise ValueError("Certificado inválido")
        XMLVerifier().verify(
            xml, x509_cert=cert.public_bytes(Encoding.PEM),
            id_attribute="Id",
        )
        print("Assinatura e XSD validados localmente.")
        print("Ambiente fixo: PRODUÇÃO RESTRITA, sem efeitos fiscais.")
        print("Identificador da DPS:", dps_id)
        print("Nenhuma nota do ambiente de produção será emitida.")
        if input("Digite HOMOLOGAR UMA DPS para transmitir: ").strip() != "HOMOLOGAR UMA DPS":
            print("Cancelado sem transmissão.")
            return 1
        registro = Path(args.registro).resolve()
        repo = Path(__file__).resolve().parent
        if registro == repo or repo in registro.parents:
            raise ValueError("Registro deve ficar fora do repositório Git público")
        if registro.exists():
            raise ValueError("Já existe registro da DPS: não retransmitir sem consultar")
        # Controle é gravado ANTES de abrir conexão para bloquear reenvio cego.
        gravar_exclusivo(registro, {
            "id_dps": dps_id, "ambiente": "PRODUCAO_RESTRITA",
            "estado": "PENDENTE_CONSULTA",
            "criado_em": datetime.now(timezone.utc).isoformat(),
            "observacao": "Consulta antes de qualquer repetição obrigatória.",
        })
        with sessao_certificado(args.certificado, password) as sess:
            consultar = enviar_request(sess, "GET", "/dps/" + dps_id)
            if consultar.status_code == 200:
                print("DPS já existe na SEFIN restrita. Envio bloqueado.")
                return 2
            if consultar.status_code != 404:
                print("Consulta prévia inconclusiva HTTP", consultar.status_code,
                      "- envio bloqueado. Consulte manualmente.")
                return 2
            response = enviar_request(
                sess, "POST", "/nfse", json=empacotar(xml),
                headers={"Content-Type": "application/json"}
            )
            print("HTTP de emissão em produção restrita:", response.status_code)
            # Corpo pode conter dados privados e só é salvo no disco local.
            resultado = registro.with_name(registro.stem + "-resposta.json")
            gravar_exclusivo(resultado, {
                "id_dps": dps_id,
                "http_status": response.status_code,
                "body": response.text[:250000],
                "ambiente": "PRODUCAO_RESTRITA",
                "estado": "CONSULTAR_ANTES_DE_REENVIAR",
            })
            print("Resposta armazenada em", resultado)
            print("Consulte a DPS antes de qualquer nova tentativa; sem retry automático.")
            return 0 if response.status_code == 201 else 2
    except Exception as exc:
        print("Homologação não concluída:", type(exc).__name__, str(exc)[:180],
              file=sys.stderr)
        print("Se houver registro PENDENTE_CONSULTA, confira antes de repetir.",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
