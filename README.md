# Reconhecimento e conversão de fluxogramas

Este projeto recebe uma imagem ou um PDF de fluxograma, reconhece suas formas com
YOLO, lê o texto com OCR, infere conexões a partir das linhas e pontas de seta e
reconstrói o resultado como um grafo visualmente organizado.

O resultado não é apenas uma imagem anotada. Para cada página são gerados:

- um JSON auditável com nós, textos, caixas, conexões e confianças;
- um arquivo DOT editável;
- SVG, PNG ou PDF reorganizado pelo Graphviz, quando ele está instalado.

## Estado do projeto

Esta é a primeira versão funcional do conversor. O pipeline e suas regras
geométricas têm testes automatizados, mas a qualidade final ainda depende dos
pesos YOLO e do dataset, que não fazem parte do repositório.

O modelo antigo com classes `node` e `arrow_head` continua compatível. Para que o
novo desenho preserve formas diferentes, recomenda-se treinar as classes
`process`, `decision`, `terminator`, `input_output`, `connector` e `arrow_head`.
O pipeline publica os cinco primeiros como símbolos canônicos; `arrow_head` serve
somente para inferir arestas. Classes inesperadas tornam-se `unknown` para revisão.

## Como funciona

```text
imagem/PDF
    │
    ├─ YOLO ───────────────► formas e pontas de seta
    ├─ Tesseract ──────────► texto no interior das formas
    └─ OpenCV/HoughLinesP ─► segmentos dos conectores
                                  │
                                  ▼
                       associação geométrica
                                  │
                                  ▼
                         grafo JSON + DOT
                                  │
                                  ▼
                       Graphviz SVG/PNG/PDF
```

Detalhes e decisões estão em [Arquitetura](docs/ARCHITECTURE.md). As orientações
de anotação e treinamento estão em [Dataset e avaliação](docs/DATASET.md). A
aparência das saídas segue o [Padrão visual](docs/VISUAL_STANDARD.md).

## Documentação

