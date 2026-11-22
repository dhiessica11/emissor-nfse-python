#!/usr/bin/env python3
"""Executa prévia ou simulação offline; nunca envia NFS-e."""
import argparse
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from emissor.core import (
    ValidationError, carrega_clientes, competencia_valida,
    conectar, gravar_simulacoes, status,
)

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Prévia e simulação offline de NFS-e")
    parser.add_argument("--competencia", required=True)
    parser.add_argument("--vencimento", help="AAAA-MM-DD; não é presumido")
    parser.add_argument("--cadastro", default=str(ROOT / "config/clientes.json"))
    parser.add_argument("--db", default=str(ROOT / "saida/historico.sqlite3"))
    parser.add_argument("--simular", action="store_true")
    args = parser.parse_args()
    try:
        competence = competencia_valida(args.competencia)
        clients = carrega_clientes(args.cadastro)
        due = date.fromisoformat(args.vencimento) if args.vencimento else None
        db = conectar(args.db)
        print("\nEMISSOR NFS-e — PRÉVIA OFFLINE (NÃO EMITE NOTAS)")
        print("Competência:", competence)
        print("Vencimento:", due.isoformat() if due else "NÃO INFORMADO")
        for pos, client in enumerate(clients, 1):
            previous = status(db, client["id"], competence) or "NOVA"
            print(f'{pos}. {client["unidade"]}: {client["cnpj"]} - R$ {client["valor"]} [{previous}]')
        total = sum((Decimal(client["valor"]) for client in clients), Decimal("0"))
        print(f"Total: R$ {total:.2f}")
        print("Tributação ainda NÃO validada para emissão fiscal.")
        print("Confira externamente se já existem NFS-e autorizadas para a competência.")
        if not args.simular:
            print("Para registrar simulação, use --simular.")
            return 0
        if due is None:
            raise ValidationError("Para simular, informe --vencimento AAAA-MM-DD.")
        print("Isto registra SOMENTE uma simulação local.")
        if input("Digite SIMULAR 8 NOTAS: ").strip() != "SIMULAR 8 NOTAS":
            print("Cancelado.")
            return 1
        gravar_simulacoes(db, clients, competence)
        print("8 simulações registradas; nenhuma NFS-e transmitida.")
        return 0
    except (ValidationError, FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
