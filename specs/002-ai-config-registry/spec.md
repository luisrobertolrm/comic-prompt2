# Feature Specification: Cadastro de configurações de IA por tipo

**Feature Branch**: `main`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Criar uma tabela para cada tipo de IA, podendo cadastrar várias e ativar e desativar uma configuração. Texto (chat) com dois padrões — OpenAI-compatível e Anthropic —, Imagem e Transcrição. Nos três casos o núcleo é o mesmo: tipo, URL, chave e modelo. Só a transcrição tem um campo a mais, o idioma."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar e ativar uma IA de texto (Priority: P1)

O administrador abre **Configurações do sistema**, vai à seção **Texto** e cadastra uma nova
configuração informando nome, padrão (OpenAI-compatível ou Anthropic), URL base, chave e modelo.
Por exemplo, um modelo da ByteDance pela BytePlus. Ele testa a configuração, ativa e, a partir daí,
toda geração de texto do sistema (sinopse, roteiro, metadados do YouTube) passa a usar esse modelo.

**Why this priority**: É a dor relatada. Hoje não dá para usar um modelo de texto de outro
fornecedor (ByteDance, Anthropic) sem mexer em código, e a tela mistura campos de fornecedores
diferentes.

**Independent Test**: Cadastrar uma configuração de texto, testá-la, ativá-la e gerar uma
sinopse. O resultado vem do modelo configurado.

**Acceptance Scenarios**:

1. **Given** nenhuma configuração de texto da ByteDance, **When** o administrador cadastra
   padrão OpenAI-compatível, URL da BytePlus, chave e modelo `seed-…` e salva, **Then** a
   configuração aparece na lista de Texto como inativa.
2. **Given** uma configuração de texto cadastrada, **When** o administrador clica em **Testar**,
   **Then** o sistema envia uma mensagem curta ao modelo e mostra a resposta e o tempo, ou o erro
   devolvido pelo fornecedor.
3. **Given** a configuração A ativa e a B inativa, **When** o administrador ativa a B,
   **Then** a A fica inativa automaticamente e as próximas gerações de texto usam a B, sem
   reiniciar o sistema.
4. **Given** uma configuração no padrão Anthropic, **When** ela é ativada e uma sinopse é gerada,
   **Then** o texto é produzido pelo modelo Anthropic informado.

---

### User Story 2 - Cadastrar e ativar uma IA de imagem (Priority: P2)

Na seção **Imagem**, o administrador cadastra configurações com o mesmo formulário (nome,
padrão, URL, chave e modelo), testa, gerando uma imagem de amostra, e ativa uma delas. A geração de
retratos e painéis passa a usar a configuração ativa.

**Why this priority**: Imagem é o segundo uso mais caro e mais trocado (Seedream, OpenAI,
MiniMax), mas já funciona hoje. A melhoria é de organização, não de capacidade nova.

**Independent Test**: Cadastrar uma configuração Seedream, testá-la (a imagem de amostra aparece),
ativá-la e gerar um retrato de personagem.

**Acceptance Scenarios**:

1. **Given** a seção Imagem, **When** o administrador cadastra padrão OpenAI-compatível, URL da
   BytePlus, chave e modelo `seedream-…`, **Then** a configuração é salva.
2. **Given** uma configuração de imagem, **When** o administrador clica em **Testar**, **Then** uma
   imagem de amostra é exibida com o modelo e o tempo, ou o erro do fornecedor.
3. **Given** uma configuração de imagem ativa, **When** um usuário gera um painel, **Then** o
   painel é gerado por ela.

---

### User Story 3 - Cadastrar e ativar uma IA de transcrição (Priority: P3)

Na seção **Transcrição**, o administrador cadastra configurações com nome, URL, chave, modelo e
**idioma**, testa ditando uma frase e ativa uma delas. O ditado por voz usa a configuração ativa.

**Why this priority**: Uso menos frequente e com um só padrão.

