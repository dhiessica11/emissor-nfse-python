#!/usr/bin/env python3
"""Prévia privada de oito cobranças PJ de dezembro/2026, sem emissão nem assinatura.

Lê cadastro LOCAL real, valida oito CNPJs e produz um novo JSON privado.
Não copia dados reais para o repositório nem altera o cadastro de origem.
"""
import argparse
from datetime import date
from decimal import Decimal
import json
import os
from pathlib import Path
import sys

from emissor.core import carrega_clientes

COMPETENCIA = "2026-12"
VENCIMENTO = "2026-12-20"
VALOR = Decimal("500.00")
DESCRICAO = (
    "Serviços de integração de sistemas em tecnologia da informação. "
    "02 parcela décimo terceiro contratual, conforme acordo de prestação de serviços. "
    "Dados para pagamento: PIX: 48.854.187/0001-17 "
    "Vencimento: 20/12/2026"
)


def gerar_previas(clientes):
    if len(clientes) != 8:
        raise ValueError("São necessários exatamente 8 tomadores")
    result = []
    for cliente in clientes:
        result.append({
            "id": cliente["id"],
            "unidade": cliente["unidade"],
            "tomador_cnpj": cliente["cnpj"],
            "tomador_razao_social": cliente["razao_social"],
            "competencia": COMPETENCIA,
            "valor": str(VALOR),
            "vencimento": VENCIMENTO,
            "descricao_servico": DESCRICAO,
            "situacao": "PREVIA_NAO_TRANSMITIDA",
            "campos_fiscais_referencia": cliente["campos_fiscais"],
            "pendencias": [
                "Conferir enquadramento PJ e descrição com contrato/contabilidade",
                "Confirmar parâmetros fiscais aplicáveis em dezembro de 2026",
                "Definir dia da competência e data real da emissão",
                "Conferir se já existe documento da mesma competência"
            ],
        })
    return result


def gravar_novo_privado(path, conteudo):
    path = Path(path).resolve()
    raiz = Path(__file__).resolve().parent
    if path == raiz or raiz in path.parents:
        raise ValueError("Saída deve ficar fora do repositório GitHub")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(conteudo, file, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser(description="Prévia das 8 NFS-e PJ de dezembro/2026, sem transmissão")
    ap.add_argument("--cadastro", required=True, help="JSON privado de 8 tomadores reais")
    ap.add_argument("--saida", required=True, help="Novo JSON privado fora do Git")
    args = ap.parse_args()
    try:
        clientes = carrega_clientes(args.cadastro)
        if any("EXEMPLO" in (c["razao_social"] + c["unidade"]).upper() for c in clientes):
            raise ValueError("Cadastro demonstrativo não pode gerar prévias de cobrança real")
        previas = gerar_previas(clientes)
        gravar_novo_privado(args.saida, {
            "tipo": "PREVIA_OFFLINE_SEM_EMISSAO",
            "competencia": COMPETENCIA,
            "vencimento": VENCIMENTO,
            "valor_total": str(VALOR * len(previas)),
            "quantidade": len(previas),
            "documentos": previas,
        })
        print("PRÉVIAS CRIADAS: 8 | VALOR POR TOMADOR: R$ 500,00")
        print("TOTAL: R$ 4.000,00 | COMPETÊNCIA: dezembro/2026")
        print("VENCIMENTO: 20/12/2026 | ARQUIVO PRIVADO:", args.saida)
        print("Somente planejamento. Nenhuma DPS assinada ou transmitida.")
        return 0
    except Exception as exc:
        print("Prévia não gerada:", type(exc).__name__, str(exc)[:200], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
