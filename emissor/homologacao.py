"""Preparação técnica de DPS para homologação; nunca usa dados reais do repositório.

IMPORTANTE: gerador baseado na DPS de referência 1.01. A conformidade com o XSD
e com as regras correntes da produção restrita precisa ser verificada antes
de qualquer tentativa de emissão.
"""
from base64 import b64encode
from datetime import datetime
from decimal import Decimal, InvalidOperation
from gzip import compress
from pathlib import Path
import re

from lxml import etree

NAMESPACE = "http://www.sped.fazenda.gov.br/nfse"
HOMOLOGACAO = "https://sefin.producaorestrita.nfse.gov.br/SefinNacional"


def _tag(parent, name, value):
    elem = etree.SubElement(parent, f"{{{NAMESPACE}}}{name}")
    elem.text = str(value)
    return elem


def id_dps(municipio, cnpj, serie, numero):
    mun = str(municipio)
    taxpayer = re.sub(r"\D", "", str(cnpj))
    serie = str(serie)
    if not (re.fullmatch(r"\d{7}", mun) and
            re.fullmatch(r"\d{14}", taxpayer) and
            re.fullmatch(r"\d{1,5}", serie) and
            isinstance(numero, int) and 1 <= numero <= 999999999999999):
        raise ValueError("Município, CNPJ, série ou número da DPS inválidos")
    return f"DPS{mun}2{taxpayer}{int(serie):05d}{numero:015d}"


def construir_dps(dados):
    """Monta DPS 1.01 sem inferir parâmetros fiscais ou compartilhar dados."""
    required = (
        "municipio_emissor", "prestador_cnpj", "tomador_cnpj",
        "tomador_razao_social", "municipio_tomador", "cep_tomador",
        "logradouro_tomador", "numero_endereco_tomador", "bairro_tomador",
        "municipio_prestacao", "codigo_servico", "codigo_nbs",
        "descricao_servico", "valor", "serie", "numero_dps", "competencia",
        "data_emissao", "op_simp_nac", "reg_ap_trib_sn", "reg_esp_trib",
        "trib_issqn", "ret_issqn", "cst_pis_cofins", "ret_pis_cofins",
        "percentual_total_tributos_sn",
    )
    missing = [k for k in required if k not in dados or dados[k] in (None, "")]
    if missing:
        raise ValueError("Campos ausentes: " + ", ".join(missing))
    if not re.fullmatch(r"\d{6}", str(dados["codigo_servico"])):
        raise ValueError("Código de serviço deve conter 6 dígitos")
    if not re.fullmatch(r"\d{9}", str(dados["codigo_nbs"])):
        raise ValueError("NBS deve conter 9 dígitos")
    if not re.fullmatch(r"\d{8}", str(dados["cep_tomador"])):
        raise ValueError("CEP deve conter 8 dígitos")
    try:
        valor = Decimal(str(dados["valor"]))
        percentual = Decimal(str(dados["percentual_total_tributos_sn"]))
        emitted = datetime.fromisoformat(str(dados["data_emissao"]))
        competence = datetime.fromisoformat(str(dados["competencia"])).date()
    except (ValueError, InvalidOperation) as exc:
        raise ValueError("Data ou número inválido") from exc
    if emitted.utcoffset() is None:
        raise ValueError("Data de emissão deve incluir fuso horário")
    if not (valor.is_finite() and valor > 0 and valor.as_tuple().exponent >= -2
            and percentual.is_finite() and 0 <= percentual <= 100):
        raise ValueError("Valor ou percentual de tributos inválido")
    root = etree.Element(f"{{{NAMESPACE}}}DPS", nsmap={None: NAMESPACE}, versao="1.01")
    info = etree.SubElement(root, f"{{{NAMESPACE}}}infDPS")
    info.set("Id", id_dps(dados["municipio_emissor"], dados["prestador_cnpj"],
                          dados["serie"], int(dados["numero_dps"])))
    for name, value in (
        ("tpAmb", 2), ("dhEmi", dados["data_emissao"]),
        ("verAplic", "EmissorPythonHomologacao_0.1"),
        ("serie", int(dados["serie"])), ("nDPS", int(dados["numero_dps"])),
        ("dCompet", competence.isoformat()), ("tpEmit", 1),
        ("cLocEmi", dados["municipio_emissor"]),
    ):
        _tag(info, name, value)
    prest = etree.SubElement(info, f"{{{NAMESPACE}}}prest")
    _tag(prest, "CNPJ", re.sub(r"\D", "", str(dados["prestador_cnpj"])))
    reg = etree.SubElement(prest, f"{{{NAMESPACE}}}regTrib")
    for name, k in (("opSimpNac", "op_simp_nac"), ("regApTribSN", "reg_ap_trib_sn"),
                    ("regEspTrib", "reg_esp_trib")):
        _tag(reg, name, dados[k])
    toma = etree.SubElement(info, f"{{{NAMESPACE}}}toma")
    _tag(toma, "CNPJ", re.sub(r"\D", "", str(dados["tomador_cnpj"])))
    _tag(toma, "xNome", dados["tomador_razao_social"])
    endereco = etree.SubElement(toma, f"{{{NAMESPACE}}}end")
    nacional = etree.SubElement(endereco, f"{{{NAMESPACE}}}endNac")
    _tag(nacional, "cMun", dados["municipio_tomador"])
    _tag(nacional, "CEP", dados["cep_tomador"])
    for tag, field in (("xLgr", "logradouro_tomador"),
                       ("nro", "numero_endereco_tomador"),
                       ("xBairro", "bairro_tomador")):
        _tag(endereco, tag, dados[field])
    serv = etree.SubElement(info, f"{{{NAMESPACE}}}serv")
    location = etree.SubElement(serv, f"{{{NAMESPACE}}}locPrest")
    _tag(location, "cLocPrestacao", dados["municipio_prestacao"])
    cserv = etree.SubElement(serv, f"{{{NAMESPACE}}}cServ")
    for tag, field in (("cTribNac", "codigo_servico"),
                       ("xDescServ", "descricao_servico"),
                       ("cNBS", "codigo_nbs")):
        _tag(cserv, tag, dados[field])
    values = etree.SubElement(info, f"{{{NAMESPACE}}}valores")
    vp = etree.SubElement(values, f"{{{NAMESPACE}}}vServPrest")
    _tag(vp, "vServ", f"{valor:.2f}")
    tax = etree.SubElement(values, f"{{{NAMESPACE}}}trib")
    muni = etree.SubElement(tax, f"{{{NAMESPACE}}}tribMun")
    _tag(muni, "tribISSQN", dados["trib_issqn"])
    _tag(muni, "tpRetISSQN", dados["ret_issqn"])
    federal = etree.SubElement(tax, f"{{{NAMESPACE}}}tribFed")
    piscofins = etree.SubElement(federal, f"{{{NAMESPACE}}}piscofins")
    _tag(piscofins, "CST", dados["cst_pis_cofins"])
    _tag(piscofins, "tpRetPisCofins", dados["ret_pis_cofins"])
    total = etree.SubElement(tax, f"{{{NAMESPACE}}}totTrib")
    _tag(total, "pTotTribSN", f"{percentual:.2f}")
    return etree.tostring(root, xml_declaration=True, encoding="utf-8")


