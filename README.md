# MarketScope — Campanhas de Pneus Portugal

Dashboard interativo de monitorização de campanhas promocionais de pneus ligeiros em Portugal.

## Conteúdo
- `index.html`: interface do dashboard.
- `campanhas.csv`: base de dados inicial dos registos incluídos.
- `.github/workflows/pages.yml`: publicação do site através do GitHub Pages.

## Publicação
1. No repositório, abrir **Settings → Pages**.
2. Em **Build and deployment → Source**, escolher **GitHub Actions**.
3. Abrir o separador **Actions** e acompanhar o workflow **Deploy MarketScope to GitHub Pages**. Também é possível executá-lo manualmente através de **Run workflow**.
4. Após conclusão com sucesso, o URL do site será apresentado no deployment. Para um repositório de projeto, o endereço normalmente segue o padrão `https://<utilizador>.github.io/<nome-do-repositorio>/`.

## Atualização dos dados
O dashboard inclui dados de um levantamento inicial, com referência indicada na interface. Para atualizar a informação é necessário alterar `index.html` e/ou `campanhas.csv` e enviar um commit para `main`; o workflow publica as alterações automaticamente. A recolha automática das páginas externas e a sincronização do CSV com a interface não estão implementadas neste momento.

## Limitações
As campanhas registadas não constituem um inventário exaustivo. Consultar sempre as páginas oficiais e regulamentos ligados nos cartões antes de tomar decisões comerciais. Campos não confirmados devem permanecer identificados como tal.
