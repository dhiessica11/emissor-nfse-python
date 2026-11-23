#!/usr/bin/env python3
"""Painel local e offline de planejamento fiscal. NUNCA transmite notas."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import socket
import sys
from urllib.parse import parse_qs
import webbrowser

from emissor.core import carrega_clientes

HOST = "127.0.0.1"
BASE = Path.home() / ".local/share/nfse"
CADASTROS = (
    Path("/Volumes/KINGSTON 1/Developer/emissor-nfse/config/clientes.json"),
    Path(__file__).resolve().parent / "config/clientes.json",
)
DEFAULT_DESCRIPTION = (
    "Serviços de integração de sistemas em tecnologia da informação. "
    "02 parcela décimo terceiro contratual, conforme acordo de prestação de serviços. "
    "Dados para pagamento: PIX: 48.854.187/0001-17 Vencimento: 20/12/2026"
)


def find_cadastro(paths=CADASTROS):
    for path in paths:
        if path.is_file():
            return path
    return None


def listar_lotes(base=BASE):
    pasta = base / "lotes-painel"
    if not pasta.is_dir():
        return []
    result = []
    for path in sorted(pasta.glob("*/manifesto.json"), reverse=True)[:25]:
        try:
            dados = json.loads(path.read_text(encoding="utf-8"))
            if dados.get("tipo") == "LOTE_OFFLINE_PAINEL":
                result.append({
                    "competencia": dados["competencia"],
                    "vencimento": dados["vencimento"],
                    "quantidade": dados["quantidade"],
                    "total": dados["total"],
                    "situacao": dados["situacao"],
                })
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return result


def preparar_lote(campos, clientes, base=BASE):
    """Grava somente prévias; não importa código de envio/assinatura."""
    if len(clientes) != 8:
        raise ValueError("O cadastro precisa ter oito tomadores")
    try:
        competencia = date.fromisoformat(campos["competencia"])
        vencimento = date.fromisoformat(campos["vencimento"])
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("Competência e vencimento precisam ser datas válidas") from exc
    if not (2020 <= competencia.year <= 2100):
        raise ValueError("Ano da competência fora do intervalo admitido")
    if vencimento < competencia:
        raise ValueError("Vencimento não pode ser anterior à competência neste fluxo")
    descricao = str(campos.get("descricao", "")).strip()
    if not 10 <= len(descricao) <= 1500:
        raise ValueError("Informe uma descrição entre 10 e 1500 caracteres")
    documentos = []
    total = Decimal("0")
    vistos = set()
    for index, cliente in enumerate(clientes):
        key = "valor_" + str(index)
        try:
            valor = Decimal(str(campos[key]).replace(",", "."))
        except (InvalidOperation, KeyError) as exc:
            raise ValueError(f"Valor inválido para {cliente['unidade']}") from exc
        if not valor.is_finite() or valor <= 0 or valor.as_tuple().exponent < -2:
            raise ValueError(f"Valor inválido para {cliente['unidade']}")
        cnpj = re.sub(r"\D", "", str(cliente["cnpj"]))
        if cnpj in vistos:
            raise ValueError("CNPJ repetido")
        vistos.add(cnpj)
        total += valor
        documentos.append({
            "unidade": cliente["unidade"],
            "cnpj_tomador": cnpj,
            "razao_social": cliente["razao_social"],
            "competencia": competencia.isoformat(),
            "vencimento": vencimento.isoformat(),
            "valor": f"{valor:.2f}",
            "descricao": descricao,
            "campos_fiscais_referencia": cliente.get("campos_fiscais", {}),
            "situacao": "PREVIA_SEM_EFEITO_FISCAL",
            "data_emissao": None,
            "numero_dps": None,
            "pendencias": [
                "Conferir prestação de serviço, tributação e código de serviço",
                "Confirmar série e numeração na fonte oficial",
                "Assinar XML com certificado A1 somente na data real de emissão",
                "Autorizar explicitamente cada emissão em produção",
            ],
        })
    pasta = base / "lotes-painel"
    pasta.mkdir(mode=0o700, parents=True, exist_ok=True)
    pasta.chmod(0o700)
    # Nomes exclusivos: nenhum lote anterior é sobrescrito.
    nome = competencia.strftime("%Y%m%d") + "-" + secrets.token_hex(6)
    destino = pasta / nome
    destino.mkdir(mode=0o700)
    manifesto = {
        "tipo": "LOTE_OFFLINE_PAINEL",
        "competencia": competencia.isoformat(),
        "vencimento": vencimento.isoformat(),
        "quantidade": 8,
        "total": f"{total:.2f}",
        "situacao": "PREVIA_NAO_EMITIDA",
        "documentos": documentos,
    }
    fd = os.open(destino / "manifesto.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, indent=2, ensure_ascii=False)
    return manifesto


def moeda(valor):
    return "R$ " + f"{Decimal(str(valor)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def painel_html(clientes, lotes, token, mensagem="", erro=False):
    h = escape
    itens = []
    for i, c in enumerate(clientes):
        itens.append(
            "<tr><td>" + h(str(c["unidade"])) + "</td><td>" +
            h(str(c["razao_social"])) + "</td><td>" +
            h(str(c["cnpj"])) + "</td><td>" +
            f'<input name="valor_{i}" type="number" min="0.01" step="0.01" value="500.00" required></td></tr>'
        )
    historico = "".join(
        "<tr><td>" + h(x["competencia"]) + "</td><td>" +
        h(x["vencimento"]) + "</td><td>" + h(moeda(x["total"])) +
        "</td><td>" + h(x["situacao"]) + "</td></tr>" for x in lotes
    ) or '<tr><td colspan="4">Nenhum lote criado pelo painel.</td></tr>'
    banner = (
        '<p role="status" class="' + ("error" if erro else "ok") + '">' + h(mensagem) + "</p>"
        if mensagem else ""
    )
    if not clientes:
        form = ('<p class="error">Cadastro privado não localizado. Coloque o arquivo clientes.json '
                'na pasta config do projeto ou no SSD KINGSTON 1.</p>')
    else:
        form = (
            '<form method="post" action="/criar" translate="no"><input type="hidden" name="token" value="' + h(token) + '">'
            '<div class="duo"><label>Competência<input type="date" name="competencia" value="2026-12-01" required></label>'
            '<label>Vencimento<input type="date" name="vencimento" value="2026-12-20" required></label></div>'
            '<label>Descrição do serviço<textarea name="descricao" rows="4" maxlength="1500" required>' +
            h(DEFAULT_DESCRIPTION) + '</textarea></label>'
            '<div class="scroll"><table><thead><tr><th>Unidade</th><th>Razão social</th><th>CNPJ</th><th>Valor (R$)</th></tr></thead>'
            '<tbody>' + "".join(itens) + '</tbody></table></div>'
            '<button type="submit">Salvar prévia privada do lote</button></form>'
        )
    return ("""<!doctype html><html lang="pt-BR" translate="no"><head><meta charset="utf-8"><meta name="google" content="notranslate">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Central de Emissão NFS-e — preparação</title>
