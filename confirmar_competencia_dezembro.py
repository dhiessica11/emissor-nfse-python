#!/usr/bin/env python3
"""Confirma a competência 01/12/2026 em oito rascunhos privados.

Não gera XML, não define data de emissão, não assina nem transmite.
Preserva os originais e cria um novo diretório exclusivo.
"""
import argparse
import json
from pathlib import Path
import sys

from preparar_rascunhos_dps_dezembro import salvar_diretorio_novo

COMPETENCIA = "2026-12-01"
MES = "2026-12"
VENCIMENTO = "2026-12-20"


def confirmar_competencia(documentos):
    if len(documentos) != 8:
        raise ValueError("São necessários exatamente oito rascunhos")
    numeros = set()
    cnpjs = set()
    resultado = []
    for item in documentos:
        if item.get("tipo") != "RASCUNHO_DPS_NAO_EMITIVEL":
            raise ValueError("Documento de origem não é um rascunho esperado")
        if item.get("competencia_mes_confirmada") != MES or item.get("vencimento") != VENCIMENTO:
            raise ValueError("Competência mensal ou vencimento incompatível")
        dados = item.get("dados_preparatorios", {})
        if dados.get("competencia") is not None or dados.get("data_emissao") is not None:
            raise ValueError("Rascunho já contém datas; não sobrescrever")
        if dados.get("valor") != "500.00":
            raise ValueError("Valor divergente do lote aprovado para planejamento")
        numero = dados.get("numero_dps")
        cnpj = dados.get("tomador_cnpj")
        if numero in numeros or cnpj in cnpjs:
            raise ValueError("Número ou tomador repetido")
        numeros.add(numero)
        cnpjs.add(cnpj)
        copia = json.loads(json.dumps(item))
        copia["dados_preparatorios"]["competencia"] = COMPETENCIA
        copia["situacao"] = "COMPETENCIA_CONFIRMADA_EMISSAO_E_FISCAL_PENDENTES"
        copia["pendencias_bloqueantes"] = [
            x for x in copia.get("pendencias_bloqueantes", [])
            if "Confirmar dia da competência" not in x
        ]
        copia["competencia_dia_confirmada"] = COMPETENCIA
        resultado.append(copia)
    if sorted(numeros) != list(range(900003, 900011)):
        raise ValueError("Numeração proposta inesperada; verificar manualmente")
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Atualiza competência dos oito rascunhos sem emitir")
    parser.add_argument("--origem-dir", required=True)
    parser.add_argument("--saida-dir", required=True)
    args = parser.parse_args()
    try:
        origem = Path(args.origem_dir).expanduser().resolve()
        manifest = json.loads((origem / "manifesto.json").read_text(encoding="utf-8"))
        if (manifest.get("tipo") != "LOTE_RASCUNHOS_SEM_XML_OU_TRANSMISSAO"
                or manifest.get("quantidade") != 8
                or manifest.get("valor_total") != "4000.00"
                or manifest.get("competencia_mes") != MES):
            raise ValueError("Manifesto de origem não corresponde ao lote")
        itens = manifest.get("documentos", [])
        if len(itens) != 8 or len({x.get("arquivo") for x in itens}) != 8:
            raise ValueError("Manifesto contém arquivos ausentes ou repetidos")
        documentos = []
        for item in itens:
            nome = item.get("arquivo", "")
            if not isinstance(nome, str) or not nome.startswith("rascunho-") or not nome.endswith(".json") or Path(nome).name != nome:
                raise ValueError("Nome de arquivo de rascunho inesperado")
            doc = json.loads((origem / nome).read_text(encoding="utf-8"))
            if item.get("unidade") != doc.get("unidade") or item.get("id_dps_proposto_nao_reservado") != doc.get("id_dps_proposto_nao_reservado"):
                raise ValueError("Manifesto e rascunho divergentes")
            documentos.append(doc)
        novos = confirmar_competencia(documentos)
        destino = salvar_diretorio_novo(args.saida_dir, novos)
        print("COMPETÊNCIA CONFIRMADA: 01/12/2026 | 8 RASCUNHOS | R$ 4.000,00")
        print("Saída privada:", destino)
        print("Data de emissão: PENDENTE; análise fiscal: PENDENTE")
        print("Nenhum XML, assinatura ou transmissão realizados")
        return 0
    except Exception as exc:
        print("Não foi possível confirmar competência:", type(exc).__name__, str(exc)[:200], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
