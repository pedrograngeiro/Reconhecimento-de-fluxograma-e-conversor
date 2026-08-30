# Fluxogramas de exemplo

Estas imagens foram geradas originalmente para este projeto em 29 de agosto de
2026 com a ferramenta integrada de geração de imagens da OpenAI. Nenhuma imagem
de terceiros foi usada como referência, entrada ou alvo de edição.

Elas podem ser usadas para demonstração, avaliação manual do pipeline e criação
de casos de regressão. Não fazem parte do dataset de treinamento atual.

Para testar uma delas depois de treinar o modelo:

```powershell
flowchart-converter fluxogramas-exemplos\original-aprovacao-compra.png `
  --model runs\flowchart\detector\weights\best.pt `
  --output-dir output\aprovacao
```

Novas imagens de demonstração podem ser colocadas nesta pasta quando forem
próprias ou tiverem licença e proveniência documentadas. Para que uma imagem
participe do treinamento, ela também precisa ser anotada e colocada na estrutura
YOLO descrita em [Dataset e treinamento](../docs/DATASET.md). O
[Guia de uso](../docs/GUIA_DE_USO.md) explica a diferença entre exemplos,
dataset e saídas geradas.

| Arquivo | Tema e composição solicitados |
|---|---|
| `original-atendimento-suporte.png` | fluxo horizontal de atendimento, com decisão de urgência e ramos que se reencontram |
| `original-aprovacao-compra.png` | fluxo vertical de compra, com validação de orçamento e retorno para ajuste |
| `original-rotina-estudos.png` | fluxo vertical de estudo, com revisão de anotações antes dos exercícios |
| `original-publicacao-conteudo.png` | fluxo horizontal editorial, com decisão de aprovação e ciclo de correção |

## Especificação visual comum

- fundo branco;
- formas clássicas de fluxograma;
- terminadores verdes, processos azuis e decisões âmbar;
- conectores escuros com pontas de seta visíveis;
- texto curto em português;
- sem logos, marcas d'água, ícones decorativos ou identidade de terceiros.