**Independent Test**: Cadastrar uma configuração, ativá-la e usar o ditado por voz em um campo de
texto.

**Acceptance Scenarios**:

1. **Given** uma configuração de transcrição com idioma `pt`, **When** o administrador testa
   ditando uma frase, **Then** o texto transcrito aparece na tela.
2. **Given** uma configuração de transcrição ativa, **When** um usuário usa o ditado por voz,
   **Then** a transcrição usa o modelo e o idioma dela.

---

### User Story 4 - Gerenciar configurações cadastradas (Priority: P2)

O administrador vê, em cada seção, a lista de configurações com nome, padrão, modelo, final da
chave e situação (ativa ou inativa). Ele pode editar, desativar ou excluir uma configuração.

**Why this priority**: Sem isso o cadastro vira lixo acumulado e não há como trocar chave vencida.

**Independent Test**: Editar o modelo de uma configuração, desativar outra e excluir uma terceira.
A lista reflete as três ações.

**Acceptance Scenarios**:

1. **Given** uma configuração salva, **When** o administrador a edita sem preencher a chave,
   **Then** a chave atual é mantida.
2. **Given** uma configuração ativa, **When** o administrador a desativa, **Then** aquele tipo de
   IA fica sem configuração ativa, e as funções que dependem dele avisam o usuário em vez de falhar
   sem explicação.
3. **Given** uma configuração inativa, **When** o administrador a exclui e confirma, **Then** ela
   some da lista.

---

### Edge Cases

- **Nenhuma configuração ativa em um tipo**: a função correspondente (gerar texto, imagem ou
  transcrever) retorna mensagem clara: "Nenhuma IA de <tipo> ativa. Configure em Configurações do
  sistema."
- **Exclusão da configuração ativa**: bloqueada com aviso; é preciso desativá-la antes.
- **Chave ou URL inválida**: salvar é permitido; o botão Testar mostra o erro devolvido pelo
  fornecedor. A ativação não depende de teste prévio.
- **Geração em andamento durante a troca da ativa**: a geração em curso termina com a
  configuração com que começou; só as novas usam a nova.
- **Padrão de imagem MiniMax**: além do OpenAI-compatível, a seção Imagem aceita o padrão
  MiniMax, que tem formato próprio.
- **Nomes repetidos**: permitidos, já que a lista mostra modelo e final da chave para diferenciar.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST manter um cadastro separado para cada tipo de IA: **Texto**,
  **Imagem**, **Transcrição**, **Voz** e **Vídeo**.
- **FR-002**: Cada tipo MUST permitir várias configurações cadastradas.
- **FR-003**: Cada tipo MUST ter **no máximo uma** configuração ativa. Ativar uma desativa
  automaticamente a anterior do mesmo tipo.
- **FR-004**: Toda configuração MUST ter: **nome**, **padrão**, **URL base**, **chave** e
  **modelo**. As configurações de Transcrição MUST ter também **idioma**.
- **FR-005**: Os padrões permitidos MUST ser:
  - Texto: **OpenAI-compatível** e **Anthropic**.
  - Imagem: **OpenAI-compatível**, **Seedream (ByteDance)** e **MiniMax**.
  - Transcrição: **OpenAI-compatível**.
  - Voz: **MiniMax**.
  - Vídeo: **MiniMax**.
  O padrão é só um valor do campo Tipo. Nenhum fornecedor tem campos próprios no formulário.
- **FR-006**: Ao escolher o padrão, a URL base MUST vir pré-preenchida com o endereço oficial do
  fornecedor, editável pelo administrador.
- **FR-007**: A chave MUST ser armazenada criptografada e nunca retornar para a tela. A tela
  mostra só os 4 últimos caracteres. Na edição, deixar o campo em branco mantém a chave atual.
- **FR-008**: Cada configuração MUST ter uma ação **Testar** que usa os dados salvos e mostra o
  resultado (texto, imagem ou transcrição), o tempo gasto ou o erro do fornecedor.
