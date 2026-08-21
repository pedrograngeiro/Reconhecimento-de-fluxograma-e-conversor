# Amostra online para benchmark

Esta pasta contém uma amostra pequena e heterogênea para medir desempenho, não
para treinar o modelo nem para afirmar acurácia estatística.

As imagens foram obtidas em 20 de agosto de 2026. O arquivo `manifest.csv`
registra a página de origem, URL de download, autoria e licença individual. As
licenças das imagens prevalecem sobre a licença geral deste repositório.

## Casos

1. `01_decision.png`: uma única forma de decisão; controle simples/negativo.
2. `02_program_flow.png`: fluxo vertical com ramificações.
3. `03_polybool_algorithm.png`: grafo horizontal pequeno com textos.
4. `04_ebay_automation.png`: diagrama grande, colorido e com imagens embutidas.

Os dois arquivos derivados de SVG do Wikimedia têm transparência. O OpenCV atual
descarta o canal alfa ao usar `IMREAD_COLOR`, deixando áreas transparentes
pretas. Isso deve ser corrigido ou normalizado antes de usar esses casos para
medir acurácia; para tempo de processamento, as dimensões ainda são válidas.

## Uso

```powershell
rtk python -m benchmarks.benchmark_light --repeats 10
```

O benchmark fixa o OpenCV em uma thread e faz duas iterações de aquecimento antes
das medições. Portanto, os tempos representam cache aquecido e não o primeiro
acesso ao disco.
