"""Validação e histórico para simulação offline."""
import json
import re
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


class ValidationError(Exception):
    pass


def cnpj_valido(value):
    n = re.sub(r"\D", "", str(value))
    if len(n) != 14 or len(set(n)) == 1:
        return False
    for size in (12, 13):
        weights = ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if size == 12
                   else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        digit = 11 - sum(int(x) * w for x, w in zip(n[:size], weights)) % 11
        if (0 if digit >= 10 else digit) != int(n[size]):
            return False
    return True


def competencia_valida(value):
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValidationError("Competência deve seguir AAAA-MM.")
    year, month = map(int, value.split("-"))
    if not (2000 <= year <= 2100 and 1 <= month <= 12):
        raise ValidationError("Competência inválida.")
    return value


def carrega_clientes(path):
    clients = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(clients, list) or len(clients) != 8:
        raise ValidationError("O cadastro deve conter exatamente 8 empresas.")
    ids, cnpjs = set(), set()
    for pos, client in enumerate(clients, 1):
        if not isinstance(client, dict):
            raise ValidationError(f"Cliente {pos}: objeto inválido.")
        client_id = client.get("id")
        cnpj = re.sub(r"\D", "", str(client.get("cnpj", "")))
        if not client_id or client_id in ids:
            raise ValidationError(f"Cliente {pos}: ID ausente ou repetido.")
        if not cnpj_valido(cnpj) or cnpj in cnpjs:
            raise ValidationError(f"Cliente {pos}: CNPJ inválido ou repetido.")
        if not str(client.get("razao_social", "")).strip():
            raise ValidationError(f"Cliente {pos}: razão social obrigatória.")
        if not str(client.get("descricao_servico", "")).strip():
            raise ValidationError(f"Cliente {pos}: descrição obrigatória.")
        try:
            price = Decimal(str(client.get("valor", "")))
        except InvalidOperation as exc:
            raise ValidationError(f"Cliente {pos}: valor inválido.") from exc
        if not price.is_finite() or price <= 0 or price.as_tuple().exponent < -2:
            raise ValidationError(f"Cliente {pos}: valor deve ser positivo, até duas casas.")
        if not isinstance(client.get("campos_fiscais"), dict) or not client["campos_fiscais"]:
            raise ValidationError(f"Cliente {pos}: campos fiscais obrigatórios.")
        ids.add(client_id)
        cnpjs.add(cnpj)
    return clients


def conectar(path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(target)
    db.execute("""CREATE TABLE IF NOT EXISTS emissao (
        cliente_id TEXT NOT NULL,
        competencia TEXT NOT NULL,
        estado TEXT NOT NULL,
        atualizado_em TEXT NOT NULL,
        observacao TEXT NOT NULL DEFAULT '',
        PRIMARY KEY (cliente_id, competencia))""")
    db.commit()
    return db


def status(db, client_id, competence):
    row = db.execute(
        "SELECT estado FROM emissao WHERE cliente_id=? AND competencia=?",
        (client_id, competence),
    ).fetchone()
    return row[0] if row else None


def gravar_simulacoes(db, clients, competence):
    now = datetime.now(timezone.utc).isoformat()
    with db:
        for client in clients:
            current = status(db, client["id"], competence)
            if current in {"AUTORIZADA", "PENDENTE_CONSULTA", "TRANSMITIDA"}:
                raise ValidationError(
                    f'{client["id"]}: {current}; consulte o portal antes de repetir.'
                )
        for client in clients:
            db.execute(
                """INSERT INTO emissao(cliente_id, competencia, estado, atualizado_em, observacao)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(cliente_id, competencia) DO UPDATE SET
                   estado=excluded.estado, atualizado_em=excluded.atualizado_em,
                   observacao=excluded.observacao""",
                (client["id"], competence, "SIMULADA", now, "Nenhum documento enviado."),
            )