- **FR-009**: Ativar, desativar, editar ou excluir uma configuração MUST valer imediatamente para
  as próximas gerações, sem reiniciar o sistema.
- **FR-010**: Todas as gerações de texto do sistema MUST usar a configuração de Texto ativa; as de
  imagem, a de Imagem ativa; o ditado por voz, a de Transcrição ativa; a síntese de voz (teste de
  voz, narração), a de Voz ativa; a geração de vídeo, a de Vídeo ativa.
- **FR-011**: Sem configuração ativa em um tipo, as funções dependentes MUST informar o usuário
  com mensagem clara, sem erro genérico.
- **FR-012**: A exclusão de uma configuração ativa MUST ser bloqueada com aviso para desativá-la
  antes.
- **FR-013**: Apenas administradores MUST acessar e alterar essas configurações.
- **FR-014**: Na primeira execução após a entrega, as configurações em uso hoje (chaves e modelos
  de OpenAI, MiniMax e BytePlus/Seedream) MUST ser convertidas em registros do novo cadastro, já
  ativos onde estavam em uso, sem que o administrador precise recadastrar.
- **FR-015**: Depois da conversão, chaves e modelos de texto, imagem e transcrição MUST vir só do
  cadastro, e não mais do arquivo de ambiente.
- **FR-016**: Voz e Vídeo MUST usar o mesmo formulário dos demais tipos (nome, padrão, URL base,
  chave, modelo), sem campos específicos de fornecedor. O teste de Voz sintetiza uma frase curta e
  toca o áudio; o teste de Vídeo é opcional por ser lento e caro, e pode se limitar a validar a
  conexão.

#### Tela

- **FR-017**: Cada tipo de IA MUST ser exibido em um **grid** com nome, padrão, modelo, final da
  chave, situação (ativa/inativa) e ações (editar, testar, excluir).
- **FR-018**: Incluir e editar uma configuração MUST acontecer em um **popup** (diálogo modal)
  com os campos do FR-004, sem sair da tela.
- **FR-019**: A ativação MUST poder ser feita de dois jeitos, com o mesmo efeito (FR-003):
  - **no grid**, por um controle de ativar/desativar na própria linha;
  - **no popup**, por um campo "Ativa" salvo junto com os demais.
- **FR-020**: Ao ativar uma configuração pelo grid ou pelo popup, o grid MUST refletir na hora
  que a anterior do mesmo tipo ficou inativa.

#### Adaptação do código

- **FR-021**: Todo ponto do código que hoje lê configuração **específica de fornecedor** (chave,
  modelo, URL ou parâmetro com nome de fornecedor, vindo do arquivo de ambiente ou da tabela atual
  de configurações) MUST ser **localizado e adaptado** para ler a configuração ativa do tipo
  correspondente, no formato genérico (padrão, URL, chave, modelo, idioma).
- **FR-022**: Depois da adaptação, MUST NOT restar no código leitura de chave, modelo ou URL de IA
  por nome de fornecedor (ex.: `OPENAI_API_KEY`, `MINIMAX_*`, `BYTEPLUS_*`, `SEEDREAM_MODEL`,
  `STT_*`, `AI_TEXT_*`, `AI_IMAGE_*`), exceto na conversão inicial (FR-014).
