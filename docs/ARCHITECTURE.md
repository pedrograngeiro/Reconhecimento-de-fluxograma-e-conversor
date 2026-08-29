# Arquitetura

## Objetivo

Converter pixels em uma representação semântica antes de reorganizar o visual.
Essa separação evita que erros de renderização escondam erros de reconhecimento e
permite editar ou exportar o mesmo grafo para diferentes formatos.

## Componentes

### `preprocessing.py`

Valida a entrada, lê imagens com OpenCV e rasteriza cada página PDF com PyMuPDF.
O restante do pipeline sempre recebe uma imagem BGR e o número da página.

### `detection.py`

É a única camada que conhece a API do Ultralytics. Converte cada resultado YOLO
em `Detection(label, confidence, bbox)`. Classes cujo nome contém `arrow`, além
dos aliases em português, são tratadas como pontas de seta. As demais classes são
tratadas como formas de nós.

Esse comportamento mantém compatibilidade com o modelo antigo de duas classes.
Um modelo com outras classes que não representem nós deve ajustar
`partition_detections` explicitamente.

### `ocr.py`

Recorta o interior da forma, amplia textos pequenos, aplica limiarização de Otsu e
usa Tesseract com modo de segmentação 6. A borda é removida pelo recorte interno
para interferir menos no reconhecimento.

Se o executável ou o pacote de idioma não estiver disponível, o pipeline registra
um aviso, desativa o OCR para os próximos nós e continua.

### `topology.py`

1. Converte a página para tons de cinza e detecta bordas.
2. Mascara as caixas dos nós para reduzir bordas e textos falsos.
3. Encontra segmentos com a transformada probabilística de Hough.
4. Agrupa segmentos cujas extremidades estão próximas.
5. Para cada ponta de seta, associa o nó-alvo mais próximo.
6. Percorre o componente de linhas conectado à seta e associa a outra extremidade
   ao nó de origem mais próximo.
7. Descarta associações distantes e pares duplicados.

As tolerâncias são proporcionais à diagonal da imagem quando isso é mais seguro
que um valor fixo. O algoritmo não cria arestas quando não há linha visível.

### `models.py`

Define o contrato entre as etapas e aceita os schemas legado 1.0 e atual 1.1:

- `BBox`: geometria em pixels;
- `Detection`: saída independente do detector;
- `Node` e `Edge`: semântica do fluxograma;
- `FlowchartGraph`: validação e JSON versionado.

Uma aresta nunca pode referenciar um nó ausente. IDs são determinísticos pela
ordem visual dos nós, de cima para baixo e da esquerda para a direita.

O schema 1.1 exige tipos semânticos canônicos. `bbox` e confianças são evidências
opcionais da entrada; o renderizador não as interpreta como coordenadas de saída.
Aliases do detector são normalizados antes da criação do grafo e classes
desconhecidas tornam-se `unknown`, preservando o rótulo original em `source_type`.

### `rendering.py`

Expõe a interface profunda `publish_graph(graph, options)`, que valida o grafo,
gera os artefatos auditáveis e esconde a serialização DOT e a execução do
Graphviz. Quando `dot` está disponível, gera SVG, PNG ou PDF. A forma visual é
escolhida pela classe semântica:

| Classe | Graphviz | Cor de apoio |
|---|---|---|
| `process` | retângulo arredondado | azul |
| `decision` | losango | âmbar |
| `terminator` / `start_end` | elipse | verde |
| `input_output` | paralelogramo | violeta |
| `connector` | círculo | cinza |
| `unknown` | retângulo arredondado | cinza |

SVG é a saída padrão porque preserva vetores e texto selecionável.
O [padrão visual](VISUAL_STANDARD.md) concentra cores, redação das ações e regras
de layout sem alterar o schema do grafo.

### `render_cli.py`

Lê novamente um JSON nos schemas 1.0 ou 1.1 e passa o grafo validado ao mesmo
módulo de renderização. Esse seam permite revisar texto e conexões no JSON e
republicar SVG, PDF ou PNG sem executar detector, OCR ou topologia novamente.
Também define o perfil de página (`content` ou `a4`), orientação e DPI do PNG.

### `pipeline.py` e `cli.py`

O pipeline coordena as etapas sem embutir regras específicas de YOLO ou
Tesseract. Detector e OCR podem ser injetados, o que mantém os testes rápidos e
permite substituir implementações no futuro sem alterar o formato do grafo.

## Invariantes

- A imagem original não é sobrescrita.
- JSON e DOT são gerados mesmo sem Graphviz.
- Falha opcional de OCR não cancela a detecção.
- Uma aresta só existe se origem, destino, ponta de seta e linha forem associados.
- O esquema JSON muda de versão quando houver quebra de compatibilidade.

## Onde calibrar

Antes de trocar de modelo, observe no JSON:

- `detections`: quantidade total prevista pelo YOLO;
- `arrowheads`: pontas de seta reconhecidas;
- `line_segments`: segmentos encontrados pelo OpenCV;
- `confidence` de cada nó e aresta.

Poucas detecções indicam problema no modelo ou no limiar YOLO. Nós corretos e
poucos segmentos indicam que Canny/Hough precisam de ajuste. Muitos segmentos e
arestas erradas indicam que tolerâncias de agrupamento ou associação precisam ser
calibradas.

## Extensões planejadas

Só devem ser adicionadas depois de existir um conjunto de validação ponta a
ponta:

- OCR dos rótulos de arestas;
- conectores curvos por skeletonization;
- correção de perspectiva para fotografias;
- interface humana para revisar conexões de baixa confiança;
- exportação Mermaid ou BPMN;
- avaliação por correspondência exata do grafo.
