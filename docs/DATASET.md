# Dataset, treinamento e avaliação

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

Treino novo:

```powershell
python treinar.py --data flow-chart/data.yaml --model yolov8n.pt --epochs 100
```

Retomada preservando o estado do otimizador e a época:

```powershell
python treinar.py `
  --data flow-chart/data.yaml `
  --model runs/flowchart/detector/weights/last.pt `
  --resume
```

Reduza `--batch` quando houver falta de memória. Aumentar `workers` melhora a
leitura de dados em máquinas adequadas, mas `0` é o padrão conservador para WSL e
ambientes limitados.

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
