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
6. Apenas após essas validações: implementar e homologar POST /nfse, consulta GET /dps/{id}, tratamento de rejeições, falhas e reconciliação, sem retry cego.
7. Homologar IBS/CBS segundo a documentação vigente e as características tributárias do prestador.

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
