# Licenciamento do projeto

Este documento registra a política técnica de licenciamento do repositório. Ele
não substitui aconselhamento jurídico para um caso concreto.

## Licença principal

O código e a documentação originais do projeto são distribuídos sob a
**GNU Affero General Public License v3.0**, variante `AGPL-3.0-only`. O texto
integral está no arquivo [`LICENSE`](../LICENSE).

Copyright (C) 2026 Pedro Grangeiro.

A AGPL permite usar, estudar, modificar e redistribuir o programa. Ao distribuir
uma versão modificada ou permitir que usuários interajam com ela por uma rede,
devem ser cumpridas as condições da licença, inclusive a disponibilização do
código-fonte correspondente da versão em uso.

## Versões publicadas anteriormente

O relicenciamento vale para o projeto a partir do commit que introduziu a
AGPL-3.0-only. As versões publicadas até o commit `a4080b2` foram oferecidas sob
MIT e continuam utilizáveis sob aqueles termos. Uma licença já concedida para
uma versão anterior não é revogada retroativamente.

Consulte o [registro do relicenciamento](RELICENCIAMENTO.md) para o escopo da
auditoria de autoria realizada antes da mudança.

## Dependências

Uma dependência conserva sua própria licença. A AGPL deste projeto não altera os
termos dos componentes instalados separadamente.

| Perfil | Componentes relevantes | Licença ou cuidado principal |
|---|---|---|
| Núcleo | NumPy e OpenCV | licenças permissivas; preservar avisos ao redistribuir binários |
| OCR | pytesseract e Tesseract | Apache-2.0; preservar avisos e licenças aplicáveis |
| Detecção `ml` | Ultralytics YOLO, código e modelos | AGPL-3.0 ou licença comercial da Ultralytics |
| PDF `pdf` | PyMuPDF/MuPDF | AGPL-3.0 ou licença comercial da Artifex |
| `full` | todos os itens anteriores | reúne simultaneamente os componentes acima |

O licenciamento principal sob AGPL reduz a incompatibilidade com a distribuição
aberta do Ultralytics e do PyMuPDF, mas não substitui a leitura das condições de
cada titular. A Ultralytics declara que seu código, seus modelos-base e os pesos
treinados com sua plataforma são abrangidos pela AGPL por padrão, salvo licença
comercial aplicável.

## Pesos treinados

Antes de publicar um arquivo `.pt`, registre em seu model card:

- arquitetura e pesos-base utilizados;
- versão e licença da ferramenta de treinamento;
- nome, versão, origem e licença de cada dataset;
- transformações e classes aproveitadas;
- parâmetros, métricas e limitações;
- licença aplicável ao checkpoint final.

Pesos não são automaticamente abrangidos apenas pela licença do código deste
repositório. Também devem ser respeitados os termos do modelo-base, da ferramenta
e dos dados de treinamento.

## Datasets e imagens

Não adicione uma imagem obtida na internet sem registrar:

- página de origem e URL do arquivo;
- autor ou organização responsável;
- licença e link para seus termos;
- alterações realizadas, como corte ou rasterização;
- data de obtenção, quando relevante.

Prefira material próprio, CC0 ou domínio público. Obras CC BY exigem atribuição;
obras CC BY-SA também exigem que adaptações sejam compartilhadas sob licença
compatível. Material sem licença explícita não deve ser redistribuído nem usado
para treinar um peso que será publicado sem uma análise específica.

As imagens de benchmark deste projeto estão documentadas em
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) e no manifesto
[`benchmarks/online_samples/manifest.csv`](../benchmarks/online_samples/manifest.csv).
Elas mantêm suas licenças individuais e não são relicenciadas pela AGPL.

Os exemplos originais gerados para o projeto têm sua proveniência registrada em
[`fluxogramas-exemplos/README.md`](../fluxogramas-exemplos/README.md). Outputs
gerados por ferramentas de IA ainda devem ser revisados para evitar marcas,
personagens ou elementos protegidos de terceiros.

## Checklist para novas contribuições

- confirmar que o autor pode oferecer a contribuição sob AGPL-3.0-only;
- evitar copiar código sem preservar licença e avisos obrigatórios;
- não versionar pesos ou datasets sem model card ou ficha de origem;
- atualizar `THIRD_PARTY_NOTICES.md` ao incorporar material externo;
- manter ativos com licença diferente claramente identificados;
- revisar dependências novas antes de adicioná-las ao `pyproject.toml`;
- registrar mudanças de licença em commit próprio e explícito.

## Fontes primárias

- [Texto da AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html)
- [Licença da Ultralytics](https://www.ultralytics.com/license)
- [AGPL-3.0 no repositório Ultralytics](https://github.com/ultralytics/ultralytics/blob/main/LICENSE)
- [Licenciamento da Artifex](https://artifex.com/licensing)
- [Licença do Tesseract](https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE)
- [Licença do pytesseract](https://github.com/madmaze/pytesseract/blob/master/LICENSE)

As páginas dos titulares podem mudar. Verifique novamente as fontes antes de
uma distribuição relevante ou da publicação de um novo modelo.
