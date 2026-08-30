# Dataset, treinamento e avaliação

Este documento explica como preparar e treinar o detector YOLO. Para instalar o
projeto, converter arquivos e renderizar JSON, consulte o
[Guia de uso](GUIA_DE_USO.md).

## Taxonomia recomendada

Use classes distintas quando a forma tiver significado diferente no fluxograma:

| Classe | Uso |
|---|---|
| `process` | ação ou etapa retangular |
| `decision` | decisão em losango |
| `terminator` | início ou fim |
| `input_output` | entrada ou saída |
| `connector` | conector circular |
| `arrow_head` | somente a ponta que determina direção |

Para um primeiro baseline, `node` e `arrow_head` ainda funcionam. Nesse caso, o
renderizador não consegue preservar a forma original e desenha todos os nós como
processos.

## Estrutura YOLO

```text
data/flowchart/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
```

O arquivo [data.example.yaml](../configs/data.example.yaml) contém a configuração
de referência.

Cada imagem precisa de um arquivo `.txt` com o mesmo nome e na divisão
correspondente:

```text
data/flowchart/images/train/fluxo-001.png
data/flowchart/labels/train/fluxo-001.txt
```

Uma linha da anotação YOLO tem cinco valores separados por espaços:

```text
<classe> <x_centro> <y_centro> <largura> <altura>
```

As quatro coordenadas são normalizadas entre `0` e `1`. A classe usa o índice
definido em `data.yaml`; por exemplo, `1` representa `decision` na taxonomia
recomendada. Arquivos sem objetos podem ser vazios, desde que essa escolha seja
compatível com a ferramenta de anotação e aplicada de forma consistente.

## Onde colocar exemplos

Há dois tipos de exemplo no projeto:

- `fluxogramas-exemplos/`: imagens próprias ou licenciadas para demonstração,
  inspeção visual e teste manual do conversor;
- `data/flowchart/`: imagens efetivamente anotadas e usadas pelo YOLO.

Copiar uma imagem apenas para `fluxogramas-exemplos/` não a inclui no treino.
Para treiná-la, distribua-a em `train`, `val` ou `test` e exporte sua anotação
YOLO para a pasta `labels` equivalente. Evite usar o mesmo documento, ou páginas
do mesmo documento, em divisões diferentes.

O diretório `docs/examples/` tem JSONs pequenos e resultados esperados para
documentação e regressão. Ele também não é um dataset do YOLO.

## Configurar `data.yaml`

Uma configuração local simples, salva como `data/flowchart/data.yaml` e usada
com o treino iniciado na raiz do projeto, é:

```yaml
path: data/flowchart
train: images/train
val: images/val
test: images/test

names:
  0: process
  1: decision
  2: terminator
  3: input_output
  4: connector
  5: arrow_head
```

