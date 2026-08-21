# Resultado preliminar

Medição executada em 20 de agosto de 2026 com OpenCV 4.13.0, uma thread, duas
iterações de aquecimento e dez repetições por imagem.

| Imagem | Resolução | MP | Segmentos | Mediana total | p95 total |
|---|---:|---:|---:|---:|---:|
| `01_decision.png` | 960 × 720 | 0,6912 | 12 | 8,525 ms | 10,054 ms |
| `02_program_flow.png` | 960 × 1.358 | 1,3037 | 179 | 24,005 ms | 24,752 ms |
| `03_polybool_algorithm.png` | 676 × 204 | 0,1379 | 154 | 4,833 ms | 5,521 ms |
| `04_ebay_automation.png` | 1.516 × 1.181 | 1,7904 | 850 | 44,145 ms | 50,373 ms |

A soma das medianas é 81,508 ms para as quatro imagens. Esse número cobre apenas
leitura e detecção de segmentos em cache aquecido. O comando completo levou mais
tempo porque fez aquecimento e 10 repetições de cada etapa.

Os números de segmentos não representam conexões corretas: sem as caixas do YOLO,
as formas e os textos não foram mascarados antes de Hough. Eles são registrados
somente para caracterizar a carga computacional desta medição.

## Etapas indisponíveis

| Etapa | Motivo |
|---|---|
| YOLO | Ultralytics e pesos treinados ausentes |
| OCR | executável Tesseract ausente |
| PDF | PyMuPDF ausente |
| SVG/PNG final | executável Graphviz ausente |

Por isso, 81,508 ms é um limite inferior, não o tempo ponta a ponta. Para um dado
defensável no artigo, a próxima medição deve usar o `best.pt` real, lote 1,
`device=cpu`, OCR configurado e as mesmas quatro imagens.