| Quero... | Consulte |
|---|---|
| instalar, fazer o primeiro teste e converter imagem ou PDF | [Guia de uso](docs/GUIA_DE_USO.md) |
| saber onde colocar exemplos, imagens e anotações | [Guia de uso — Pastas](docs/GUIA_DE_USO.md#2-pastas-onde-colocar-cada-arquivo) |
| criar um dataset e treinar ou retomar o YOLO | [Dataset, treinamento e avaliação](docs/DATASET.md) |
| entender o JSON, os módulos e o pipeline | [Arquitetura](docs/ARCHITECTURE.md) |
| conhecer formas, cores e regras da saída | [Padrão visual](docs/VISUAL_STANDARD.md) |

Se esta é a primeira execução, comece pelo
[`flowchart-render` com o JSON incluído no projeto](docs/GUIA_DE_USO.md#4-primeiro-teste).

## Exemplos originais

O diretório [`fluxogramas-exemplos`](fluxogramas-exemplos/) contém quatro
diagramas originais criados para demonstração e avaliação manual do projeto:

- [atendimento de suporte](fluxogramas-exemplos/original-atendimento-suporte.png);
- [aprovação de compra](fluxogramas-exemplos/original-aprovacao-compra.png);
- [rotina de estudos](fluxogramas-exemplos/original-rotina-estudos.png);
- [publicação de conteúdo](fluxogramas-exemplos/original-publicacao-conteudo.png).

A proveniência e o propósito de cada imagem estão documentados no
[README dos exemplos](fluxogramas-exemplos/README.md).

## Requisitos

- Python 3.10 ou superior;
- pesos YOLO treinados (`best.pt`);
- Tesseract com o idioma português para OCR;
- Graphviz para renderizar DOT como SVG, PNG ou PDF.

Tesseract e Graphviz são programas do sistema, não apenas pacotes Python.
Confirme a instalação com:

```powershell
tesseract --version
dot -V
```

Sem Tesseract, o conversor continua e deixa os textos vazios. Sem Graphviz, ele
continua gerando JSON e DOT.

## Instalação

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[full,dev]"
```

As dependências são separadas para instalações menores:

```powershell
python -m pip install -e ".[ml]"   # YOLO
python -m pip install -e ".[ocr]"  # integração com Tesseract
python -m pip install -e ".[pdf]"  # leitura de PDF
```

## Uso rápido

```powershell
flowchart-converter pagina_1.png `
  --model "modelo treinado/best.pt" `
  --output-dir output
```

Também é possível executar sem instalar o comando:

```powershell
python -m flowchart_converter pagina_1.png --model "modelo treinado/best.pt"
```

Para PDF e mais de um formato de saída:

```powershell
flowchart-converter documento.pdf `
  --model "modelo treinado/best.pt" `
  --format svg `
  --format png `
  --dpi 250
```

Opções importantes:

| Opção | Função |
|---|---|
| `--confidence 0.25` | confiança mínima do YOLO |
| `--no-ocr` | desativa o OCR |
| `--ocr-lang por` | idioma instalado no Tesseract |
| `--tesseract-cmd CAMINHO` | informa o executável quando não está no `PATH` |
| `--rankdir TB` | direção do novo layout: `TB`, `BT`, `LR` ou `RL` |
| `--format svg` | formato visual; pode ser repetido |
| `--page-size content` | página ajustada ao conteúdo ou limitada a `a4` |
| `--orientation portrait` | orientação `portrait` ou `landscape` |
| `--output-dpi 300` | resolução da saída PNG |

Os atalhos legados `python fluxo.py` e `python testar.py` aceitam os mesmos
argumentos.

## Saídas

Uma imagem `triagem.png` produz, por padrão:

```text
output/
  triagem.json
  triagem.dot
  triagem.svg
```

Um PDF produz um conjunto por página, como
`documento-page-001.json` e `documento-page-001.svg`.

Um JSON revisado pode ser renderizado novamente sem executar detecção ou OCR:

```powershell
flowchart-render output\triagem.json `
  --output-dir output\padronizado `
  --format svg `
  --format pdf `
  --format png `
  --page-size a4 `
  --dpi 300
```

O JSON segue este formato versionado:

```json
{
  "schema_version": "1.1",
  "nodes": [
    {
      "id": "n1",
      "type": "decision",
      "text": "Está aprovado?",
      "bbox": [100, 200, 310, 290],
      "confidence": 0.94
    },
    {
      "id": "n2",
      "type": "terminator",
      "text": "Fim"
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "n1",
      "target": "n2",
      "confidence": 0.81,
      "label": "Sim",
      "branch": "yes"
    }
  ],
  "metadata": {}
}
```

No schema 1.1, `bbox` e confianças são opcionais porque registram a evidência do
reconhecimento, não o layout publicado. JSONs 1.0 continuam aceitos. Consulte o
[contrato formal](schemas/flowchart-1.1.schema.json).

## Treinamento

Use [configs/data.example.yaml](configs/data.example.yaml) como ponto de partida.

Treino novo, com parâmetros conservadores para CPU e pouca memória:

```powershell
python treinar.py `
  --data flow-chart/data.yaml `
  --model yolov8n.pt `
  --epochs 100 `
  --batch 8 `
  --device cpu
```

Retomada real de um treinamento interrompido:

```powershell
python treinar.py `
  --data flow-chart/data.yaml `
  --model runs/flowchart/detector/weights/last.pt `
  --resume
```

Para extrair páginas de um PDF antes de anotá-las:

```powershell
python convert_pdf_to_img.py documento.pdf --output-dir pages --dpi 250
```

## Testes

```powershell
python -m pytest
```

Os testes do núcleo não precisam dos pesos YOLO, do Tesseract nem do executável
Graphviz. Eles verificam o esquema JSON, a separação das classes, a reconstrução
de uma conexão, a geração DOT e a orquestração do pipeline.

## Limitações conhecidas

- Conectores curvos, cruzados ou muito apagados podem não ser associados.
- A direção depende da detecção da ponta da seta.
- Rótulos `Sim`/`Não` nas arestas ainda não são extraídos.
- Diagramas manuscritos e fotos com perspectiva exigem dataset e
  pré-processamento próprios.
- Quando a imagem é ambígua, o sistema prefere omitir uma aresta a inventar uma
  conexão.

O próximo avanço recomendado é criar um conjunto de validação ponta a ponta com
grafos esperados e medir precisão/recall das conexões, além do mAP do detector.

## Licenciamento

O código original deste repositório é distribuído sob a licença MIT. As imagens
de benchmark mantêm suas licenças individuais, documentadas em
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

As dependências opcionais de detecção e PDF não são relicenciadas pela MIT deste
projeto. Consulte [Licenciamento das dependências](docs/LICENSING.md) antes de
distribuir ou operar o pipeline completo, especialmente em produto comercial ou
de código fechado.
