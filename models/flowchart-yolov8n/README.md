# Flowchart YOLOv8n

Checkpoint de referência para as seis classes consumidas pelo conversor:

| ID | Classe |
|---:|---|
| 0 | `process` |
| 1 | `decision` |
| 2 | `terminator` |
| 3 | `input_output` |
| 4 | `connector` |
| 5 | `arrow_head` |

## Treinamento

- arquitetura inicial: Ultralytics YOLOv8n;
- dataset: [FC-Detection](https://huggingface.co/datasets/galirage/FC-Detection), licença Apache-2.0;
- divisão: 55 imagens de treino, 14 de validação e 30 de teste reservado;
- configuração: 100 épocas, imagens de 640 px, batch 8, CPU, seed 42;
- duração: 0,296 hora em um Intel Core i7-14700;
- versão: Ultralytics 8.4.126, PyTorch 2.13.0+cpu e Python 3.12.14.

O mapeamento usado na conversão foi `data` para `input_output`, `connection`
para `connector` e `arrow_end` para `arrow_head`. As anotações `text`, `arrow`
e `arrow_start` não foram usadas. O script
[`preparar_dataset_fc_detection.py`](../../preparar_dataset_fc_detection.py)
reproduz o download e a conversão.

## Validação do melhor checkpoint

| Métrica | Resultado |
|---|---:|
| Precisão | 0,791 |
| Recall | 0,915 |
| mAP50 | 0,805 |
| mAP50-95 | 0,647 |

Os dados completos estão em [`metrics/results.csv`](metrics/results.csv), e os
gráficos em [`metrics/results.png`](metrics/results.png) e
[`metrics/confusion_matrix_normalized.png`](metrics/confusion_matrix_normalized.png).

## Limitações

A validação contém apenas uma instância de `connector`, portanto a métrica dessa
classe não é representativa. `arrow_head` também teve desempenho inferior às
formas principais. O conjunto é pequeno e deve ser ampliado antes de uso em
documentos muito diferentes dos exemplos de treinamento.

## Licenciamento

O dataset declara licença Apache-2.0. O checkpoint foi derivado de pesos e da
implementação Ultralytics YOLO; ele não é abrangido automaticamente pela licença
MIT do código deste repositório. Consulte [`docs/LICENSING.md`](../../docs/LICENSING.md)
e cumpra a AGPL-3.0 ou obtenha a licença comercial aplicável antes de redistribuir
ou usar o modelo em um produto incompatível com a AGPL.
