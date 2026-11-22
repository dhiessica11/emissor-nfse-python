#!/usr/bin/env python3
"""Prepara oito rascunhos individuais de DPS, sem XML, certificado nem rede.

O mês de competência foi confirmado, mas o dia não. Portanto não gera XML
fiscal, não atribui data de emissão e NÃO transmite. Saída sempre privada.
"""
import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import sys

from emissor.core import carrega_clientes, cnpj_valido
from emissor.homologacao import id_dps

COMPETENCIA_MES = "2026-12"
VENCIMENTO = "2026-12-20"
VALOR = Decimal("500.00")
CAMPOS_REFERENCIA = (
    "municipio_emissor", "prestador_cnpj", "op_simp_nac",
    "reg_ap_trib_sn", "reg_esp_trib", "trib_issqn",
    "ret_issqn", "cst_pis_cofins", "ret_pis_cofins",
    "percentual_total_tributos_sn",
)


def montar_rascunhos(previas, cadastro, fiscal, numero_inicial):
    if (previas.get("tipo") != "PREVIA_OFFLINE_SEM_EMISSAO"
            or previas.get("competencia") != COMPETENCIA_MES
            or previas.get("vencimento") != VENCIMENTO
            or previas.get("quantidade") != 8
            or Decimal(str(previas.get("valor_total", ""))) != VALOR * 8):
        raise ValueError("Lote de prévias incompatível com dezembro/2026")
    docs = previas.get("documentos")
    if not isinstance(docs, list) or len(docs) != 8 or len(cadastro) != 8:
        raise ValueError("São necessários oito documentos e oito cadastros")
    if not isinstance(numero_inicial, int) or numero_inicial < 900003 or numero_inicial + 7 > 999999999999999:
        raise ValueError("Numeração proposta deve iniciar a partir de 900003")
    if not isinstance(fiscal, dict) or any(not str(fiscal.get(k, "")).strip() for k in CAMPOS_REFERENCIA):
        raise ValueError("Referência fiscal de novembro incompleta")
    prestador = re.sub(r"\D", "", str(fiscal["prestador_cnpj"]))
    if not cnpj_valido(prestador):
        raise ValueError("CNPJ do prestador na referência é inválido")
    if not re.fullmatch(r"\d{7}", str(fiscal["municipio_emissor"])):
        raise ValueError("Código do município emissor na referência inválido")
    por_id = {c["id"]: c for c in cadastro}
    if len(por_id) != 8:
        raise ValueError("IDs de cadastro repetidos")
    vistos = set()
    resultado = []
    for index, previa in enumerate(docs):
        cliente = por_id.get(previa.get("id"))
        if cliente is None or previa["id"] in vistos:
            raise ValueError("Identificador de tomador ausente ou repetido na prévia")
        vistos.add(previa["id"])
        if (re.sub(r"\D", "", str(cliente["cnpj"])) !=
                re.sub(r"\D", "", str(previa.get("tomador_cnpj", "")))):
            raise ValueError("CNPJ divergente entre prévia e cadastro")
        if cliente["razao_social"] != previa.get("tomador_razao_social"):
            raise ValueError("Razão social divergente entre prévia e cadastro")
        if (previa.get("competencia") != COMPETENCIA_MES or
                previa.get("vencimento") != VENCIMENTO or
                Decimal(str(previa.get("valor", "0"))) != VALOR or
                previa.get("situacao") != "PREVIA_NAO_TRANSMITIDA" or
                not previa.get("descricao_servico")):
            raise ValueError("Valor, descrição, vencimento ou estado divergente na prévia")
        cf = cliente["campos_fiscais"]
        expected = previa.get("campos_fiscais_referencia")
        if cf != expected:
            raise ValueError("Referência fiscal divergente entre cadastro e prévia")
        numero = numero_inicial + index
        serie = 1  # Série API do protótipo de homologação; verificar disponibilidade
        id_proposto = id_dps(fiscal["municipio_emissor"], prestador, serie, numero)
        dados = {
            "municipio_emissor": fiscal["municipio_emissor"],
            "prestador_cnpj": prestador,
            "tomador_cnpj": re.sub(r"\D", "", str(cliente["cnpj"])),
            "tomador_razao_social": cliente["razao_social"],
            "municipio_tomador": cliente["codigo_ibge_tomador"],
            "cep_tomador": re.sub(r"\D", "", str(cliente["cep_tomador"])),
            "logradouro_tomador": cliente["logradouro_tomador"],
            "numero_endereco_tomador": cliente["numero_endereco_tomador"],
            "bairro_tomador": cliente["bairro_tomador"],
            "complemento_endereco_tomador": cliente.get("complemento_endereco_tomador", ""),
            "municipio_prestacao": cf["municipio_prestacao_ibge"],
            "codigo_servico": cf["codigo_tributacao_nacional"],
            "codigo_nbs": cf["codigo_nbs"],
            "descricao_servico": previa["descricao_servico"],
            "valor": "500.00",
            "serie": str(serie),
            "numero_dps": numero,
            "competencia": None,
            "data_emissao": None,
            **{k: fiscal[k] for k in CAMPOS_REFERENCIA if k not in ("municipio_emissor", "prestador_cnpj")},
        }
        if (not re.fullmatch(r"\d{7}", str(dados["municipio_tomador"])) or
                not re.fullmatch(r"\d{8}", str(dados["cep_tomador"])) or
                not re.fullmatch(r"\d{6}", str(dados["codigo_servico"])) or
                not re.fullmatch(r"\d{9}", str(dados["codigo_nbs"]))):
            raise ValueError("Código IBGE, CEP, código de serviço ou NBS inválido")
        resultado.append({
            "tipo": "RASCUNHO_DPS_NAO_EMITIVEL",
            "situacao": "PENDENTE_VALIDACAO_FISCAL_E_DATAS",
            "unidade": cliente["unidade"],
            "competencia_mes_confirmada": COMPETENCIA_MES,
            "vencimento": VENCIMENTO,
            "id_dps_proposto_nao_reservado": id_proposto,
            "dados_preparatorios": dados,
            "pendencias_bloqueantes": [
                "Confirmar dia da competência para dezembro/2026",
                "Informar data real de emissão somente na execução futura",
                "Validar enquadramento contratual e tributação de dezembro",
                "Consultar controle de numeração e notas já existentes antes de qualquer emissão",
                "Validar assinatura e XSD vigentes após preencher as datas",
            ],
        })
    return resultado