- **FR-023**: O inventário de pontos a adaptar MUST ser levantado no planejamento por busca no
  código. O ponto de partida conhecido é:

  | Área | Configuração específica hoje |
  |------|------------------------------|
  | Montagem dos provedores de IA (`sumi-api/src/prompt_clinica/ai/__init__.py`) | `openai_api_key`, `byteplus_api_key`, `minimax_*`, `seedream_model`, `ai_text_*`, `ai_image_*`, `stt_*` |
  | Configuração MiniMax (`ai/minimax/config.py`) | `MINIMAX_API_KEY`, `MINIMAX_BASE_URL`, `MINIMAX_GROUP_ID`, `MINIMAX_*_MODEL` |
  | Provedor Seedream (`ai/providers/seedream_provider.py`) | `byteplus_api_key`, `byteplus_base_url`, `seedream_model` |
  | Configurações gerais (`config.py`) | campos de IA por fornecedor e `STT_*` |
  | Transcrição (`ai/speech.py`) | `stt_model`, `stt_language` |
  | Voz e teste de imagem (`routers/voice.py`, `routers/image_test.py`) | `minimax_config()` |
  | Saúde da API (`routers/health.py`) | `current_config()` |
  | Configurações do sistema (modelo, schema, serviço e rota `app_settings`) | uma coluna por fornecedor |
  | Tela web (`sumi-web/.../features/app-settings`, `core/services/admin.service.ts`) | campos por fornecedor |
  | Arquivos de ambiente de exemplo e documentação (`README.md`, `ARCHITECTURE.md`, `.env.example`) | variáveis por fornecedor |

### Key Entities

- **Configuração de IA de Texto**: nome, padrão (OpenAI-compatível / Anthropic), URL base, chave
  criptografada, modelo, ativa (sim/não), data de atualização.
- **Configuração de IA de Imagem**: nome, padrão (OpenAI-compatível / Seedream / MiniMax), URL base, chave
  criptografada, modelo, ativa (sim/não), data de atualização.
- **Configuração de IA de Transcrição**: nome, padrão (OpenAI-compatível), URL base, chave
  criptografada, modelo, idioma, ativa (sim/não), data de atualização.
- **Configuração de IA de Voz**: nome, padrão (MiniMax), URL base, chave criptografada, modelo,
  ativa (sim/não), data de atualização.
- **Configuração de IA de Vídeo**: nome, padrão (MiniMax), URL base, chave criptografada, modelo,
  ativa (sim/não), data de atualização.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O administrador cadastra e ativa um modelo de texto de um fornecedor novo
  compatível (ex.: ByteDance) em menos de 2 minutos, sem alteração de código nem reinício.
- **SC-002**: Trocar a IA ativa de um tipo exige no máximo 1 clique no grid, e a próxima geração
  já usa a nova configuração.
- **SC-006**: Uma busca no código por nomes de configuração de fornecedor (FR-022) não retorna
  nenhuma leitura fora da conversão inicial.
- **SC-003**: 100% das configurações em uso antes da entrega continuam funcionando depois dela,
  sem recadastro.
- **SC-004**: O formulário de cadastro tem os mesmos campos para todos os fornecedores de um tipo.
  Nenhum campo é específico de um fornecedor.
- **SC-005**: Nenhuma chave completa aparece na tela ou nas respostas do sistema.

## Assumptions

- **URLs padrão por padrão/fornecedor**: OpenAI `https://api.openai.com/v1`; BytePlus
  `https://ark.ap-southeast.bytepluses.com/api/v3`; MiniMax (texto compatível)
  `https://api.minimax.io/v1`; MiniMax (imagem, voz, vídeo) `https://api.minimax.io`; Anthropic
  `https://api.anthropic.com`.
- O padrão OpenAI-compatível atende OpenAI, ByteDance/BytePlus, MiniMax (texto), DeepSeek e
  Ollama. Nenhum desses exige campo próprio no cadastro.
- Para imagem, tamanho e proporção dependem de cada geração e ficam fora do cadastro.
- Parâmetros de geração (temperatura, limite de tokens) dependem da tarefa e ficam fora do
  cadastro.
- A **IA local por usuário** (tela Configurações do usuário, Ollama) continua como está e fora
  deste escopo.
- O provedor **ComfyUI** (uso local de desenvolvimento) fica fora do cadastro.
- A tela atual "Configurações do sistema" é substituída por esta. As seções antigas de chaves e
  modelos por fornecedor deixam de existir.
- Ativação não exige teste prévio bem-sucedido.
- O "Group ID" do MiniMax já é opcional hoje (só é enviado se preenchido) e a API atual não o
  exige. Ele sai do cadastro, sem campo específico de fornecedor.