O `path` é a raiz do dataset; `train`, `val` e `test` são resolvidos a partir
dele. O Ultralytics pode resolver um `path` relativo usando o diretório de
execução ou sua configuração global de datasets. Por isso, execute `treinar.py`
na raiz do projeto ou use um caminho absoluto. Os geradores deste repositório
gravam um caminho absoluto automaticamente. Consulte também o
[formato oficial de datasets de detecção do Ultralytics](https://docs.ultralytics.com/datasets/detect/).

Os nomes, índices e anotações devem corresponder exatamente; trocar a ordem
depois de anotar muda o significado do dataset.

## Regras de anotação

- A caixa da forma deve incluir sua borda completa, mas não o conector externo.
- A caixa da ponta de seta deve ser justa e não incluir a linha inteira.
- Texto não é uma classe: ele será lido pelo OCR dentro da forma.
- Formas parcialmente visíveis devem seguir uma regra única em todo o dataset.
- Objetos ambíguos devem ser revisados, não classificados por adivinhação.

Mantenha um pequeno guia visual de exemplos válidos e inválidos para cada classe.
Consistência de anotação costuma ter mais impacto que simplesmente aumentar o
número de imagens.

## Divisão dos dados

Separe treino, validação e teste por documento ou origem, nunca distribuindo
páginas do mesmo PDF aleatoriamente entre os conjuntos. Isso evita vazamento de
layout, fonte e estilo visual.

Uma divisão inicial razoável é 70%/15%/15%, ajustada ao volume disponível. O teste
deve permanecer congelado durante a calibração.

Inclua diversidade que represente a entrada real:

- exportações digitais e capturas de tela;
- resoluções e proporções diferentes;
- compressão, desfoque e contraste moderados;
- pequenas rotações e mudanças de escala;
- fotografias e manuscritos apenas se forem parte do objetivo do produto.

Não aplique aumentos que mudem a semântica ou tornem o exemplo irreal.

## Treinamento reproduzível

O script fixa `seed=42` e solicita execução determinística. Registre para cada
experimento:

- commit do código;
- versão do dataset;
- pesos iniciais;
- parâmetros usados;
- métricas e matriz de confusão;
- caminho do `best.pt` resultante.

Para um teste inicial do pipeline, sem substituir a coleta de exemplos reais,
gere o pequeno conjunto sintético local:

```powershell
python scripts/generate_synthetic_dataset.py
```

O comando cria 72 imagens de treino, 18 de validação e 18 de teste em
`flow-chart/`, que é ignorado pelo Git. As métricas desse conjunto medem apenas
a capacidade de aprender os desenhos gerados; não representam desempenho em
fluxogramas reais.

Há também um gerador com páginas verticais mais densas, ramificações laterais e
estilo de documento:

```powershell
python scripts/generate_document_flowcharts.py --output flow-chart-document
```

Use os geradores para validar a instalação, criar um baseline ou complementar
um conjunto real. Não use métricas sintéticas como estimativa de desempenho em
documentos reais.

Treino novo:

```powershell
python treinar.py --data flow-chart/data.yaml --model yolov8n.pt --epochs 100
```

Exemplo completo com destino e nome explícitos:

```powershell
python treinar.py `
  --data data\flowchart\data.yaml `
  --model yolov8n.pt `
  --epochs 100 `
  --imgsz 640 `
  --batch 8 `
  --workers 0 `
  --device cpu `
  --project runs\flowchart `
  --name detector `
  --seed 42
```

| Opção | Padrão | Uso |
|---|---:|---|
| `--data` | `flow-chart/data.yaml` | configuração e classes do dataset |
| `--model` | `yolov8n.pt` | pesos-base ou checkpoint `last.pt` |
| `--epochs` | `100` | número máximo de épocas |
| `--imgsz` | `640` | dimensão usada pelo modelo |
| `--batch` | `8` | imagens por lote |
| `--workers` | `0` | processos de carregamento dos dados |
| `--device` | `cpu` | `cpu`, índice de GPU como `0`, ou opção aceita pelo Ultralytics |
| `--project` | `runs/flowchart` | raiz dos resultados |
| `--name` | `detector` | nome do experimento |
| `--seed` | `42` | semente para reprodução |
| `--resume` | desligado | retoma o estado completo do checkpoint |

Retomada preservando o estado do otimizador e a época:

```powershell
python treinar.py `
  --data flow-chart/data.yaml `
  --model runs/flowchart/detector/weights/last.pt `
  --resume
```

Não use `best.pt` com `--resume`: a retomada deve apontar para `last.pt`, que
mantém o estado necessário do otimizador e da época. Para iniciar outro ajuste a
partir de pesos já treinados, informe os pesos em `--model` sem `--resume`.

Ao final, procure:

```text
runs/flowchart/detector/
  weights/best.pt
  weights/last.pt
  results.csv
  results.png
  confusion_matrix.png
```

O Ultralytics pode criar `detector2`, `detector3` e assim por diante quando o
nome já existe. O terminal informa o diretório realmente utilizado.

Reduza `--batch` quando houver falta de memória. Aumentar `workers` melhora a
leitura de dados em máquinas adequadas, mas `0` é o padrão conservador para WSL e
ambientes limitados.

## Checklist antes do treino

- todas as imagens abrem e têm a anotação correspondente;
- os índices dos `.txt` existem em `names`;
- caixas estão normalizadas e dentro do intervalo `0..1`;
- nenhuma página ou origem aparece em mais de uma divisão;
- cada classe possui exemplos suficientes e variados;
- `data.yaml` aponta para as pastas corretas;
- o commit, a versão do dataset e os parâmetros foram registrados.

Faça primeiro uma execução curta, por exemplo com 2 ou 3 épocas, para detectar
erros de caminho e anotação antes de iniciar um treinamento longo.

## Métricas

Não avalie o sistema apenas pelo mAP do YOLO. Meça separadamente:

| Etapa | Métrica |
|---|---|
| formas e pontas | precisão, recall e mAP por classe |
| OCR | CER e WER |
| conexões | precisão, recall e F1 de pares origem/destino |
| ponta a ponta | nós, textos e arestas corretos por diagrama |

Um detector com mAP alto ainda pode gerar um grafo incorreto se perder uma única
ponta de seta. Por isso, mantenha arquivos JSON esperados para um conjunto pequeno
de diagramas representativos e compare-os automaticamente nas próximas versões.
