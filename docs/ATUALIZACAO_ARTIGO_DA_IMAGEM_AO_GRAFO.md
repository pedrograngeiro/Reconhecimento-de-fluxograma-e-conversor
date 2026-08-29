# Atualização do artigo: da imagem ao grafo editável

> Documento de apoio para atualizar o artigo
> [“Da imagem ao grafo editável”](https://pedrograngeiro.github.io/blog/da-imagem-ao-grafo-editavel/).
> Evidências verificadas em 29 de agosto de 2026.

## Como incorporar esta atualização

O artigo publicado em 20 de agosto de 2026 descreve corretamente a arquitetura,
mas termina com três ressalvas que o novo experimento permite atualizar:

- ainda não havia um detector treinado para o estilo da imagem usada como exemplo;
- o Tesseract não estava disponível na máquina da primeira execução;
- o estudo de caso era controlado por testes, sem uma conversão empírica ponta a
  ponta.

Essas ressalvas não devem simplesmente ser apagadas. Elas formam o “antes” do
experimento. A atualização mais transparente é acrescentar uma seção depois do
estudo de caso atual e ajustar as seções de avaliação, limitações e conclusão com
os resultados abaixo.

## Resumo do que mudou

O primeiro checkpoint, ajustado com 72 imagens sintéticas simples e acompanhado
por 18 imagens de validação a 384 pixels, não generalizou para o fluxograma
documental escolhido. Com confiança mínima de
0,25, ele retornou zero nós e zero conexões. Reduzir a confiança para 0,05 revelou
apenas um losango, com confiança 0,07168 e texto vazio. Isso mostrou que o JSON
vazio não era um problema de serialização: o detector não estava entregando as
regiões que alimentam OCR e reconstrução topológica.

O novo experimento atacou duas causas separadamente:

1. o detector foi ajustado com um dataset sintético mais próximo do domínio
   visual do documento;
2. o OCR ganhou uma instalação real do Tesseract e pré-processamento específico
   para texto dentro de formas.

No diagrama usado como caso de aceitação, o novo pipeline recuperou os 14 nós,
preencheu os 14 textos e reconstruiu 14 das 15 conexões visíveis. Doze textos
ficaram literalmente corretos; os dois restantes continuaram compreensíveis,
mas apresentaram erros de espaço ou pontuação.

| Evidência no mesmo fluxograma | Baseline | `document-v2` |
|---|---:|---:|
| nós detectados, `confidence=0.25` | 0/14 | 14/14 |
| tipos de nó corretos por inspeção manual | 0/14 | 14/14 |
| textos não vazios | 0/14 | 14/14 |
| textos literalmente corretos | 0/14 | 12/14 |
| conexões corretas recuperadas | 0/15 | 14/15 |
| conexões espúrias | 0 | 0 |

O [JSON do baseline](../output/article-baseline-conf025/Capturar_2016_12_23_14_15_52_123.json)
e o [JSON do novo pipeline](../output/document-v2-final/Capturar_2016_12_23_14_15_52_123.json)
são os artefatos primários dessa comparação no ambiente local. Como `output/` é
ignorado pelo Git, eles precisam ser publicados como artefatos do post ou movidos
para uma área versionada antes de serem referenciados pelo site.

## Diagnóstico: treinar o YOLO não ensina o modelo a ler

Uma escolha conceitual importante foi manter as responsabilidades separadas. O
YOLO não reconhece as palavras; ele localiza `process`, `decision`, `terminator`,
`input_output`, `connector` e `arrow_head`. O texto continua sendo responsabilidade
do Tesseract, aplicado ao recorte de cada forma.

Isso explica por que “treinar melhor para identificar os textos” exigiu duas
mudanças, não uma:

- melhores caixas aumentaram a chance de o OCR receber o recorte correto;
- instalar e calibrar o mecanismo de OCR transformou esses recortes em texto.

Na primeira máquina, o pacote Python `pytesseract` existia, mas o executável do
Tesseract não. São componentes diferentes. O experimento final usou Tesseract
5.5.3, com os idiomas `por` e `eng`, apontado explicitamente por
`--tesseract-cmd` porque o instalador não o adicionou ao `PATH`. A versão consta
nas [notas oficiais do Tesseract](https://github.com/tesseract-ocr/tessdoc/blob/main/ReleaseNotes.md#v553).

## Dataset direcionado ao domínio

O baseline original foi treinado por oito épocas, com `imgsz=384`, sobre o
primeiro conjunto sintético. No fim da oitava época, a validação interna chegou a
mAP50 de 0,59265 e mAP50–95 de 0,49216, mas a inferência real permaneceu vazia.
Esse contraste é evidência de lacuna de domínio: bons números no gerador original
não garantiram desempenho no estilo documental.

Em vez de baixar imagens sem uma licença de reutilização explicitamente
verificável, foi criado o gerador
[`scripts/generate_document_flowcharts.py`](../scripts/generate_document_flowcharts.py).
Ele produz páginas de 640 × 960 pixels com:

- fundo branco, formas cinza e contornos finos;
- texto curto em português;
- terminadores, processos, decisões, entrada/saída e conectores;
- ramificações laterais e pontas de seta anotadas;
- pequenas variações de posição, tom, espessura e ruído.

O conjunto `flow-chart-document/` contém 224 imagens: 160 de treino, 32 de
validação e 32 de teste. As 6.496 anotações estão distribuídas assim:

| Classe | Objetos |
|---|---:|
| `process` | 1.707 |
| `decision` | 448 |
| `terminator` | 448 |
| `input_output` | 387 |
| `connector` | 146 |
| `arrow_head` | 3.360 |

O fluxograma externo usado nesse experimento não foi incluído no treino e não é
redistribuído neste repositório porque sua licença não pôde ser comprovada. Ele
foi usado como caso de aceitação durante o desenvolvimento. Por ter influenciado
a decisão de interromper o treinamento, não deve ser chamado de “teste cego”. As
32 imagens do diretório `test` é que permaneceram fora do ajuste dos pesos. Os
exemplos originais atualmente versionados foram produzidos depois desse ensaio e
não são a fonte das métricas desta seção.

Também foram incorporadas duas imagens com licença clara apenas ao benchmark de
referência, não ao treinamento: uma imagem
[CC0](https://commons.wikimedia.org/wiki/File:FlowChart.svg) e outra em
[domínio público](https://commons.wikimedia.org/wiki/File:Flowchart_for_a_999_emergency_call.svg).
A origem e as licenças estão no
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) e no
[`manifest.csv`](../benchmarks/online_samples/manifest.csv). Essa separação evita
misturar material de avaliação com dados de treino e mantém a procedência
auditável.

## Treinamento e critério de parada

O ajuste partiu do melhor checkpoint do baseline, em vez de reiniciar de pesos
genéricos. A resolução subiu de 384 para 640 pixels para preservar detalhes de
formas e pontas de seta. A documentação oficial do
[modo de treinamento do Ultralytics](https://docs.ultralytics.com/modes/train)
descreve `imgsz`, `batch`, `device`, transferência de pesos e checkpoints usados
nessa configuração.

O comando configurou 50 épocas, lote 8, CPU, zero workers e semente 42:

```powershell
.\.venv\Scripts\python.exe treinar.py `
  --data flow-chart-document\data.yaml `
  --model runs\flowchart\synthetic-baseline\weights\best.pt `
  --epochs 50 `
  --imgsz 640 `
  --batch 8 `
  --workers 0 `
  --device cpu `
  --name document-v2
```

O processo foi interrompido manualmente depois da sexta época, quando o caso de
aceitação já recuperava os objetos esperados e a validação sintética havia
estabilizado em nível alto. Não foi o `early stopping` automático do Ultralytics.
Registrar isso evita sugerir que as 50 épocas foram concluídas.

| Época | Precisão | Recall | mAP50 | mAP50–95 |
|---:|---:|---:|---:|---:|
| 1 | 0,96471 | 0,49836 | 0,58049 | 0,48469 |
| 2 | 0,82075 | 0,77821 | 0,85227 | 0,65297 |
| 3 | 0,90325 | 0,97972 | 0,98717 | 0,80976 |
| 4 | 0,98810 | 0,98819 | 0,99296 | 0,80492 |
| 5 | 0,98233 | 0,98873 | 0,99323 | 0,79946 |
| 6 | 0,98968 | 0,99369 | 0,99381 | 0,85706 |

Os números vêm de
[`runs/flowchart/document-v2/results.csv`](../runs/flowchart/document-v2/results.csv),
um diretório local ignorado pelo Git. Uma avaliação separada do `best.pt` nas 32
imagens sintéticas de teste obteve precisão 0,99253, recall 0,99506, mAP50
0,99449 e mAP50–95 0,85517. Esses resultados medem apenas imagens geradas pela
mesma família de regras; não são uma estimativa de desempenho em fluxogramas
arbitrários.

O checkpoint final tem 24.468.903 bytes e SHA-256
`e2c563cfd0277e347d59b9d39043c1c3b9e4793665503d0571c565b98668f394`.
Ele está localmente em `runs/flowchart/document-v2/weights/best.pt`. Como `runs/`
e `*.pt` são ignorados, o artigo não deve afirmar que os pesos estão versionados
no repositório até que exista um release ou outro armazenamento permanente com
esse checksum.

## Ajustes do OCR

O OCR localizado já era a estratégia correta, mas o recorte ainda continha muito
da borda das formas. Em losangos, o Tesseract podia interpretar os traços como
pontuação. O adaptador [`flowchart_converter/ocr.py`](../flowchart_converter/ocr.py)
passou a:

- recuar 15% nas laterais e 18% na vertical antes de ler;
- ampliar recortes pequenos até 128 pixels de altura;
- aplicar tons de cinza e limiarização de Otsu;
- usar `PSM 11` em caixas largas e `PSM 6` nos demais casos;
- consumir `image_to_data`, descartar tokens com confiança inferior a 25 e
  ignorar tokens que ainda encostem na borda do recorte.

Os modos de segmentação estão descritos na
[documentação oficial de linha de comando do Tesseract](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html).
O comportamento de ampliação e filtragem ganhou teste isolado em
[`tests/test_ocr.py`](../tests/test_ocr.py).

## Resultado ponta a ponta

O comando final foi:

```powershell
.\.venv\Scripts\python.exe -m flowchart_converter `
  "<fluxograma-historico-nao-versionado>" `
  --model ".\runs\flowchart\document-v2\weights\best.pt" `
  --confidence 0.25 `
  --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe" `
  --output-dir ".\output\document-v2-final"
```

O JSON registrou 38 detecções, das quais 24 eram pontas de seta, além de 65
segmentos de linha. Os 14 nós foram classificados como dez processos, duas
decisões e dois terminadores, exatamente como na imagem.

Os textos reconhecidos foram:

```text
Início
Acordar
Tomar café
Ver TV
Ir à praia
Diade sol?
Almoçar
Cochilar
Jogar futebol!
Cansado?
Passear
Jantar
Dormir
Fim
```

As duas divergências literais foram `Diade sol?`, em vez de `Dia de sol?`, e
`Jogar futebol!`, em vez de `Jogar futebol`. Ambas preservam o significado, mas
mostram por que a saída precisa continuar auditável e editável.

Das 15 conexões desenhadas, 14 foram reconstruídas. Faltou a aresta da decisão
`Cansado?` para `Jogar futebol`; as 14 arestas emitidas correspondem a conexões
reais. Para este único diagrama, a inspeção manual equivale a precisão 1,00 e
recall 0,9333 das conexões. Esses números são descritivos do caso, não uma
avaliação estatística do sistema.

## O que não funcionou tão bem

O ganho foi forte no estilo que orientou o gerador, mas não se repetiu em todos os
arquivos da pasta `fluxogramas-exemplos/`:

| Exemplo visual | Nós | Textos não vazios | Arestas | Leitura |
|---|---:|---:|---:|---|
| sitemap roxo | 0 | 0 | 0 | fora do domínio de fluxograma padrão |
| fluxograma roxo com sombras | 2 | 2 | 0 | sombras e estilo ainda causam perdas |
| recrutamento azul, documento longo | 17 | 17 | 3 | detecta conteúdo, mas OCR e topologia ficam parciais |

Essa verificação impede uma conclusão exagerada. O novo modelo resolveu o caso
documental cinza usado como alvo e aprendeu muito bem o gerador correspondente;
ele ainda não é um detector geral para qualquer diagrama colorido, com sombras,
ícones ou estrutura de sitemap.

Também permanecem limitações anteriores do artigo:

- rótulos de aresta como `SIM` e `NÃO` ainda não entram no JSON;
- conectores curvos, cruzados ou com sombra exigem uma reconstrução mais robusta;
- o Graphviz não estava instalado nesta execução, portanto JSON e DOT foram
  produzidos, mas a imagem reconstruída não;
- a avaliação real ainda precisa de vários documentos com grafos esperados,
  mantidos fora das decisões de treinamento.

## Escolhas e alternativas rejeitadas

| Decisão | Motivo | Consequência |
|---|---|---|
| não “corrigir” o baseline apenas baixando `confidence` | a 0,05 surgiu somente uma detecção a 0,07168 | evitou mascarar falta de aprendizado com falsos positivos |
| não treinar com o próprio fluxograma de aceitação | ele deixaria de medir transferência para uma imagem não vista | o resultado é mais informativo, embora ainda influencie a parada |
| gerar dados no estilo alvo | havia pouca evidência reutilizável com licença e anotação compatíveis | experimento reproduzível, porém diversidade visual limitada |
| manter imagens externas licenciadas só no benchmark | separa procedência e reduz vazamento | elas não aumentam a diversidade do treino atual |
| continuar com OCR separado do detector | texto e geometria têm sinais e métricas diferentes | permite melhorar ou substituir o OCR sem retreinar YOLO |
| usar pesos do baseline como ponto inicial | reaproveita representação já aprendida das classes | treinamento convergiu em poucas épocas |
| parar na época 6 | critério de aceitação alcançado e métricas sintéticas altas | economiza CPU, mas exige registrar que o plano de 50 épocas não terminou |
| manter JSON como artefato principal | erros de texto e aresta precisam ser inspecionáveis | a renderização não esconde falhas semânticas |

## Reprodução

Gerar novamente o dataset determinístico:

```powershell
.\.venv\Scripts\python.exe scripts\generate_document_flowcharts.py `
  --output flow-chart-document `
  --train 160 `
  --val 32 `
  --test 32 `
  --seed 2026
```

Executar os testes do projeto:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Na revisão desta atualização, a suíte terminou com 14 testes aprovados. O teste
do gerador valida que as caixas YOLO permanecem normalizadas; o teste do OCR
protege a ampliação e a remoção de tokens de borda.

## Alterações recomendadas no artigo publicado

1. **Seção 4 — dataset e treinamento:** manter as boas práticas gerais e adicionar
   o dataset `flow-chart-document`, sua composição, o uso de transferência a
   partir do baseline e a parada real na época 6.
2. **Seção 5 — utilização:** acrescentar `--tesseract-cmd` ao exemplo do Windows e
   explicar que `pytesseract` não instala o executável do Tesseract.
3. **Seção 6 — estudo de caso:** preservar o caso controlado como teste de regra e
   adicionar o caso empírico com a comparação 0 → 14 nós.
4. **Seção 7 — avaliação:** atualizar a suíte de 10 para 14 testes, acrescentar as
   métricas sintéticas separadas e a inspeção manual do caso real. Não misturar
   esses resultados com o benchmark de latência Canny/Hough já publicado.
5. **Seção 8 — limitações:** registrar explicitamente a falha nos diagramas roxos
   e o resultado parcial no documento azul.
6. **Conclusão:** trocar “ainda falta um dataset e pesos” por “há um primeiro
   checkpoint experimental e um gerador direcionado, mas ambos ainda precisam de
   publicação versionada e validação em um conjunto real congelado”.

## Formulação sugerida para a conclusão

> A atualização confirmou a hipótese arquitetural: a saída vazia não exigia
> abandonar o pipeline híbrido, mas alinhar cada estágio ao domínio. Um detector
> ajustado ao estilo documental forneceu as 14 regiões esperadas; o Tesseract,
> instalado e calibrado sobre esses recortes, preencheu todos os rótulos; e a
> reconstrução geométrica recuperou 14 das 15 conexões. O resultado ainda não é
> generalização ampla: diagramas coloridos e com sombras continuam difíceis, e o
> conjunto sintético mede sobretudo a distribuição que ele próprio gera. O
> próximo experimento precisa congelar um conjunto real, versionar o checkpoint e
> medir separadamente formas, CER/WER do OCR e F1 das conexões.
