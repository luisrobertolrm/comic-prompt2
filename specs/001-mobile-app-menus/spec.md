# Feature Specification: Aplicativo móvel com os menus do Sumi

**Feature Branch**: `android`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Criar aplicativo com os menus hoje existentes no web Projetos, Biblioteca, Séries, Teste de Voz. A Dashboard inicial também, sendo que ela vai aparecer no menu Início"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entrar no app e ver o Início (Priority: P1)

O criador abre o aplicativo, faz login com a mesma conta do Sumi web e cai na tela **Início**, que
mostra o mesmo painel inicial do web: projetos em andamento (com título, gênero, páginas, status e
data da última alteração), filtro por status e os personagens recentes da biblioteca. Um menu de
navegação dá acesso a Início, Projetos, Biblioteca, Séries e Teste de Voz.

**Why this priority**: sem login, menu e painel inicial nenhum outro menu é alcançável; é o MVP.

**Independent Test**: instalar o app, logar com uma conta que já tem projetos no web e conferir que
os mesmos projetos e personagens recentes aparecem no Início.

**Acceptance Scenarios**:

1. **Given** um usuário com conta no Sumi, **When** ele faz login no app, **Then** vê a tela Início
   com seus projetos e personagens recentes.
2. **Given** o usuário no Início, **When** escolhe um status no filtro, **Then** só os projetos com
   aquele status são listados.
3. **Given** o usuário em qualquer tela, **When** abre o menu, **Then** vê exatamente os itens
   Início, Projetos, Biblioteca, Séries e Teste de Voz, com o item atual destacado.
4. **Given** o usuário logado, **When** fecha e reabre o app, **Then** continua logado e volta ao
   Início sem digitar credenciais.

---

### User Story 2 - Consultar Projetos (Priority: P2)

No menu **Projetos**, o criador vê a lista completa de suas HQs, alterna entre visualização em
grade e em lista, filtra por status e abre um projeto para acompanhá-lo.

**Why this priority**: projetos são o conteúdo principal do produto.

**Independent Test**: abrir Projetos, alternar grade/lista, filtrar e abrir um projeto existente.

**Acceptance Scenarios**:

1. **Given** um usuário com projetos, **When** abre Projetos, **Then** vê todos os seus projetos.
2. **Given** a lista em grade, **When** toca em alternar visualização, **Then** a lista passa a
   linhas, mantendo o filtro aplicado.
3. **Given** um projeto na lista, **When** o usuário toca nele, **Then** o app abre o projeto na
   etapa de produção em que ele parou.

---

### User Story 2b - Produzir uma HQ completa pelo app (Priority: P2)

Pelo botão **Nova HQ** (no Início ou em Projetos) ou abrindo um projeto existente, o criador
percorre as mesmas etapas de produção do web, na mesma ordem: **Ideia → Personagens → Cenários →
Roteiro → Revisão → Editor → Finalizar → Vídeo**. Durante a produção, o app mostra o título da HQ
atual, a etapa ativa e as etapas concluídas, e permite pular para qualquer etapa já liberada. O
criador também pode excluir o projeto, confirmando com o código exibido, como no web.

**Why this priority**: é o fluxo principal do produto; sem ele o app é só de consulta.

**Independent Test**: criar uma HQ do zero no app até a etapa Finalizar e conferir que o resultado
aparece igual no web; depois abrir no web uma HQ iniciada no app e continuar de onde parou.

**Acceptance Scenarios**:

1. **Given** o usuário no Início, **When** toca em Nova HQ e descreve uma ideia, **Then** o projeto
   é criado e o app avança para a etapa Personagens.
2. **Given** um projeto em produção, **When** o usuário conclui uma etapa, **Then** ela fica marcada
   como concluída e a próxima é aberta.
3. **Given** um projeto em andamento, **When** o usuário sai do app no meio de uma etapa e volta,
   **Then** encontra o rascunho salvo na mesma etapa.
4. **Given** uma etapa com geração por IA (texto, imagem, áudio ou vídeo) em andamento, **When** a
   geração termina, **Then** o resultado aparece na tela sem o usuário precisar recarregar.
5. **Given** um projeto, **When** o usuário pede para excluir e digita o código de confirmação,
   **Then** o projeto e suas imagens são apagados permanentemente.
6. **Given** a etapa Finalizar ou Vídeo concluída, **When** o usuário pede o arquivo final, **Then**
   pode salvá-lo no aparelho ou compartilhá-lo.

---

### User Story 3 - Navegar pela Biblioteca de personagens (Priority: P2)