def salvar_diretorio_novo(destino, documentos):
    destino = Path(destino).expanduser().resolve()
    raiz = Path(__file__).resolve().parent
    if destino == raiz or raiz in destino.parents:
        raise ValueError("A saída deve ficar fora do repositório público")
    destino.mkdir(mode=0o700, parents=True, exist_ok=False)
    destino.chmod(0o700)
    manifesto = {
        "tipo": "LOTE_RASCUNHOS_SEM_XML_OU_TRANSMISSAO",
        "competencia_mes": COMPETENCIA_MES, "vencimento": VENCIMENTO,
        "quantidade": len(documentos),
        "valor_total": "4000.00",
        "documentos": [
            {"unidade": d["unidade"],
             "id_dps_proposto_nao_reservado": d["id_dps_proposto_nao_reservado"],
             "arquivo": f'rascunho-{i:02d}.json'}
            for i, d in enumerate(documentos, 1)
        ]
    }
    arquivos = [(f'rascunho-{i:02d}.json', d) for i, d in enumerate(documentos, 1)]
    arquivos.append(("manifesto.json", manifesto))
    for nome, data in arquivos:
        path = destino / nome
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
    return destino


def main():
    ap = argparse.ArgumentParser(description="Oito rascunhos privados de DPS, SEM emissão")
    ap.add_argument("--previas", required=True)
    ap.add_argument("--cadastro", required=True)
    ap.add_argument("--referencia-fiscal", required=True,
                    help="dps.json privado de novembro (parâmetros apenas de referência)")
    ap.add_argument("--numero-inicial", type=int, default=900003,
                    help="Número apenas proposto e ainda não reservado (padrão 900003)")
    ap.add_argument("--saida-dir", required=True,
                    help="Diretório PRIVADO ainda inexistente, fora do Git")
    args = ap.parse_args()
    try:
        previas = json.loads(Path(args.previas).read_text(encoding="utf-8"))
        clientes = carrega_clientes(args.cadastro)
        fiscal = json.loads(Path(args.referencia_fiscal).read_text(encoding="utf-8"))
        docs = montar_rascunhos(previas, clientes, fiscal, args.numero_inicial)
        target = salvar_diretorio_novo(args.saida_dir, docs)
        print("8 RASCUNHOS INDIVIDUAIS PREPARADOS | TOTAL R$ 4.000,00")
        print("Arquivos privados:", target)
        print("Numeração somente PROPOSTA: não reservada e não verificada na SEFIN")
        print("Datas e validação fiscal pendentes; JSONs não são DPS emitíveis")
        print("Nenhum XML, assinatura ou transmissão realizada")
        return 0
    except Exception as exc:
        print("Falha na preparação:", type(exc).__name__, str(exc)[:240], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