def validar_xsd(xml, caminho_xsd):
    schema_doc = etree.parse(str(caminho_xsd))
    schema = etree.XMLSchema(schema_doc)
    document = etree.fromstring(xml, parser=etree.XMLParser(resolve_entities=False, no_network=True))
    schema.assertValid(document)
    return True


def assinar_dps(xml, p12_bytes, senha):
    """Assina infDPS em memória, sem salvar chave privada ou certificado."""
    from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
    from signxml import XMLSigner, methods
    key, cert, chain = pkcs12.load_key_and_certificates(p12_bytes, senha.encode("utf-8"))
    if key is None or cert is None:
        raise ValueError("A1 não contém certificado e chave privada")
    doc = etree.fromstring(xml, parser=etree.XMLParser(resolve_entities=False, no_network=True))
    inf = doc.find(f"{{{NAMESPACE}}}infDPS")
    if inf is None or not inf.get("Id"):
        raise ValueError("infDPS e Id obrigatórios")
    # O signxml recebe o documento e ancora a assinatura no Id do infDPS.
    signer = XMLSigner(method=methods.enveloped, signature_algorithm="rsa-sha256",
                       digest_algorithm="sha256", c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    signed = signer.sign(
        doc, key=key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
        cert=cert.public_bytes(Encoding.PEM), reference_uri=f'#{inf.get("Id")}',
        id_attribute="Id",
    )
    return etree.tostring(signed, xml_declaration=True, encoding="utf-8")


def empacotar(xml_assinado):
    return {"dpsXmlGZipB64": b64encode(compress(xml_assinado)).decode("ascii")}
