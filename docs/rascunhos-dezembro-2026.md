# Rascunhos individuais — dezembro de 2026

Este procedimento **não gera XML fiscal, não assina DPS, não acessa a SEFIN e não emite notas**. A competência foi confirmada apenas como **dezembro/2026**, sem indicação de dia exato; por isso, os campos `competencia` e `data_emissao` permanecem `null` em todos os documentos.

Oito tomadores reais ficam em cadastro privado fora do controle de versão. São esperados R$ 500,00 por tomador, R$ 4.000,00 no total, vencimento em 20/12/2026 e a descrição estabelecida para a segunda parcela contratual.

## Preparação no Mac

Execute dentro de `$HOME/Developer/emissor-nfse-python`, com o ambiente virtual ativo:

```bash
git pull origin main
python preparar_rascunhos_dps_dezembro.py \
  --previas "$HOME/.local/share/nfse/previas-dezembro-2026.json" \
  --cadastro "/Volumes/KINGSTON 1/Developer/emissor-nfse/config/clientes.json" \
  --referencia-fiscal "$HOME/.local/share/nfse/homologacao-006/dps.json" \
  --numero-inicial 900003 \
  --saida-dir "$HOME/.local/share/nfse/rascunhos-dezembro-2026"
```

A referência fiscal é um arquivo privado da homologação anterior e **não substitui a conferência fiscal de dezembro**. A numeração 900003 a 900010 é apenas **proposta**, não uma reserva e não uma consulta de disponibilidade à SEFIN. Antes de qualquer emissão futura, é obrigatória a conciliação com notas já emitidas e numeração utilizada, inclusive em outros emissores.

O programa exige oito CNPJs distintos e válidos, verifica que os oito registros de prévia batem com o cadastro e recusa sobrescrever um diretório existente. Os arquivos criados têm permissões privadas.

## Saída

- `manifesto.json`: índice das oito unidades e dos números propostos.
- `rascunho-01.json` a `rascunho-08.json`: campos cadastrais e fiscais de referência com datas ainda indefinidas, pendências bloqueantes explícitas.

**Não passe esses JSONs diretamente a rotinas de transmissão.** Eles não são DPS válidas até que os dados fiscais sejam aprovados e as datas reais definidas, e um novo estágio de construção/validação seja executado.
