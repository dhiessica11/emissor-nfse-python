# Central de Emissão NFS-e — painel local (versão inicial)

Este painel é um aplicativo **offline**, que abre no navegador do próprio Mac.
Ele serve para **preparar prévias recorrentes**, consultar o histórico local das
prévias criadas pelo painel e conferir os oito tomadores.

**Não emite NFS-e.** Esta versão não prepara XML fiscal nem DPS assinadas,
não lê o A1, não pede senha e não se conecta à SEFIN.

## Instalar o atalho (uma única vez)

Na pasta do projeto que já está instalada no Mac:

\`\`\`bash
cd "$HOME/Developer/emissor-nfse-python"
git pull origin main
source .venv/bin/activate
python instalar_atalho_mac.py
\`\`\`

Depois disso, dê **dois cliques** no arquivo \`Central NFS-e.command\`
que aparecerá na Mesa/Desktop. Uma janela de Terminal abrirá o servidor
**somente em 127.0.0.1** e o navegador abrirá o painel automaticamente.
A partir dessa instalação inicial, não é necessário digitar comandos
para abrir o painel. **Feche o Terminal do atalho para encerrar o painel.**

Se o macOS bloquear a abertura do \`.command\`, abra as configurações de
Privacidade e Segurança do macOS e autorize o arquivo apenas se você
reconhecer este atalho instalado localmente. Nunca execute anexos
\`.command\` de origem desconhecida.

## Caminhos usados

Cadastro lido automaticamente, nesta ordem:

1. \`/Volumes/KINGSTON 1/Developer/emissor-nfse/config/clientes.json\`
2. \`$HOME/Developer/emissor-nfse-python/config/clientes.json\`

As novas prévias são criadas exclusivamente em
\`$HOME/.local/share/nfse/lotes-painel/<competencia>-<identificador>/manifesto.json\`.
A cada clique é criada uma pasta **nova**, sem sobrescrever lote anterior.
Não são alterados os rascunhos de dezembro previamente preparados,
localizados em \`rascunhos-dezembro-2026-competencia-01\`.

## O que pode fazer no painel

- Visualizar oito tomadores e respectivos CNPJs de seu cadastro local.
- Informar uma competência e um vencimento completos.
- Editar a descrição e o valor de cada tomador.
- Salvar um novo lote de **prévias**, com proteção contra valores e datas inválidos.
- Consultar histórico de prévias criadas neste painel.

**Limitações:** ainda não há edição do cadastro nem importação dos
rascunhos criados antes do painel; o histórico mostrado contém somente
prévias criadas nesta interface. A descrição inicial é uma sugestão
do lote de dezembro/2026, que deve ser alterada em novas competências.
A competência e valores nunca são considerados validados fiscalmente
apenas por serem salvos. A numeração de DPS e a data real de emissão
não são preenchidas nesta versão.

As melhorias futuras (XML, validação XSD, assinatura A1, integração e emissão
real) demandam implementação, validação fiscal, verificação de duplicidade
e confirmação explícita de emissão. Nenhum botão de transmissão está ativo.