<style>
:root{color-scheme:light;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f7f5f3;color:#221a1c}
*{box-sizing:border-box}body{margin:0}header{background:#651c32;color:white;padding:24px 6vw}
header h1{margin:0;font-size:24px}header p{margin:8px 0 0;opacity:.9}
main{max-width:1100px;padding:24px;margin:auto}section{background:white;border:1px solid #ddd3d2;
border-radius:14px;padding:22px;margin:0 0 18px}h2{margin:0 0 14px;font-size:20px}
small,.muted{color:#655d60}label{display:block;font-weight:600;margin:12px 0}
input,textarea{display:block;width:100%;padding:12px;border:1px solid #b8adae;border-radius:7px;
font:inherit;margin-top:7px}textarea{resize:vertical}.duo{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px;min-width:680px}
td,th{text-align:left;padding:10px;border-bottom:1px solid #e5e0df}th{background:#f5f0ef}
td input{max-width:150px;padding:8px;margin:0}button{background:#651c32;color:white;border:0;
padding:14px 18px;border-radius:9px;font-weight:bold;font-size:15px;cursor:pointer;margin-top:18px}
.ok{background:#edf8ee;padding:14px;border-radius:8px}.error{background:#fff0f0;color:#892929;
padding:14px;border-radius:8px}footer{color:#605b5d;font-size:13px;padding:12px 0}
@media(max-width:620px){.duo{grid-template-columns:1fr}main{padding:12px}section{padding:16px}}
</style></head><body><header><h1>Central de Emissão NFS-e</h1>
<p>Painel local • planejamento offline • transmissão desativada</p></header>
<main>""" + banner + """<section><h2>Novo planejamento</h2>
<p class="muted">Os dados ficam neste Mac. Você poderá preparar outros meses sem usar o Terminal.
Este painel não cria DPS/XML fiscal, não assina e não transmite notas.</p>""" + form +
"""</section><section><h2>Histórico local de prévias</h2><div class="scroll"><table>
<thead><tr><th>Competência</th><th>Vencimento</th><th>Total</th><th>Situação</th></tr></thead>
<tbody>""" + historico + """</tbody></table></div></section>
<footer>Controle de emissão real, certificados, numeração e validação tributária são etapas pendentes.
O navegador deve acessar somente 127.0.0.1.</footer></main></body></html>""")


def criar_handler(token, cadastro_path, base):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            return  # Nunca registrar dados ou URLs fiscais.

        def _validar_host(self):
            host = self.headers.get("Host", "")
            return host in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def _validar_origem(self):
            origem = self.headers.get("Origin")
            return origem is None or origem in {
                f"http://127.0.0.1:{self.server.server_port}",
                f"http://localhost:{self.server.server_port}",
            }

        def _responder(self, html, codigo=200):
            data = html.encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; style-src 'unsafe-inline'; "
                             "form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def _pagina(self, mensagem="", erro=False):
            try:
                clientes = carrega_clientes(cadastro_path) if cadastro_path else []
                lotes = listar_lotes(base)
                self._responder(painel_html(clientes, lotes, token, mensagem, erro))
            except (OSError, ValueError) as exc:
                self._responder(painel_html([], [], token, str(exc), True), 400)

        def do_GET(self):
            if not self._validar_host():
                self.send_error(403)
                return
            if self.path != "/":
                self.send_error(404)
                return
            self._pagina()

        def do_POST(self):
            if not self._validar_host():
                self._responder(
                    "<h2>Endereço local não reconhecido</h2>"
                    "<p>Reabra o painel pelo atalho da Mesa do Mac.</p>", 403)
                return
            # Origin pode ser alterado por tradutores/extensões no Chrome.
            # A autorização é feita pelo token aleatório de 256 bits presente
            # somente no HTML fornecido via loopback, além da validação Host.
            # Nenhum cookie, credencial ou sessão ambiente é usado.
            # Não recusar apenas por divergência de Origin.
            if self.path != "/criar":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if length < 0 or length > 20_000:
                    self.send_error(413)
                    return
                payload = self.rfile.read(length).decode("utf-8", errors="strict")
                dados = parse_qs(payload, keep_blank_values=True, max_num_fields=40)
                if any(len(v) != 1 for v in dados.values()):
                    self.send_error(400)
                    return
                valores = {k: v[0] for k, v in dados.items()}
                if not secrets.compare_digest(valores.get("token", ""), token):
                    self._responder(
                        "<h2>Formulário expirado ou alterado</h2>"
                        "<p>Atualize a página (Command + R) antes de tentar novamente. "
                        "Se persistir, reabra o painel pelo atalho. "
                        "Não use formulários de abas antigas ou traduzidas. "
                        "Nenhuma prévia foi salva por esta tentativa.</p>", 403)
                    return
                if cadastro_path is None:
                    raise ValueError("Cadastro não localizado")
                clientes = carrega_clientes(cadastro_path)
                manifesto = preparar_lote(valores, clientes, base)
                self._pagina("Prévia privada salva: " + str(manifesto["quantidade"]) +
                             " tomadores, total de " + moeda(manifesto["total"]) +
                             ". Nenhuma nota emitida.")
            except (ValueError, UnicodeDecodeError, OSError) as exc:
                self._pagina("Não foi possível criar prévia: " + str(exc)[:180], True)
    return Handler


def iniciar():
    cadastro = find_cadastro()
    BASE.mkdir(mode=0o700, parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    # Bind estrito no loopback IPv4; sem acesso remoto à rede local.
    with ThreadingHTTPServer((HOST, 0), criar_handler(token, cadastro, BASE)) as server:
        server.daemon_threads = True
        url = f"http://{HOST}:{server.server_port}/"
        print("Central NFS-e local iniciada. Feche esta janela para encerrar.")
        print("Endereço:", url)
        print("Cadastro:", cadastro if cadastro else "não encontrado")
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            return


if __name__ == "__main__":
    iniciar()
