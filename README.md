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
