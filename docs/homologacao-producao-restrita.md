# Homologação em produção restrita — 22/11/2026

## Contexto
Integração com a API SEFIN Nacional para NFS-e recorrentes. O repositório é
**público** e usa apenas dados fictícios. O código ainda **não emite** notas.

## Evidências automatizadas
- Geração de DPS XML 1.01 com campos estruturados; não reutiliza assinatura ou Id da NFS-e anterior.
- Formação do identificador da DPS com município, tipo de inscrição, CNPJ, série e número.
- Codificação GZip + Base64 em `dpsXmlGZipB64`.
- XMLDSIG RSA-SHA256 assinado com certificado PKCS#12 **fictício criado em memória** durante os testes.
- Validação criptográfica da assinatura pelos testes.
- Prévia, confirmação, controle de estado e bloqueios locais testados.
- Execução CI em Python 3.11, 3.12, 3.13.

## Evidências que ainda faltam no Mac do contribuinte
1. Baixar o **XSD específico do ambiente de produção restrita** e identificar o XSD principal da DPS e dependências (includes/imports). O download automático do pacote oficial não foi realizado neste ambiente.
2. Comparar campos gerados com o XSD vigente (produção restrita pode divergir da versão da nota histórica).
3. Preparar arquivo JSON **privado** com os campos reais revisados; dados pessoais e empresariais não devem aparecer em repositório ou ações do GitHub.
4. Executar a assinatura usando A1 válido no Mac, conferindo CNPJ, validade e autorização.
5. Executar consulta mTLS somente leitura: `verificar_conexao_restrita.py`.
6. O envio experimental de uma DPS para POST /nfse foi implementado em `transmitir_teste_restrito.py`, com consulta prévia GET /dps/{id}, confirmação manual e registro de tentativa. **Sua execução com o A1 real e o aceite pela API permanecem pendentes.**
7. Homologar IBS/CBS segundo a documentação vigente e as características tributárias do prestador.\n8. Para o lote de oito notas, implementar e validar emissão individual, tratamento de rejeições e reconciliação antes de ativar o botão de lote.

## Comandos locais

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v

# Apenas consulta mTLS: não emite documento.
python verificar_conexao_restrita.py \
  --certificado /caminho/privado/certificado.p12 \
  --municipio 5003702

# Validação XML + assinatura local. Ainda não transmite:
python validar_homologacao.py \
  --dados /caminho/privado/dps.json \
  --xsd /caminho/privado/arquivo-DPS-oficial.xsd \
  --certificado /caminho/privado/certificado.p12 \
  --saida /caminho/privado/resultado
```

As duas rotinas solicitam a senha diretamente no Terminal. Nenhuma senha
é gravada, e nenhuma nota é transmitida. O validador pode escrever XML
com dados reais em pasta privada: jamais envie esse arquivo ao GitHub.

## Classificação do resultado
- **Aprovado em CI:** estrutura e assinatura criptográfica com dados fictícios.
- **Não validado:** conformidade do XML com XSD oficial de produção restrita.
- **Não validado:** certificado do contribuinte e autenticação mTLS.
- **Não validado:** transmissão real para homologação e consulta da NFS-e.
- **Não autorizado:** qualquer envio à produção.

## Referências oficiais
- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/producao-restrita
- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao
- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual

## Envio de UMA DPS em produção restrita (opcional, somente após XSD e assinatura)

```bash
python transmitir_teste_restrito.py \
  --xml /caminho/privado/resultado/dps-assinada.xml \
  --xsd /caminho/privado/arquivo-DPS-oficial.xsd \
  --certificado /caminho/privado/certificado.p12 \
  --registro /caminho/privado/registro-competencia-cliente.json
```

O programa solicita a senha do A1 e exige digitar
`HOMOLOGAR UMA DPS` antes do POST. É obrigatório escolher um identificador
de DPS novo e confirmar dados fiscais válidos do prestador e tomador.

**Nunca executar** esse teste usando uma nota antiga, duplicando número/série,
sem conferência da legislação, ou com arquivos compartilhados publicamente.
Uma tentativa cria um registro privativo `PENDENTE_CONSULTA` mesmo em falha de
rede. Não excluir nem ignorar esse registro para tentar novamente: conferir
manualmente no ambiente restrito, evitando duplicação.

## Atualização técnica de 22/11/2026

- HTTP 200 confirmado em consulta ADN de parametrização municipal no Mac,
  usando arquivo A1 local; o endpoint por si só não prova autenticação exigida
  pela API SEFIN de emissão.
- Disponibilizado `baixar_esquemas_restritos.py` para o pacote oficial
  `esquemas_prod_restrita_20261020.zip`. **Download e validação do XSD
  oficial ainda dependem de execução no Mac**.
- Disponibilizado `preparar_dps_referencia.py`, que extrai os campos da DPS
  de um XML autorizado e prepara **outro** documento com nova competência,
  série, número e vencimento, sempre em arquivo privado, sem transmitir.
- A série **70000** das notas originadas no Portal Web não serve para
  emissão via API. O gerador e o envio experimental bloqueiam séries fora
  de **1–49999**.
- Adicionadas validações de pasta privada, CNPJ de confirmação e bloqueio
  de conteúdo demonstrativo na rotina de envio em produção restrita.
- CI validou 19 testes em cada uma das três versões Python 3.11, 3.12 e
  3.13, na execução:
  https://github.com/dhiessica11/emissor-nfse-python/actions/runs/45034376435
- A assinatura com certificado fictício foi testada, mas **não** há evidência
  de autorização de DPS real em produção restrita ou produção.
