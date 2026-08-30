# Registro do relicenciamento para AGPL-3.0-only

Data da auditoria: 30 de agosto de 2026.

## Decisão

O projeto passou de MIT para `AGPL-3.0-only` para manter aberto o código de
versões modificadas e serviços de rede e para alinhar a distribuição do pipeline
com seus principais componentes AGPL.

Versões publicadas até `a4080b2` continuam disponíveis sob MIT. A mudança não
revoga direitos já concedidos sobre essas versões.

## Auditoria de autoria

Antes da mudança, foram verificados:

- os 12 commits alcançáveis por `main`;
- os 16 commits alcançáveis considerando todas as branches e tags locais/remotas;
- autores e e-mails registrados em cada commit;
- colaboradores reconhecidos pela API do GitHub;
- autores dos quatro pull requests existentes;
- histórico do arquivo `LICENSE`;
- o pull request aberto que propõe publicar um checkpoint treinado.

Todos os commits e pull requests encontrados estavam atribuídos a Pedro
Grangeiro. Os dois e-mails observados pertencem à mesma identidade:

- `46334439+pedrograngeiro@users.noreply.github.com`;
- `pedrop.grangeiro@gmail.com`.

A API de colaboradores do GitHub também retornou somente `pedrograngeiro`. O
arquivo `LICENSE` havia sido criado no commit inicial e não possuía outra
alteração no histórico auditado.

Essa verificação reduz o risco de relicenciar contribuição autoral de terceiro,
mas metadados do Git não constituem, sozinhos, prova jurídica de titularidade.

## Materiais de terceiros

O relicenciamento não altera:

- licenças das imagens de benchmark;
- aviso MIT associado à imagem do PolyBoolJS;
- licenças de dependências instaladas separadamente;
- direitos e condições dos datasets;
- licença aplicável a modelos-base e checkpoints treinados.

Esses materiais continuam identificados em
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) e no
[guia de licenciamento](LICENSING.md).

## Pull request de modelo treinado

O pull request #4 foi revisado durante a auditoria. Ele está atribuído ao mesmo
autor do projeto e registra:

- pesos-base e implementação Ultralytics;
- dataset FC-Detection, declarado como Apache-2.0 pela fonte;
- parâmetros, métricas e limitações do treinamento;
- necessidade de cumprir a AGPL aplicável ao checkpoint.

Antes do merge, o model card deve ser atualizado para remover referências à
licença MIT atual do repositório e declarar diretamente `AGPL-3.0-only` para o
checkpoint, sem apagar os avisos do dataset e da Ultralytics.
