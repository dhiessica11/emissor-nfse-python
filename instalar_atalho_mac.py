#!/usr/bin/env python3
"""Instala atalho executável no Desktop para abrir o painel sem comandos futuros."""
from pathlib import Path
import os
import stat
import sys

PROJETO = Path(__file__).resolve().parent


def instalar(desktop, projeto=PROJETO):
    desktop = Path(desktop).expanduser().resolve()
    if not desktop.is_dir():
        raise FileNotFoundError("Pasta Mesa/Desktop não localizada")
    python = projeto / ".venv/bin/python"
    painel = projeto / "painel_local.py"
    if not painel.is_file():
        raise FileNotFoundError("painel_local.py não existe")
    if not python.is_file():
        raise FileNotFoundError("Ambiente virtual ausente em .venv")
    destino = desktop / "Central NFS-e.command"
    if destino.exists():
        raise FileExistsError("Atalho já existe. Não será sobrescrito")
    # Os caminhos são inseridos como literais em aspas simples do shell.
    # Escapamos aspas simples para evitar execução de trechos do caminho.
    def q(path):
        return "'" + str(path).replace("'", "'\"'\"'") + "'"
    linhas = (
        "#!/bin/zsh\n"
        "cd " + q(projeto) + " || exit 1\n"
        "echo 'Abrindo Central de Emissão NFS-e no navegador...'\n"
        + q(python) + " " + q(painel) + "\n"
        "echo 'Painel encerrado. Pressione Enter para fechar esta janela.'\n"
        "read -r\n"
    )
    fd = os.open(destino, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o700)
    with os.fdopen(fd, "w", encoding="utf-8") as arq:
        arq.write(linhas)
    destino.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    return destino


def main():
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home() / "Mesa"
    try:
        caminho = instalar(desktop)
        print("Atalho instalado:", caminho)
        print("Da próxima vez, abra com dois cliques no Finder.")
        print("Para parar o painel, feche a janela do Terminal aberta pelo atalho.")
        return 0
    except Exception as exc:
        print("Não foi possível instalar atalho:", type(exc).__name__, str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
