#!/usr/bin/env python3
"""Converte uma NFS-e autorizada em dados locais de uma NOVA DPS de teste.

Nunca transmite documentos. Todos os arquivos de saída devem ficar fora do GitHub.
É obrigatório informar nova série API, número, competência e vencimento.
A tributação vem da referência: deve ser revisada antes da assinatura.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys

from lxml import etree
from emissor.homologacao import NAMESPACE, id_dps

NS = {"n": NAMESPACE}


def extrair_dados(xml, serie, numero, competencia, vencimento):
    if not 1 <= int(serie) <= 49999:
        raise ValueError("Série da API deve estar entre 1 e 49999")
    if not 1 <= int(numero) <= 999999999999999:
        raise ValueError("Número inválido")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", competencia):
        raise ValueError("Competência deve ser AAAA-MM-DD")
    datetime.fromisoformat(competencia)
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", vencimento):
        raise ValueError("Vencimento deve ser DD/MM/AAAA")
    datetime.strptime(vencimento, "%d/%m/%Y")
    root = etree.fromstring(xml, parser=etree.XMLParser(resolve_entities=False, no_network=True))
    inf = root.find(".//n:infDPS", namespaces=NS)
    if inf is None:
        raise ValueError("XML não contém infDPS")
    def get(path):
        value = inf.findtext(path, namespaces=NS)
        if not value:
            raise ValueError(f"Campo necessário ausente: {path}")
        return value.strip()
    desc = get("n:serv/n:cServ/n:xDescServ")
    old_due = re.search(r"Vencimento:\s*\d{2}/\d{2}/\d{4}", desc, flags=re.I)
    if not old_due:
        raise ValueError("Descrição da nota anterior não contém vencimento identificável")
    desc = desc[:old_due.start()] + f"Vencimento: {vencimento}" + desc[old_due.end():]
    data = {
        "municipio_emissor": get("n:cLocEmi"),
        "prestador_cnpj": get("n:prest/n:CNPJ"),
        "tomador_cnpj": get("n:toma/n:CNPJ"),
        "tomador_razao_social": get("n:toma/n:xNome"),
        "municipio_tomador": get("n:toma/n:end/n:endNac/n:cMun"),
        "cep_tomador": get("n:toma/n:end/n:endNac/n:CEP"),
        "logradouro_tomador": get("n:toma/n:end/n:xLgr"),
        "numero_endereco_tomador": get("n:toma/n:end/n:nro"),
        "bairro_tomador": get("n:toma/n:end/n:xBairro"),
        "municipio_prestacao": get("n:serv/n:locPrest/n:cLocPrestacao"),
        "codigo_servico": get("n:serv/n:cServ/n:cTribNac"),
        "codigo_nbs": get("n:serv/n:cServ/n:cNBS"),
        "descricao_servico": desc,
        "valor": get("n:valores/n:vServPrest/n:vServ"),
        "serie": str(int(serie)),
        "numero_dps": int(numero),
        "competencia": competencia,
        "data_emissao": datetime.now().astimezone().isoformat(timespec="seconds"),
        "op_simp_nac": get("n:prest/n:regTrib/n:opSimpNac"),
        "reg_ap_trib_sn": get("n:prest/n:regTrib/n:regApTribSN"),
        "reg_esp_trib": get("n:prest/n:regTrib/n:regEspTrib"),
        "trib_issqn": get("n:valores/n:trib/n:tribMun/n:tribISSQN"),
        "ret_issqn": get("n:valores/n:trib/n:tribMun/n:tpRetISSQN"),
        "cst_pis_cofins": get("n:valores/n:trib/n:tribFed/n:piscofins/n:CST"),
        "ret_pis_cofins": get("n:valores/n:trib/n:tribFed/n:piscofins/n:tpRetPisCofins"),
        "percentual_total_tributos_sn": get("n:valores/n:trib/n:totTrib/n:pTotTribSN"),
    }
    id_dps(data["municipio_emissor"], data["prestador_cnpj"], data["serie"], data["numero_dps"])
    return data


def main():
    parser = argparse.ArgumentParser(description="Prepara JSON privado de nova DPS, sem emissão")
    parser.add_argument("--xml-referencia", required=True)
    parser.add_argument("--serie", type=int, required=True)
    parser.add_argument("--numero-dps", type=int, required=True)
    parser.add_argument("--competencia", required=True)
    parser.add_argument("--vencimento", required=True)
    parser.add_argument("--saida", required=True)
    args = parser.parse_args()
    try:
        target = Path(args.saida).resolve()
        repo = Path(__file__).resolve().parent
        if target == repo or repo in target.parents:
            raise ValueError("O arquivo privado deve ficar fora do GitHub")
        data = extrair_dados(
            Path(args.xml_referencia).read_bytes(), args.serie, args.numero_dps,
            args.competencia, args.vencimento
        )
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as dest:
            json.dump(data, dest, indent=2, ensure_ascii=False)
        print("Preparação local concluída:", target)
        print("Série API:", data["serie"], "Novo número DPS:", data["numero_dps"])
        print("Revisar todos os campos fiscais e a competência ANTES de assinar/transmitir.")
        print("Nenhuma DPS foi transmitida.")
        return 0
    except Exception as exc:
        print("Não foi possível preparar a DPS:", type(exc).__name__, str(exc)[:180], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
