# Mapeamento fiscal — referência técnica sem dados reais

> Este documento explica campos observados em uma DPS autorizada de referência, **sem reproduzir XML real ou valores, identificadores, CNPJs ou chaves fiscais**. Não representa parecer tributário ou autorização de emissão.

## Campos de DPS (leiaute 1.01)

| XPath relativo a infDPS | Interpretação |
|---|---|
| tpAmb | Ambiente de transmissão; não confundir com ambGer da NFS-e autorizada |
| dhEmi | Data/hora de emissão da DPS |
| serie, nDPS | Série e número próprios da DPS; não reutilizar |
| dCompet | Competência da prestação |
| tpEmit, cLocEmi | Tipo de emissor e município de emissão |
| prest/regTrib/opSimpNac | Opção pelo Simples Nacional |
| prest/regTrib/regApTribSN | Regime de apuração do Simples |
| prest/regTrib/regEspTrib | Regime especial |
| toma | Dados do tomador |
| serv/locPrest/cLocPrestacao | Município da prestação |
| serv/cServ/cTribNac | Código nacional de tributação |
| serv/cServ/cNBS | Código NBS |
| valores/vServPrest/vServ | Valor do serviço |
| valores/trib/tribMun/tribISSQN | Indicador de tributação do ISS |
| valores/trib/tribMun/tpRetISSQN | Indicador de retenção de ISS |
| valores/trib/tribFed/piscofins/CST | Código tributário PIS/COFINS |
| valores/trib/tribFed/piscofins/tpRetPisCofins | Retenção PIS/COFINS |
| valores/trib/totTrib/pTotTribSN | Percentual de tributos informado para Simples Nacional |

## Cuidados importantes

- O XML autorizado inclui informações processadas pelo emissor que **não foram necessariamente digitadas na DPS**, como valor de ISS apurado e alíquota aplicada.
- `pTotTribSN` **não deve ser interpretado como alíquota de ISS**.
- A ausência de grupo `IBSCBS` em uma nota anterior não autoriza omiti-lo em novas competências. Verificar legislação, cronograma e notas técnicas vigentes, incluindo exigências para Simples Nacional.
- Há distinção entre versão do leiaute, ambiente da DPS e ambiente gerador da NFS-e.
- Não reaproveitar identificação da DPS, assinatura, valores de digest, certificado do assinante da NFS-e nem identificadores de documentos autorizados.
- O XML autorizado não é, por si só, um modelo para assinar uma nova DPS: gerar XML novo conforme XSD e requisitos de assinatura.
- A apuração tributária deve ser validada com profissional responsável antes de qualquer transmissão real.

## Fontes oficiais

- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/documentacao-atual
- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/producao-restrita
- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao
