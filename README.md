# MarketScope — Campanhas de Pneus Portugal

Dashboard interativo de monitorização de campanhas promocionais de pneus ligeiros em Portugal.

## Componentes
- `index.html`: dashboard interativo.
- `campanhas.csv`: base de dados inicial do dashboard; os registos são preliminares e não constituem inventário exaustivo.
- `revisao.html`: área de revisão de candidatas recolhidas automaticamente.
- `scripts/monitorizar_fontes.py`: verifica alterações técnicas nas páginas-fonte já registadas; não interpreta semanticamente o conteúdo.
- `scripts/recolher_campanhas.py`: recolhe resultados de pesquisa RSS como potenciais campanhas.
- `scripts/interpretar_campanhas.py`: sugere campos a partir do título e publicador RSS, sem confirmar factos.
- `.github/workflows/monitorizacao.yml`: execução agendada e manual da monitorização.
- `.github/workflows/pages.yml`: publicação do site através do GitHub Pages.

## Dashboard e revisão
- Dashboard: https://bruno1996santos-jpg.github.io/marketscope-pneus-portugal/
- Revisão: https://bruno1996santos-jpg.github.io/marketscope-pneus-portugal/revisao.html

Na área de revisão, consulte a fonte original, corrija os campos e marque cada candidata como aprovada, rejeitada ou pendente. As alterações e decisões são guardadas no armazenamento local do navegador usado para a revisão. Não são enviadas automaticamente para o GitHub. Exporte as campanhas aprovadas em JSON ou CSV para posterior integração manual na base de dados do dashboard. Limpar os dados do navegador ou usar outro dispositivo pode tornar as alterações locais indisponíveis.

## Monitorização
O workflow corre diariamente às 07:30 UTC e também pode ser iniciado manualmente em **Actions → Monitorizar fontes MarketScope → Run workflow**. Os resultados são guardados em `monitorizacao/`, quando existem alterações.

A recolha usa resultados RSS e a interpretação é heurística, baseada apenas no título e no publicador. A monitorização de fontes conhecidas deteta alterações técnicas (por exemplo, conteúdo ou estado HTTP), não valida o significado comercial das alterações. Nenhuma candidata deve ser tratada como campanha confirmada sem verificação da fonte primária e das respetivas condições.

## Publicação
1. No repositório, abrir **Settings → Pages**.
2. Em **Build and deployment → Source**, escolher **GitHub Actions**.
3. Acompanhar o workflow de publicação no separador **Actions**.

## Limitações
O levantamento não é exaustivo e os dados podem mudar. Consultar sempre as páginas oficiais e regulamentos antes de usar a informação para decisões comerciais. Datas, valores, elegibilidade e mecânicas não confirmados devem permanecer identificados como tal.
