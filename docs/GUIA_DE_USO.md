# Guia de uso

Este guia mostra o fluxo completo do projeto: preparar o ambiente, testar com
um exemplo, treinar um detector, converter imagens ou PDFs e publicar um JSON
revisado como SVG, PNG ou PDF.

## 1. O que entra e o que sai

O conversor recebe:

- uma imagem (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif` ou `.tiff`); ou
- um PDF, processado página por página.

Para reconhecer uma imagem ou PDF é necessário informar um modelo YOLO `.pt`.
O pipeline pode usar Tesseract para ler os textos e Graphviz para desenhar a
versão reorganizada do fluxograma.

Para cada página, o projeto pode produzir:

```text
output/
  exemplo.json   # grafo semântico, próprio para revisão e integração
  exemplo.dot    # fonte do diagrama Graphviz
  exemplo.svg    # saída vetorial padrão
  exemplo.png    # opcional
  exemplo.pdf    # opcional
```

O JSON e o DOT são criados mesmo quando o Graphviz não está instalado. Um PDF
de várias páginas usa nomes como `documento-page-001.json`.

## 2. Pastas: onde colocar cada arquivo

| Conteúdo | Local recomendado | Vai para o Git? |
|---|---|---|
| Imagens apenas para demonstração manual | `fluxogramas-exemplos/` | sim, quando forem próprias ou licenciadas |
| Imagens usadas no treinamento | `data/flowchart/images/<divisão>/` | não |
| Anotações YOLO dessas imagens | `data/flowchart/labels/<divisão>/` | não |
| Configuração local do dataset | `data/flowchart/data.yaml` | não |
| Pesos iniciais ou treinados (`.pt`) | local à sua escolha; exemplos usam a raiz e `runs/` | não |
| Resultados de treinamento | `runs/flowchart/` | não |
| Resultado de conversões | `output/` | não |
| JSONs pequenos de referência e regressão | `docs/examples/` | sim |

`fluxogramas-exemplos/` não é lida automaticamente pelo treinamento. Para uma
imagem participar do treino, ela precisa estar em `images/train`, `images/val`
ou `images/test` e possuir uma anotação YOLO de mesmo nome na pasta `labels`
correspondente.

Exemplo:

```text
data/flowchart/
  images/train/compra-001.png
  labels/train/compra-001.txt
```

Não versione datasets, pesos, PDFs privados ou saídas geradas. Essas pastas e
os arquivos `.pt` já são ignorados pelo `.gitignore`.

## 3. Instalação

Requisitos:

- Python 3.10 ou superior;
- Graphviz, para gerar SVG, PNG e PDF;
- Tesseract e o idioma `por`, para OCR em português;
- uma GPU compatível é opcional, mas acelera o treinamento.

No PowerShell, a partir da raiz do projeto:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[full,dev]"
```

No Linux ou macOS, somente a ativação muda:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[full,dev]"
```

As opções de instalação são:

| Extra | Instala | Quando usar |
|---|---|---|
| `ml` | Ultralytics/YOLO | treinamento e reconhecimento |
| `ocr` | integração Python com Tesseract | leitura dos textos |
| `pdf` | PyMuPDF | entrada em PDF |
| `dev` | pytest | desenvolvimento e testes |
| `full` | `ml`, `ocr` e `pdf` | uso completo |

Tesseract e Graphviz são programas do sistema. Os pacotes Python não instalam
os executáveis. Verifique se eles estão disponíveis:

```powershell
tesseract --version
dot -V
```

No Windows, quando o Tesseract não estiver no `PATH`, use por exemplo:

```powershell
--tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## 4. Primeiro teste

Antes de treinar, é possível validar a geração visual usando o JSON versionado
que já acompanha o projeto. Esse comando não precisa de YOLO nem Tesseract:

```powershell
flowchart-render docs\examples\standard-flow.json `
  --output-dir output\primeiro-teste `
  --format svg `
  --format png `
  --format pdf `
  --page-size a4 `
  --dpi 300
```

Se os comandos instalados pelo pacote não estiverem disponíveis, use:

```powershell
python -m flowchart_converter.render_cli docs\examples\standard-flow.json `
  --output-dir output\primeiro-teste
```

Confira os arquivos em `output/primeiro-teste/`. Sem Graphviz, o comando ainda
grava JSON e DOT e apresenta um aviso sobre os formatos não renderizados.

## 5. Converter uma imagem

Depois de obter `best.pt` pelo treinamento:

```powershell
flowchart-converter fluxogramas-exemplos\original-aprovacao-compra.png `
  --model runs\flowchart\detector\weights\best.pt `
  --output-dir output\aprovacao `
  --format svg `
  --format png
```

Sem o comando instalado:

```powershell
python -m flowchart_converter fluxogramas-exemplos\original-aprovacao-compra.png `
  --model runs\flowchart\detector\weights\best.pt `
  --output-dir output\aprovacao
```

O resultado depende de o modelo ter sido treinado com imagens visualmente
parecidas com a entrada. Os exemplos do repositório são casos de demonstração,
não uma garantia de qualidade para um modelo treinado apenas com dados
sintéticos.

## 6. Converter um PDF

```powershell
flowchart-converter documento.pdf `
  --model runs\flowchart\detector\weights\best.pt `
  --output-dir output\documento `
  --dpi 250 `
  --format svg `
  --format pdf
```

`--dpi` controla a rasterização da entrada PDF. Em geral, 200 a 300 DPI é um
bom intervalo. Valores maiores consomem mais memória e não corrigem uma imagem
original de baixa qualidade.

Para somente extrair as páginas antes de anotá-las:

```powershell
python convert_pdf_to_img.py documento.pdf --output-dir pages --dpi 250
```

## 7. Revisar o JSON e publicar novamente

O reconhecimento e a apresentação são etapas separadas. É possível corrigir
textos, tipos de nós e conexões no JSON e depois gerar novamente os formatos
visuais sem executar YOLO ou OCR:

```powershell
flowchart-render output\aprovacao\original-aprovacao-compra.json `
  --output-dir output\aprovacao-revisada `
  --name aprovacao-final `
  --format svg `
  --format png `
  --format pdf `
  --rankdir TB `
  --page-size a4 `
  --orientation portrait `
  --dpi 300
```

O comando não permite sobrescrever o JSON de origem. Use outro diretório de
saída ou outro `--name`. O contrato aceito está em
[`schemas/flowchart-1.1.schema.json`](../schemas/flowchart-1.1.schema.json).

## 8. Configuração do conversor

| Opção | Padrão | Efeito |
|---|---:|---|
| `--model` | obrigatório | caminho para os pesos YOLO `.pt` |
| `--output-dir` | `output` | diretório dos artefatos |
| `--confidence` | `0.25` | confiança mínima das detecções |
| `--dpi` | `200` | DPI usado para rasterizar PDFs de entrada |
| `--no-ocr` | desligado | pula a leitura de texto |
| `--ocr-lang` | `por` | idioma instalado no Tesseract |
| `--tesseract-cmd` | `PATH` do sistema | caminho explícito do Tesseract |
| `--format` | `svg` | formato visual; repita para gerar vários |
| `--rankdir` | `TB` | fluxo: `TB`, `BT`, `LR` ou `RL` |
| `--page-size` | `content` | ajusta ao conteúdo ou limita a `a4` |
| `--orientation` | `portrait` | `portrait` ou `landscape` |
| `--output-dpi` | `300` | resolução da saída PNG |

No `flowchart-render`, a opção de resolução chama-se `--dpi`; no
`flowchart-converter`, chama-se `--output-dpi` para diferenciá-la do DPI da
entrada PDF.

Orientações usuais:

- use `TB` para fluxos de cima para baixo e `LR` para fluxos horizontais;
- mantenha `content` para diagramas digitais e use `a4` para impressão;
- reduza `--confidence` apenas depois de examinar falsos positivos no JSON;
- use `--no-ocr` para diagnosticar apenas detecção e topologia.

## 9. Treinamento resumido

Para experimentar o pipeline sem dados próprios:

```powershell
python scripts\generate_synthetic_dataset.py --output flow-chart
python treinar.py `
  --data flow-chart\data.yaml `
  --model yolov8n.pt `
  --epochs 100 `
  --batch 8 `
  --device cpu
```

O melhor checkpoint normalmente ficará em:

```text
runs/flowchart/detector/weights/best.pt
```

O nome exato do diretório é mostrado pelo Ultralytics e pode ganhar um sufixo
quando já existe uma execução com o mesmo nome. Para montar um dataset real,
anotar as classes e escolher os parâmetros, siga o
[`Guia de dataset e treinamento`](DATASET.md).

## 10. Diagnóstico rápido

### O comando não é reconhecido

Ative o ambiente virtual e repita `python -m pip install -e ".[full,dev]"`.
Como alternativa, use `python -m flowchart_converter` ou
`python -m flowchart_converter.render_cli`.

### O modelo `.pt` não foi encontrado

Confirme o caminho exibido ao fim do treino. Use `best.pt` para inferência e
`last.pt` apenas para retomar o estado de um treino interrompido.

### Os textos ficaram vazios

Confirme `tesseract --version`, a instalação do idioma `por` e o caminho passado
em `--tesseract-cmd`. Para outro idioma, informe seu código em `--ocr-lang`.

### Só foram gerados JSON e DOT

Instale o Graphviz e confirme `dot -V`. O executável `dot` precisa estar no
`PATH` do processo.

### Há nós corretos, mas faltam conexões

Verifique no JSON os campos `arrowheads` e `line_segments` em `metadata`. O
detector precisa reconhecer as pontas e o OpenCV precisa encontrar as linhas.
Conectores curvos, cruzados ou apagados ainda são limitações conhecidas.

### O treinamento ficou sem memória

Reduza `--batch` e, se necessário, `--imgsz`. Em CPU ou Windows, mantenha
`--workers 0` como ponto de partida.

## 11. Verificação do projeto

Execute a suíte antes de publicar alterações:

```powershell
python -m pytest
```

Os testes do núcleo não exigem pesos YOLO, Tesseract ou Graphviz.