No menu **Biblioteca**, o criador vê seus personagens reutilizáveis (retrato, nome, papel, idade,
altura, resumo, traços e indicação de rascunho), busca por nome e filtra por papel. Também cria
novos personagens e edita os existentes, incluindo a geração e aprovação do retrato, com as mesmas
regras da etapa Personagens do web.

**Why this priority**: personagens são reutilizados entre HQs e mantê-los pelo celular é frequente.

**Independent Test**: abrir Biblioteca, buscar e filtrar; criar um personagem com retrato gerado,
aprová-lo e conferir que aparece no web.

**Acceptance Scenarios**:

1. **Given** personagens cadastrados, **When** o usuário digita parte de um nome na busca,
   **Then** só os personagens correspondentes aparecem.
2. **Given** a Biblioteca, **When** o usuário escolhe um papel no filtro, **Then** a lista mostra
   só personagens daquele papel.
3. **Given** nenhum personagem encontrado, **When** a lista fica vazia, **Then** o app mostra a
   mensagem "Nenhum personagem encontrado".
4. **Given** a Biblioteca, **When** o usuário toca em Novo personagem, preenche os dados e gera o
   retrato, **Then** o personagem é salvo como rascunho até ser aprovado.
5. **Given** um personagem existente, **When** o usuário edita seus dados ou gera outro retrato,
   **Then** as alterações são salvas e valem para as próximas HQs que o usarem.

---

### User Story 4 - Gerenciar Séries (Priority: P3)

No menu **Séries**, o criador cria, edita e exclui séries (nome e descrição) e escolhe quais
projetos pertencem a cada série, como no web.

**Why this priority**: organização complementar; não bloqueia a produção.

**Independent Test**: criar uma série, vincular dois projetos, editar o nome e excluí-la.

**Acceptance Scenarios**:

1. **Given** a tela Séries, **When** o usuário cria uma série com nome e descrição, **Then** ela
   aparece na lista e também no web.
2. **Given** uma série, **When** o usuário marca/desmarca projetos, **Then** a associação é salva.
3. **Given** uma série, **When** o usuário a exclui e confirma, **Then** ela some da lista e os
   projetos continuam existindo.

---

### User Story 5 - Teste de Voz (Priority: P3)

No menu **Teste de Voz**, o criador pesquisa uma voz do catálogo por nome ou id, escreve um texto,
gera o áudio, ouve no próprio aparelho e salva a configuração de voz com nome e descrição para
reutilizar depois.

**Why this priority**: ferramenta isolada, fora do fluxo de produção.

**Independent Test**: escolher uma voz, gerar áudio para um texto curto, ouvir e salvar.

**Acceptance Scenarios**:

1. **Given** o catálogo de vozes, **When** o usuário pesquisa por nome, **Then** vê as vozes
   correspondentes.
2. **Given** uma voz e um texto, **When** toca em gerar, **Then** o áudio é reproduzido no aparelho.
3. **Given** um áudio gerado, **When** o usuário salva com nome e descrição, **Then** a voz salva
   aparece na lista e pode ser reaberta para edição.

---

### Edge Cases

- Sem conexão com a internet: o app avisa claramente e permite tentar novamente, sem travar.
- Sessão perto de expirar: o app renova a sessão sem intervenção a cada abertura; só se ela já
  tiver expirado (30 dias sem abrir o app) ou a renovação falhar, volta ao login com aviso.
- Usuário sem projetos/personagens/séries: cada tela mostra um estado vazio com mensagem.
- Falha na geração de áudio: mensagem de erro amigável; o texto digitado não é perdido.
- Dados alterados no web enquanto o app está aberto: ao voltar à tela ou puxar para atualizar, o
  app mostra os dados atuais.
- Usuário administrador: os menus de administração do web não aparecem no app.
- Mesmo projeto aberto no web e no app ao mesmo tempo: vale a última alteração salva, e a outra
  tela mostra os dados atualizados ao recarregar a etapa.
- Conexão cai durante uma geração por IA: a geração continua no servidor e o resultado aparece
  quando a conexão voltar.
- Editor em tela pequena: os quadros podem ser ampliados e reposicionados por toque, e a página
  inteira pode ser vista com zoom.
- Ditado por voz disponível no web para campos de texto: no app, usa-se o ditado do próprio teclado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O app MUST permitir login com as mesmas contas do Sumi web e manter a sessão entre
  aberturas do app até o usuário sair.
- **FR-002**: O app MUST oferecer um menu com exatamente: Início, Projetos, Biblioteca, Séries e
  Teste de Voz, além da opção de sair da conta.
