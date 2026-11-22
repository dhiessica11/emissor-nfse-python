#!/usr/bin/env python3
"""Consulta somente leitura de uma DPS na SEFIN produção restrita.

Não transmite, altera, cancela ou substitui NFS-e.
"""
import argparse
import getpass
import re
import sys
from emissor.cliente_sefin import sessao_certificado, enviar_request


def validar_id(identifier):
    if not re.fullmatch(r"DPS[0-9]{42}", identifier):
        raise ValueError("Identificador DPS deve conter DPS seguido de 42 dígitos")
    return identifier


def main():
    parser = argparse.ArgumentParser(description="Consultar DPS em produção restrita: apenas GET")
    parser.add_argument("--certificado", required=True)
    parser.add_argument("--id-dps", required=True)
    args = parser.parse_args()
    try:
        identifier = validar_id(args.id_dps)
        password = getpass.getpass("Senha A1 (não gravada): ")
        with sessao_certificado(args.certificado, password) as session:
            response = enviar_request(session, "GET", "/dps/" + identifier)
        print("Ambiente: PRODUÇÃO RESTRITA | Método: GET")
        print("Status HTTP:", response.status_code)
        if response.status_code == 200:
            print("DPS localizada. Não reutilize o identificador; consulte o registro autorizado no ambiente.")
            return 0
        if response.status_code == 404:
            print("DPS não localizada nesta consulta. Isso não autoriza retransmissão automática.")
            return 0
        print("Consulta inconclusiva. Nenhuma transmissão realizada.")
        return 2
    except Exception as exc:
        print("Falha na consulta:", type(exc).__name__, str(exc)[:120], file=sys.stderr)
        print("Nenhuma transmissão realizada.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
