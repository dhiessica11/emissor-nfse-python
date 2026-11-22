# Emissor NFS-e Python

Protótipo de automação local e manual para **prévia e simulação offline de 8 NFS-e recorrentes**, desenvolvido em Python para macOS.

> **Estado do projeto:** protótipo. Ainda **não transmite NFS-e**, não assina a DPS nem executa chamadas à API da SEFIN Nacional. Não é um emissor fiscal pronto para produção.

## Funcionalidades

- Cadastro local de oito tomadores em JSON, não versionado
- Validação de CNPJ, competência e valores
- Prévia do lote no terminal e confirmação explícita
- Histórico de simulação em SQLite e proteção contra estados de transmissão real
- Inspeção local opcional de certificado A1
- Testes automatizados com `unittest`
- Dados demonstrativos fictícios no repositório

## Instalação (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp config/clientes.exemplo.json config/clientes.json
cp config/prestador.exemplo.json config/prestador.json
python -m unittest discover -s tests -v
```

Edite os arquivos `config/clientes.json` e `config/prestador.json` apenas no seu computador. Os exemplos não são válidos para emissão fiscal.

## Prévia

```bash
python emitir.py --competencia 2026-12 --vencimento 2027-01-01
```

## Simulação offline

```bash
python emitir.py --competencia 2026-12 --vencimento 2027-01-01 --simular
```

A confirmação exige digitar `SIMULAR 8 NOTAS`. Nenhuma chamada externa é executada.

## Certificado A1

```bash
python verificar_certificado.py /caminho/privado/certificado.p12
```

A senha é solicitada de forma oculta e não é gravada pelo script.

## Estrutura

- `emitir.py` — prévia e simulação offline
- `emissor/core.py` — validação, persistência e bloqueios de duplicidade
- `verificar_certificado.py` — inspeção local de certificado A1
- `config/*.exemplo.json` — dados fictícios
- `tests/` — testes automatizados
- `docs/mapeamento-fiscal.md` — mapeamento conceitual sem dados reais

## Próximas etapas

1. Confirmar as regras fiscais aplicáveis com a contabilidade e documentação vigente
2. Implementar o gerador da DPS conforme os XSD oficiais, sem copiar XML autorizado
3. Implementar assinatura da DPS e autenticação mTLS com certificado A1 local
4. Realizar testes em produção restrita e consultar o resultado antes de repetir envios
5. Liberar emissão real somente com conferência manual e controles de duplicidade

## Documentação oficial

- [Documentação atual](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/documentacao-atual)
- [Produção restrita](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/producao-restrita)
- [APIs da plataforma](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao)

## Privacidade

Não publique XMLs autorizados, DANFSe, CNPJs reais, dados de tomadores, certificados, senhas, chaves fiscais ou bases SQLite. O `.gitignore` não elimina segredos já enviados em commits antigos.

## Validação técnica em produção restrita (sem envio)

Foi incluído o módulo `emissor/homologacao.py` para montar uma DPS em formato
1.01 e realizar assinatura XMLDSIG local. A conformidade do XML deve ser
verificada com o XSD oficial **específico da produção restrita**, que não é
distribuído neste repositório.

Baixe o pacote oficial de XSD:
https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/producao-restrita

No Mac, mantenha o certificado `.p12`, o cadastro real e o XSD em pasta
**privada**. Prepare um arquivo JSON privado com os campos exigidos pela
função `construir_dps` (consulte `tests/test_homologacao.py` apenas para
estrutura; os dados de teste são fictícios). Execute:

```bash
python validar_homologacao.py \
  --dados /caminho/privado/dps.json \
  --xsd /caminho/privado/DPS_v1.01.xsd \
  --certificado /caminho/privado/certificado.p12 \
  --saida /caminho/privado/resultado-validacao
```

Substitua o nome do XSD pelo arquivo real presente no pacote oficial.
A senha é solicitada de forma oculta no Terminal; os artefatos locais podem
conter dados fiscais sensíveis, portanto **nunca devem ser enviados ao GitHub**.
O diretório deve estar fora do repositório. A rotina exige que os arquivos
de saída ainda não existam, evitando sobrescrita acidental.

**Status real:** geração de XML, empacotamento e assinatura testados com
certificado fictício em CI. A verificação de esquema com os XSD oficiais,
a assinatura com A1 real, o handshake mTLS e o envio/retorno da API
**ainda precisam ser executados no Mac do titular**. O script não faz POST.
A assinatura somente com XSD válido não garante aceite fiscal.

A referência para a API de testes é:
https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional/docs/index

Não envie arquivos reais, certificados ou senhas a workflows públicos do GitHub.

### Teste de conexão com a SEFIN Nacional (somente leitura)

Para testar a autenticação mTLS com A1 no Mac, sem emissão fiscal:

```bash
python verificar_conexao_restrita.py --certificado /caminho/privado/certificado.p12 --municipio 5003702
```

O comando usa HTTPS com validação TLS, não segue redirecionamentos, não imprime
respostas com dados fiscais e apaga os arquivos PEM temporários ao terminar.
Um HTTP diferente de 200 requer investigação; não é prova de validade do certificado.

[Relatório de homologação técnica](docs/homologacao-producao-restrita.md)

## Fluxo completo de homologação local (Mac)

**Nunca coloque dados reais no GitHub.** Trabalhe com arquivos privados fora do repositório.

1. Baixe os esquemas oficiais da produção restrita:

```bash
python baixar_esquemas_restritos.py --destino "$HOME/Documents/NFSe-Privado/xsd-20261020"
find "$HOME/Documents/NFSe-Privado/xsd-20261020" -iname '*DPS*.xsd'
```

2. Se possuir localmente o XML autorizado de uma nota anterior, prepare o JSON
de uma **nova** DPS de homologação, conferindo série e número ainda não usados:

```bash
python preparar_dps_referencia.py \
  --xml-referencia "$HOME/Documents/NFSe-Privado/nota-referencia.xml" \
  --serie 1 --numero-dps 1 \
  --competencia 2026-11-22 --vencimento 01/12/2026 \
  --saida "$HOME/Documents/NFSe-Privado/nova-dps.json"
```

O exemplo da série 1 e número 1 **não confirma que estão disponíveis**;
antes do envio, confira se já foram utilizados no mesmo ambiente. A faixa
**00001–49999** é reservada ao aplicativo próprio/API; a série **70000**
das notas históricas corresponde ao Emissor Web e não deve ser reutilizada.

3. Revise manualmente os campos fiscais do JSON com a documentação atual
e execute `validar_homologacao.py`, passando o XSD principal da DPS extraído
do pacote oficial, e o certificado `.p12` privado.
4. Só após resultado válido, execute `transmitir_teste_restrito.py` com
`--confirmar-cnpj`, XML assinado, XSD, A1 e registro privado. O programa
só envia a **produção restrita**, exige confirmação e bloqueia retries.

O pacote de produção restrita em 22/11/2026 é o identificado no portal
oficial como `esquemas_prod_restrita_20261020.zip`. A inclusão de
campos IBS/CBS e suas regras depende do XSD e das orientações vigentes.
[Orientações detalhadas](docs/homologacao-producao-restrita.md).

O pacote XSD não foi executado contra os dados reais neste ambiente;
qualquer inconsistência retornada no Mac deverá ser corrigida antes do POST.

## Um comando: pré-homologação local completa

Depois de instalar dependências e salvar o XML autorizado de referência
em pasta privada, execute:

```bash
python homologar_localmente.py \
  --xml-referencia "/caminho/privado/nota-referencia.xml" \
  --certificado "/caminho/privado/certificado.p12" \
  --serie 1 --numero-dps 1 \
  --competencia 2026-11-22 --vencimento 01/12/2026 \
  --pasta-privada "$HOME/.local/share/nfse/teste-001"
```

O comando baixa o pacote XSD oficial de produção restrita, extrai os dados
da DPS anterior, prepara **um novo documento de teste**, assina com o A1 local,
valida XMLDSIG e tenta validar o XSD. Não faz transmissão à SEFIN.
Escolha um número de DPS ainda não usado, e reveja os dados da nota anterior
antes de testar. Uma reprovação pelo XSD deve ser corrigida no código; **não
ignore o erro nem use o emissor real até resolver**.

Depois do resultado positivo, a emissão no ambiente restrito deve ser
efetuada separadamente com confirmação explícita, usando
`transmitir_teste_restrito.py` e seu parâmetro `--confirmar-cnpj`.
O ambiente real não é acessível por esse script.