- **FR-003**: A tela Início MUST ser a primeira após o login e mostrar o painel inicial do web:
  projetos (título, gênero, nº de páginas, status, última alteração) com filtro por status e
  personagens recentes, com atalho para a Biblioteca completa.
- **FR-004**: A tela Projetos MUST listar todos os projetos do usuário, com filtro por status e
  alternância entre grade e lista.
- **FR-005**: A Biblioteca MUST listar os personagens do usuário com busca por nome e filtro por
  papel, exibindo retrato (ou inicial quando não houver imagem), dados e indicação de rascunho.
- **FR-006**: A tela Séries MUST permitir criar, editar e excluir séries e vincular/desvincular
  projetos.
- **FR-007**: O app MUST oferecer o fluxo completo de produção do web — Nova HQ e as etapas Ideia,
  Personagens, Cenários, Roteiro, Revisão, Editor, Finalizar e Vídeo — com as mesmas regras e
  resultados, indicador de etapa atual/concluídas, rascunho salvo automaticamente e exclusão de
  projeto com código de confirmação.
- **FR-007a**: Gerações por IA demoradas MUST mostrar progresso e MUST continuar mesmo se o usuário
  trocar de tela ou minimizar o app; o resultado aparece quando ele voltar.
- **FR-007b**: O usuário MUST poder salvar no aparelho ou compartilhar o resultado final (HQ e vídeo).
- **FR-008**: A Biblioteca MUST permitir criar e editar personagens, incluindo gerar, refazer e
  aprovar o retrato, com as mesmas regras da etapa Personagens.
- **FR-009**: O Teste de Voz MUST permitir pesquisar vozes, gerar e reproduzir áudio a partir de um
  texto e salvar/editar configurações de voz.
- **FR-010**: Tudo que o usuário cria ou altera no app MUST aparecer no web e vice-versa (mesma
  conta, mesmos dados).
- **FR-011**: Todas as telas MUST tratar carregamento, estado vazio e erro com mensagens claras.

### Key Entities

- **Usuário**: conta do Sumi; nome, e-mail, plano.
- **Projeto (HQ)**: título, subtítulo, gênero, páginas, status, capa, última alteração.
- **Personagem**: nome, papel, idade, altura, resumo, traços, retrato, situação (aprovado/rascunho).
- **Série**: nome, descrição e conjunto de projetos.
- **Cenário**: ambiente reutilizável do projeto, com descrição e imagem de referência.
- **Quadro (painel)**: unidade da página da HQ; texto do roteiro, imagem gerada, posição na página.
- **Etapa de produção**: posição do projeto no fluxo (Ideia → … → Vídeo) e quais já foram concluídas.
- **Voz salva**: voz do catálogo escolhida, nome, descrição e parâmetros de geração.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um usuário com conta existente chega ao Início em menos de 30 segundos a partir da
  primeira abertura do app.
- **SC-002**: Com o usuário já logado, o Início fica visível em até 3 segundos após abrir o app.
- **SC-003**: 100% dos projetos, personagens e séries visíveis no web aparecem no app para a mesma
  conta.
- **SC-004**: Qualquer menu é alcançado em no máximo 2 toques a partir de qualquer tela.
- **SC-005**: Um áudio de teste de voz é gerado e começa a tocar em até 15 segundos para textos de
  até 300 caracteres.
- **SC-006**: Um usuário consegue levar uma HQ da Ideia até Finalizar usando apenas o app, e o
  resultado é idêntico ao que veria no web.
- **SC-007**: Nenhum trabalho é perdido ao sair do app no meio de uma etapa: 100% dos rascunhos são
  recuperados ao voltar.

## Assumptions

- O aplicativo é para Android (branch `android`); outras plataformas ficam fora deste escopo.
- O app consome os mesmos dados e regras do backend atual; não há regra de negócio nova. A única
  mudança no backend é um endpoint de renovação de sessão.
- Ao reabrir um projeto, o app só pula para uma etapa se todas as anteriores já foram feitas.
- Por ter o fluxo de produção completo, o escopo é grande; o plano deve entregar por fatias na
  ordem de prioridade das histórias (P1 → P2 → P3), cada uma utilizável sozinha.
- No web, o item "Projetos" leva ao painel inicial; no app esse painel passa a ser o **Início** e
  "Projetos" vira a lista completa de HQs.
- Ficam fora do app: Teste de imagem, Configurações, Administração, Config. do sistema, galeria
  pública e importação/exportação de backup.
- Uso exclusivamente online; não há modo offline nesta versão.
- O visual segue a identidade do Sumi web (referência em `comic-prompt/`), adaptado ao celular.
