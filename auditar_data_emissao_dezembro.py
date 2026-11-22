#!/usr/bin/env python3
"""Validação offline de prontidão de emissão futura, SEM emitir ou assinar.

A SEFIN rejeita DPS cuja competência seja posterior à data de emissão.
O programa nunca simula que uma emissão futura já aconteceu.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import sys

DIA_COMPETENCIA = date(2026, 12, 1)


def avaliar_data(data_planejada, competencia=DIA_COMPETENCIA):
    if data_planejada < competencia:
        return (
            False,
            f"BLOQUEADO: competência {competencia:%d/%m/%Y} é posterior à emissão "
            f"planejada {data_planejada:%d/%m/%Y}; regra E0015."
        )
    return True, "Datas cronologicamente compatíveis; ainda exige validação fiscal e autorização."


def main():
    parser = argparse.ArgumentParser(description="Auditoria de datas da emissão futura, SOMENTE LEITURA")
    parser.add_argument("--data-planejada", required=True, help="AAAA-MM-DD")
    parser.add_argument("--lote-dir", required=True)
    args = parser.parse_args()
    try:
        planejada = date.fromisoformat(args.data_planejada)
        pasta = Path(args.lote_dir).expanduser().resolve()
        manifesto = json.loads((pasta / "manifesto.json").read_text(encoding="utf-8"))
        if (manifesto.get("quantidade") != 8
                or manifesto.get("valor_total") != "4000.00"
                or len(manifesto.get("documentos", [])) != 8):
            raise ValueError("Manifesto não corresponde ao lote de oito documentos")
        for item in manifesto["documentos"]:
            nome = item["arquivo"]
            if Path(nome).name != nome:
                raise ValueError("Nome de rascunho inválido")
            rascunho = json.loads((pasta / nome).read_text(encoding="utf-8"))
            if (rascunho["dados_preparatorios"].get("competencia") != "2026-12-01"
                    or rascunho["dados_preparatorios"].get("data_emissao") is not None):
                raise ValueError("Rascunho com competência ou emissão inesperada")
        permitido, mensagem = avaliar_data(planejada)
        print(mensagem)
        print("Rascunhos conferidos: 8 | Nenhum XML gerado ou transmitido")
        return 0 if permitido else 3
    except Exception as exc:
        print("Auditoria incompleta:", type(exc).__name__, str(exc)[:180], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
