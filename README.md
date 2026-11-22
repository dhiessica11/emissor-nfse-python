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
