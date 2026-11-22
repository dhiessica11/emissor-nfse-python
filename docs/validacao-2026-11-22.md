# Relatório de validação — 2026-11-22

## Escopo
Versão pública de um protótipo Python para **prévia e simulação offline de oito notas recorrentes**. Não há envio para serviços fiscais.

## Evidências verificadas
- Projeto hospedado em repositório público com cadastros demonstrativos fictícios.
- Dados operacionais reais, XML de documento autorizado, DANFSe, certificado A1 e credenciais **não foram adicionados ao repositório**.
- Workflow `.github/workflows/python-tests.yml` criado para teste automatizado em Python 3.11, 3.12 e 3.13.
- Em 22/11/2026, a execução [45031037950](https://github.com/dhiessica11/emissor-nfse-python/actions/runs/45031037950) concluiu os três jobs com sucesso.
- Testes cobrindo cadastro de oito tomadores, CNPJ, competência, valor positivo, prévia CLI, confirmação cancelada, persistência da simulação e bloqueio de substituição de estado TRANSMITIDA por SIMULADA.

## Limitações e pendências
1. Os testes atuais cobrem **somente lógica de negócio local**; não validam conformidade fiscal da DPS nem a assinatura XML.
2. O código ainda não gera DPS conforme XSD, não usa o certificado A1 para autenticar e não chama APIs.
3. Uma referência XML autorizada foi analisada fora do repositório. Ela mostra uma DPS de versão 1.01, mas **não substitui** a validação da documentação oficial vigente em cada competência.
4. Regras de IBS/CBS dependem da legislação, do enquadramento do prestador e do leiaute em vigor. A ausência de grupo em notas passadas não justifica supressão futura.
5. O banco SQLite verifica estados conhecidos localmente; **não garante** ausência de notas já emitidas pelo portal web ou por outro sistema. É indispensável consultar a SEFIN antes de eventual retransmissão.
6. Certificado digital e senha devem permanecer apenas no Mac do usuário. A validação do A1 na máquina local, incluindo prazo de validade, chave privada e titularidade, não foi executada remotamente.
7. O sistema não está homologado em produção restrita. Nunca utilizar esta versão para emissão real.

## Critérios para habilitar emissão fiscal
- Validar XSD, regras de negócio e legislação atualizadas com documentos oficiais e responsável fiscal.
- Gerar DPS sem reaproveitar identificadores nem assinaturas de notas anteriores.
- Assinar DPS corretamente e autenticar requisições via certificado A1 local.
- Homologar emissão, consulta, rejeição, falha de rede, repetição segura e reconciliação.
- Implantar prévia e confirmação humana obrigatórias, seguidas do registro de XML e chave autorizados.
- Validar explicitamente que os oito clientes e os valores estão corretos no cadastro **privado**.

## Referências
- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/documentacao-atual
- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/producao-restrita
- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao
