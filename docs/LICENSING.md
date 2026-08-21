# Licenciamento das dependências

Este documento registra a análise técnica de licenças do projeto. Ele não é
aconselhamento jurídico.

## Escopo da licença MIT

O código original deste repositório permanece sob a licença MIT. Dependências,
executáveis externos, datasets e pesos de modelos conservam suas próprias
licenças. Instalar um extra do projeto não transforma uma dependência de
terceiros em software MIT.

## Perfis de instalação

| Perfil | Componentes relevantes | Situação de licença |
|---|---|---|
| Núcleo | NumPy e OpenCV | Licenças permissivas; preservar avisos ao redistribuir binários |
| OCR | pytesseract e Tesseract | Licenças permissivas; o executável Tesseract é instalado separadamente |
| Detecção `ml` | Ultralytics YOLO, código e modelos | AGPL-3.0 ou licença comercial da Ultralytics |
| PDF `pdf` | PyMuPDF/MuPDF | AGPL-3.0 ou licença comercial da Artifex |
| `full` | Todos os itens anteriores | Inclui simultaneamente as duas dependências AGPL |

## Consequência prática

Segundo a orientação publicada pela Ultralytics, um projeto que usa seu código
ou seus modelos deve disponibilizar a obra derivada completa sob AGPL-3.0 ou
obter uma licença Enterprise. A Artifex exige um ambiente compatível com AGPL
para PyMuPDF/MuPDF ou uma licença comercial quando essas obrigações não puderem
ser cumpridas.

Por isso, publicar somente este repositório sob MIT não resolve automaticamente
o licenciamento de uma aplicação completa que instale e use os extras `ml` ou
`pdf`. Para um produto empresarial ou de código fechado, as opções de menor
risco são:

1. adquirir as licenças comerciais aplicáveis;
2. substituir PyMuPDF por um renderizador permissivo, como `pypdfium2`, e
   substituir também a pilha Ultralytics por detector, treinamento e pesos com
   licenças compatíveis; ou
3. relicenciar e distribuir a aplicação completa de forma compatível com
   AGPL-3.0, incluindo o código-fonte correspondente e os demais materiais
   exigidos pela licença.

A fronteira jurídica entre um programa MIT e uma dependência opcional carregada
em tempo de execução depende da forma de distribuição e integração. A posição
conservadora para este projeto é seguir a orientação dos titulares das
dependências até que exista parecer jurídico específico.

## Fontes primárias

- [Licença da Ultralytics](https://www.ultralytics.com/license)
- [AGPL-3.0 no repositório Ultralytics](https://github.com/ultralytics/ultralytics/blob/main/LICENSE)
- [Licenciamento da Artifex](https://artifex.com/licensing)
- [PyMuPDF no PyPI](https://pypi.org/project/PyMuPDF/)
- [Licenciamento do pypdfium2](https://pypi.org/project/pypdfium2/)

Antes de publicar pesos treinados ou datasets, revise também a licença das
imagens de treinamento, dos pesos-base e das ferramentas usadas para produzir o
modelo. Esses direitos são independentes da licença do código deste repositório.
