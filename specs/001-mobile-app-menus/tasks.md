---

description: "Lista de tarefas do aplicativo móvel Sumi (Flutter)"
---

# Tasks: Aplicativo móvel com os menus do Sumi

**Input**: Design documents from `/specs/001-mobile-app-menus/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: a spec não pede TDD; não há tarefas de teste por história. A validação é feita por
`flutter analyze` e pelos cenários de `quickstart.md`.

**Organization**: tarefas agrupadas por história de usuário da spec (US1, US2, US2b, US3, US4, US5).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: história da spec a que a tarefa pertence
- Caminhos relativos à raiz do repositório; o app fica em `sumi-mobile/`

## Regras que valem para TODAS as tarefas

- **Princípio III**: todo acesso à API passa por um repositório declarado como `abstract class
  XRepository` + `class ApiXRepository implements XRepository` (Dio), no mesmo arquivo. O provider
  Riverpod é tipado pela abstração: `final xRepositoryProvider = Provider<XRepository>((ref) =>
  ApiXRepository(ref.read(apiClientProvider)));`. Telas/controllers só importam a abstração.
- **Princípio IV**: sem classe base genérica de repositório, sem camada `domain/usecases`. Um
  controller Riverpod (`Notifier`/`AsyncNotifier`) por tela quando houver estado.
- **Paridade com o web**: cada tela tem uma fonte no web (indicada na tarefa). Ler o componente
  `.ts`/`.html` e o service correspondente em `sumi-web/src/app/core/services/` para copiar
  payloads, validações, textos e regras. Rotas e corpos: `contracts/api-consumed.md`.
- Modelos com `fromJson`/`toJson` manuais (sem codegen), campos conforme `data-model.md`.
- Textos da interface em português. Sem comentários óbvios.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: criar o projeto Flutter conforme a skill, adaptado ao plano

- [X] T001 Criar o projeto em `sumi-mobile/` com `flutter create --org com.sumi --platforms=android --project-name sumi_mobile sumi-mobile` e ajustar `android:label="Sumi"` em `sumi-mobile/android/app/src/main/AndroidManifest.xml`
- [X] T002 Adicionar dependências em `sumi-mobile/pubspec.yaml`: `flutter pub add flutter_riverpod dio go_router flutter_secure_storage intl just_audio video_player share_plus path_provider` e `flutter pub add dev:flutter_lints`
- [X] T003 [P] Adicionar `<uses-permission android:name="android.permission.INTERNET"/>` e `android:usesCleartextTraffic="true"` (API em HTTP na LAN durante o desenvolvimento) em `sumi-mobile/android/app/src/main/AndroidManifest.xml`
- [X] T004 [P] Criar as pastas `lib/core/{api,auth,router,services,storage,theme}`, `lib/features/{shell,auth,home,projects,library,series,voice_test,production}` e `lib/shared` em `sumi-mobile/`, removendo o contador de exemplo de `sumi-mobile/lib/main.dart` e `sumi-mobile/test/widget_test.dart`
- [X] T005 [P] Adicionar `sumi-mobile/` (build/, .dart_tool/) ao `.gitignore` da raiz se o `.gitignore` gerado pelo Flutter não for suficiente, e citar o app na seção de arquitetura do `README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: núcleo usado por todas as histórias

**⚠️ CRITICAL**: nenhuma história começa antes desta fase

- [X] T006 [P] Criar `SecureStorage` em `sumi-mobile/lib/core/storage/secure_storage.dart` com cache em memória (padrão da skill), guardando apenas `access_token`, `user` (JSON) e `draft_project_id`; métodos `accessToken`, `user`, `draftProjectId`, `saveSession`, `saveDraftProjectId`, `clear` (research R4, R6)
- [X] T007 [P] Criar `NotificationService` + `scaffoldMessengerKey` em `sumi-mobile/lib/core/services/notification_service.dart`, idêntico à skill (`show`, `success`, `error`)
- [X] T008 Criar `apiClientProvider` em `sumi-mobile/lib/core/api/api_client.dart`: `baseUrl` de `String.fromEnvironment('API_BASE_URL')`, `connectTimeout` 10 s, `receiveTimeout` 10 min (R7); `onRequest` anexa `Authorization: Bearer`; `onError` converte `{detail: String}` ou `{detail: [{msg}]}` em toasts, mostra "Sem conexão com o servidor." em erros de conexão/timeout, respeita `extra['silent'] == true` e em 401 chama `authProvider.notifier.logout()`. **Não** desembrulhar envelope nem ler ProblemDetails (R3) (depende de T006, T007)
- [X] T009 [P] Criar `AppUser` em `sumi-mobile/lib/core/auth/app_user.dart` com `id`, `name`, `email` (nullable), `plan`, `group`, `approved` (data-model)
- [X] T010 Adicionar `POST /auth/refresh` em `sumi-api/src/prompt_clinica/routers/auth.py`: `user: User = Depends(get_current_user)`, retorna `TokenResponse(access_token=create_access_token(<mesmo subject usado em auth_service.login>, settings.jwt_remember_expire_minutes), user=UserOut do usuário)`; conferir com `curl -X POST -H "Authorization: Bearer <token>" <API>/auth/refresh` que volta um token com `exp` 30 dias à frente (research R4, contracts/api-consumed.md)
- [X] T011 Criar `AuthRepository` (abstrata) + `ApiAuthRepository` em `sumi-mobile/lib/core/auth/auth_repository.dart`: `login(email, password)` → `POST /auth/login` com `remember: true`, e `refresh()` → `POST /auth/refresh` com `extra: {'silent': true}`, ambos retornando `(accessToken, AppUser)` (depende de T008, T009)
- [X] T012 Criar `authProvider` em `sumi-mobile/lib/core/auth/auth_provider.dart`: estado `loading/autenticado/anônimo`; bootstrap lê o token e verifica o claim `exp` como `_isExpired` da skill — expirado → `logout()` e toast "Sua sessão expirou. Entre novamente."; válido → entra autenticado e chama `refresh()` em seguida, salvando o token novo (falha de rede mantém o token atual; 401 → `logout()`); `login()` salva sessão; `logout()` limpa storage (R4) (depende de T006, T011, T010)
- [X] T013 [P] Criar tema em `sumi-mobile/lib/core/theme/app_theme.dart` com as cores/tipografia do Sumi lidas de `sumi-web/src/styles.scss` (variáveis `--ink-*`, `--accent`, e as cores de capa usadas como `cover_accent`), expondo `coverAccentColor(String)` e `coverAccentSoftColor(String)`
- [X] T014 [P] Criar `AudioPlayerService` (abstrata) + `JustAudioPlayerService` em `sumi-mobile/lib/core/services/audio_player_service.dart`: `playBytes(Uint8List)`, `playUrl(String)`, `stop()` (R5, R9)
- [X] T015 [P] Criar `FileShareService` (abstrata) + `SharePlusFileShareService` em `sumi-mobile/lib/core/services/file_share_service.dart`: `shareBytes(Uint8List bytes, String fileName, String mimeType)` grava em `getTemporaryDirectory()` e abre `Share.shareXFiles` (R9, FR-007b)
- [X] T016 [P] Criar widgets compartilhados em `sumi-mobile/lib/shared/`: `empty_state.dart` (mensagem + ação opcional), `error_retry.dart` (mensagem + botão "Tentar novamente"), `filter_chips.dart` (lista de chips com seleção única) (FR-011)
- [X] T017 Criar `app_router.dart` em `sumi-mobile/lib/core/router/app_router.dart` com `go_router`, rota `/login` e redirect: sem token → `/login`; autenticado em `/login` → `/`; `refreshListenable` ligado ao `authProvider` (contracts/navigation.md) (depende de T012)
- [X] T018 Configurar `sumi-mobile/lib/main.dart`: `ProviderScope`, `MaterialApp.router` com `routerConfig`, `theme` (T013) e `scaffoldMessengerKey` (T007) (depende de T013, T017)

**Checkpoint**: o app abre e redireciona para `/login`

---

## Phase 3: User Story 1 - Entrar no app e ver o Início (Priority: P1) 🎯 MVP

**Goal**: login, menu com os 5 itens e painel Início igual ao web

**Independent Test**: logar com conta que tem projetos no web e conferir projetos e personagens recentes no Início; fechar e reabrir e continuar logado (quickstart 1–3, 15)

- [X] T019 [US1] Criar `LoginScreen` em `sumi-mobile/lib/features/auth/login_screen.dart`: campos e-mail e senha, botão "Entrar", loading no botão, chama `authProvider.notifier.login`; fonte: `sumi-web/src/app/features/auth/auth-screen/` (só a parte de login; sem cadastro e sem recuperar senha)
- [X] T020 [P] [US1] Criar modelo `Project` em `sumi-mobile/lib/features/projects/project.dart` com os campos de `ProjectOut` e `ProjectDetailOut` (data-model; `pages` "1–20"; `premise`, `synopsis`, `characters`, `scenarios` só no detalhe)
- [X] T021 [P] [US1] Criar modelo `Character` em `sumi-mobile/lib/features/library/character.dart` com os campos de `CharacterOut` (data-model; `approved: false` = RASCUNHO)
- [X] T022 [US1] Criar `ProjectsRepository` + `ApiProjectsRepository` em `sumi-mobile/lib/features/projects/projects_repository.dart` com `list()` → `GET /projects` (demais métodos entram em US2b) (depende de T008, T020)
- [X] T023 [US1] Criar `CharactersRepository` + `ApiCharactersRepository` em `sumi-mobile/lib/features/library/characters_repository.dart` com `list()` → `GET /characters` (depende de T008, T021)
- [X] T024 [US1] Criar `ShellScaffold` em `sumi-mobile/lib/features/shell/shell_scaffold.dart`: `Scaffold` com `AppBar` (título da tela) e `NavigationDrawer` com cabeçalho (marca "墨 Sumi", nome, e-mail e plano do usuário), itens **Início** (`/`), **Projetos** (`/projects`), **Biblioteca** (`/library`), **Séries** (`/series`), **Teste de Voz** (`/voice-test`) com o item atual destacado, e "Sair" que chama `logout()`. Nenhum item de administração (FR-002)
- [X] T025 [US1] Registrar `ShellRoute` com `ShellScaffold` em `sumi-mobile/lib/core/router/app_router.dart` contendo `/` e placeholders para `/projects`, `/library`, `/series`, `/voice-test` (depende de T024)
- [X] T026 [P] [US1] Criar widget `ProjectCover` em `sumi-mobile/lib/shared/project_cover.dart`: capa com cor `cover_accent`, padrão `cover_tone`, tags de gênero (maiúsculo) e "N pg", título; e variante de linha para modo lista. Fonte: `coverPattern`/`coverBgSize` em `sumi-web/src/app/features/home/home.component.ts` (depende de T013)
- [X] T027 [US1] Criar `homeControllerProvider` em `sumi-mobile/lib/features/home/home_controller.dart`: carrega projetos e personagens em paralelo, filtro de status com as mesmas opções de `statuses` em `sumi-web/src/app/features/home/home.component.ts` (depende de T022, T023)
- [X] T028 [US1] Criar `HomeScreen` em `sumi-mobile/lib/features/home/home_screen.dart`: cabeçalho "SEUS PROJETOS / Onde sua próxima história começa.", chips de status (T016), grade de `ProjectCover`, botão "+ Nova HQ" (navega para `/production/new/idea`, rota criada em US2b), seção "BIBLIOTECA — PERSONAGENS RECENTES" com avatar de inicial, "Nenhum personagem ainda." quando vazio e "Ver biblioteca completa" → `/library`; skeleton no loading, `ErrorRetry` no erro, pull-to-refresh. Fonte: `sumi-web/src/app/features/home/home.component.html` (sem importar/exportar backup) (depende de T025, T026, T027)

**Checkpoint**: US1 completa — MVP demonstrável

---

## Phase 4: User Story 2 - Consultar Projetos (Priority: P2)

**Goal**: lista completa de HQs com grade/lista e filtro

**Independent Test**: abrir Projetos, alternar grade/lista mantendo filtro, tocar num projeto (quickstart 4)

- [X] T029 [US2] Criar `projectsListControllerProvider` em `sumi-mobile/lib/features/projects/projects_list_controller.dart` com projetos, filtro de status e modo `grid`/`list` (o filtro persiste ao trocar o modo) (depende de T022)
- [X] T030 [US2] Criar `ProjectsScreen` em `sumi-mobile/lib/features/projects/projects_screen.dart`: chips de status, botão alternar visualização, grade de `ProjectCover` ou linhas (título, subtítulo, gênero, status, data `dd/MM/yyyy`), estado vazio "Nenhum projeto ainda." com ação "+ Nova HQ", pull-to-refresh; tocar abre o projeto via `openProject(context, project)` (definido em T044) e registrar a rota `/projects` em `sumi-mobile/lib/core/router/app_router.dart` (depende de T029)

**Checkpoint**: US1 e US2 funcionando

---

## Phase 5: User Story 2b - Produzir uma HQ completa pelo app (Priority: P2)

**Goal**: fluxo Ideia → Personagens → Cenários → Roteiro → Revisão → Editor → Finalizar → Vídeo, com rascunho, exclusão e compartilhamento

**Independent Test**: criar HQ do zero até Finalizar e ver igual no web; abrir no web uma HQ iniciada no app (quickstart 5–10)

### Base da produção

- [X] T031 [P] [US2b] Criar modelos `Panel` e `Bubble` em `sumi-mobile/lib/features/production/panel.dart` (data-model: `kind` ∈ `say|thought|shout|whisper|narration` padrão `say`; `side` ∈ `left|right`; `tail` ∈ `none|left|right`; `x`,`y` int 0–100, padrão 8/12)
- [X] T032 [P] [US2b] Criar modelos `Scenario`, `PortraitJob`, `SceneJob`, `VideoJob` em `sumi-mobile/lib/features/production/jobs_and_scenarios.dart` (data-model; `status` ∈ `pending|running|done|error`; `progress` 0–100 só no VideoJob)
- [X] T033 [US2b] Criar `ProductionStep` em `sumi-mobile/lib/features/production/production_step.dart`: enum `idea, characters, scenarios, script, review, editor, finalize, video` com `label` (Ideia, Personagens, Cenários, Roteiro, Revisão, Editor, Finalizar, Vídeo) e `path`, e função `ProductionStep stepFor(Project detail, List<Panel> panels)` com a regra exata do data-model ("só se pula para uma etapa se todas as anteriores já foram feitas"), avaliada nesta ordem, primeira verdadeira vence: `video_url != null` → video; quadros existem e todos têm `image_url` → editor; quadros existem → review; `detail.scenarios` não vazio → script; `detail.characters` não vazio → scenarios; senão → characters (depende de T020, T031)
- [X] T034 [US2b] Completar `ProjectsRepository` em `sumi-mobile/lib/features/projects/projects_repository.dart` com `get`, `create`, `update`, `delete`, `generateSynopsis`, `setCharacters`, `setScenarios`, `exportPanelsZip` (bytes, silent), `startVideo`, `videoJob` (silent), `getYoutubeMetadata`, `saveYoutubeMetadata`, `generateYoutubeMetadata` (contracts/api-consumed.md; payloads de `sumi-web/src/app/core/services/project.service.ts`)
- [X] T035 [US2b] Criar `PanelsRepository` + `ApiPanelsRepository` em `sumi-mobile/lib/features/production/panels_repository.dart` com todos os métodos da seção PanelsRepository do contrato (payloads de `sumi-web/src/app/core/services/panel.service.ts`) (depende de T031)
- [X] T036 [US2b] Criar `ScenariosRepository` + `ApiScenariosRepository` em `sumi-mobile/lib/features/production/scenarios_repository.dart` (`list`, `create`, `update`, `options`, `startScene`, `sceneJob` silent, `deleteUnused`; payloads de `sumi-web/src/app/core/services/scenario.service.ts`) (depende de T032)
- [X] T037 [US2b] Completar `CharactersRepository` em `sumi-mobile/lib/features/library/characters_repository.dart` com `create`, `update`, `options`, `startPortrait`, `portraitJob` (silent), `deleteUnused` (payloads de `sumi-web/src/app/core/services/character.service.ts`) (depende de T032)
- [X] T038 [P] [US2b] Criar `StylesRepository` + `ApiStylesRepository` em `sumi-mobile/lib/features/production/styles_repository.dart` com `list()` → `GET /styles` (fonte: `sumi-web/src/app/core/services/style.service.ts`)
- [X] T039 [US2b] Criar `pollJob<T>` em `sumi-mobile/lib/features/production/poll_job.dart`: consulta a cada 2 s até `done`/`error`, para quando o widget é descartado e reconsulta imediatamente em `AppLifecycleState.resumed` (R7, FR-007a)
- [X] T040 [US2b] Criar `productionDraftProvider` em `sumi-mobile/lib/features/production/production_draft.dart`: `projectId` e `title` do projeto em produção, persistidos via `SecureStorage.saveDraftProjectId` (T006), mais os dados da Ideia/Personagens/Cenários ainda não salvos no servidor (equivalente a `sumi-web/src/app/core/services/project-draft.service.ts`) (depende de T006)
- [X] T041 [US2b] Criar `ProductionScaffold` em `sumi-mobile/lib/features/production/production_scaffold.dart`: AppBar com título da HQ, barra horizontal rolável das 8 etapas (atual destacada; concluídas com ✓; só concluídas e a atual são tocáveis — nunca uma etapa futura; Editor e Finalizar ficam tocáveis depois da Revisão), menu com "Excluir projeto" quando há `projectId`, e voltar do Android indo à etapa anterior (contracts/navigation.md) (depende de T033, T040)
- [X] T042 [US2b] Criar `DeleteProjectDialog` em `sumi-mobile/lib/features/production/delete_project_dialog.dart`: texto de aviso permanente, código aleatório exibido, campo para digitá-lo, botão "Excluir definitivamente" habilitado só com código igual; chama `ProjectsRepository.delete`, limpa o rascunho e volta para `/`. Fonte: modal de exclusão em `sumi-web/src/app/features/shell/shell.component.html` e `deleteCode` em `shell.component.ts` (depende de T034, T041)
- [X] T043 [US2b] Registrar as rotas `/production/new/idea` e `/production/:id/{characters,scenarios,script,review,editor,finalize,video}` com `ProductionScaffold` em `sumi-mobile/lib/core/router/app_router.dart` (placeholders até cada etapa ficar pronta) (depende de T041)
- [X] T044 [US2b] Criar `openProject(BuildContext, Project)` em `sumi-mobile/lib/features/production/open_project.dart`: busca o detalhe (`ProjectsRepository.get`) e os quadros, calcula `stepFor`, grava o `projectId` no rascunho e navega para `/production/:id/<etapa>` (depende de T033, T034, T035, T040)

### Etapas (em ordem; cada uma: controller + tela no mesmo diretório)

- [X] T045 [US2b] Etapa **Ideia** em `sumi-mobile/lib/features/production/idea/idea_screen.dart`: campos de `ProjectCreate` (title, premise, genre, tone obrigatórios; `pages` "1–20" padrão 4; style via `StylesRepository`; color_mode; narrator_voice_id), mesmas opções/validações de `sumi-web/src/app/features/projects/new/new-project.component.ts`; ao avançar **cria o projeto no servidor** (`ProjectsRepository.create`, como na linha 154 do componente web), grava `projectId`/`title` no `productionDraftProvider` e navega para `/production/:id/characters`; se o rascunho já tem `projectId` (usuário voltou à Ideia), usa `update` em vez de `create` (depende de T034, T038, T040, T043)
- [X] T046 [US2b] Criar `CharacterForm` em `sumi-mobile/lib/features/library/character_form.dart`: campos de `CharacterCreate` com opções de `GET /character-options`, geração de retrato (`startPortrait` + `pollJob` mostrando progresso), escolha entre candidatos, refazer e aprovar; reutilizável pela etapa Personagens e pela Biblioteca. Fonte: `sumi-web/src/app/features/projects/characters/characters-screen.component.{ts,html}` (depende de T037, T039)
- [X] T047 [US2b] Etapa **Personagens** em `sumi-mobile/lib/features/production/characters/characters_step_screen.dart`: selecionar personagens existentes da biblioteca e criar novos com `CharacterForm`; ao avançar salva a seleção com `ProjectsRepository.setCharacters` e navega para `/production/:id/scenarios`. Mesmo fluxo de `characters-screen.component.ts` (depende de T034, T046)
- [X] T048 [US2b] Etapa **Cenários** em `sumi-mobile/lib/features/production/scenarios/scenarios_step_screen.dart`: selecionar/criar cenários com opções de `GET /scenario-options` e geração por `startScene` + `pollJob`; ao concluir salva com `ProjectsRepository.setScenarios` e navega para `/production/:id/script` (o projeto já existe desde a Ideia). Fonte: `sumi-web/src/app/features/projects/scenarios/scenarios-screen.component.{ts,html}` (depende de T036, T039, T045, T047)
- [X] T049 [US2b] Etapa **Roteiro** em `sumi-mobile/lib/features/production/script/script_screen.dart`: sinopse (gerar com `generateSynopsis`, editar e salvar via `update`), geração de quadros (`panels/generate`) quando não houver, edição de label/caption/framing/personagem por quadro, adicionar, reordenar (arrastar) e excluir quadros; loading com mensagem durante gerações longas; recarrega os quadros ao reabrir. Fonte: `sumi-web/src/app/features/projects/script/script.component.{ts,html}` (depende de T034, T035, T043)
- [X] T050 [US2b] Etapa **Revisão** em `sumi-mobile/lib/features/production/review/review_screen.dart`: grade de quadros com imagem, gerar todas (`generate-images`), regerar uma (`panels/{id}/generate` ou `panels/{id}/image` com corpo `{}`, usando o mesmo método que `review.component.ts` chama via `panel.service.ts` — não há upload de arquivo), status por quadro e recarga em `resumed`. Fonte: `sumi-web/src/app/features/projects/review/review.component.{ts,html}` (depende de T035, T039)
- [X] T051 [US2b] Copiar `LAYOUTS` de `sumi-web/src/app/features/projects/editor/editor.component.ts` para `sumi-mobile/lib/features/production/editor/page_layouts.dart` como constantes Dart com mesmo `key`, `label` e geometria
- [X] T052 [US2b] Etapa **Editor** em `sumi-mobile/lib/features/production/editor/editor_screen.dart`: seletor de layout (T051), página dentro de `InteractiveViewer`, balões posicionados por `x`/`y` em %, arrasto com `GestureDetector.onPanUpdate` e salvamento em `onPanEnd` via `PanelsRepository.update(bubbles)` (com debounce como o `patchSubject` do web), editar texto/kind/side/tail do balão e gerar balões (`bubbles/generate`); estilos de balão de `bubbleStyle`/`bubbleClass` em `sumi-web/src/app/features/projects/editor/editor.component.ts` (R8) (depende de T035, T051)
- [X] T053 [US2b] Etapa **Finalizar** em `sumi-mobile/lib/features/production/finalize/finalize_screen.dart`: pré-visualização das páginas, baixar ZIP (`exportPanelsZip`) e compartilhar via `FileShareService` (`application/zip`), e demais ações de `sumi-web/src/app/features/projects/final/final.component.{ts,html}` (depende de T015, T034)
- [X] T054 [US2b] Etapa **Vídeo** em `sumi-mobile/lib/features/production/video/video_screen.dart`: iniciar exportação (`startVideo` + `pollJob` com barra de `progress`), pré-visualizar com `video_player` a partir de `video_url`, compartilhar o MP4 via `FileShareService` (`video/mp4`), metadados do YouTube (get/generate/save). Fonte: `sumi-web/src/app/features/projects/video/video.component.{ts,html}` (depende de T015, T034, T039)
- [X] T055 [US2b] Ligar "+ Nova HQ" (Início e Projetos) a `/production/new/idea` limpando o rascunho anterior, e abrir projetos via `openProject` em `sumi-mobile/lib/features/home/home_screen.dart` e `sumi-mobile/lib/features/projects/projects_screen.dart` (depende de T044, T045)

**Checkpoint**: HQ completa produzida pelo app

---

## Phase 6: User Story 3 - Biblioteca de personagens (Priority: P2)

**Goal**: listar, buscar, filtrar, criar e editar personagens

**Independent Test**: buscar, filtrar por papel, criar personagem com retrato aprovado e ver no web (quickstart 11)

- [X] T056 [US3] Criar `libraryControllerProvider` em `sumi-mobile/lib/features/library/library_controller.dart`: personagens, busca por nome (case-insensitive, contém) e filtro de papel com as opções de `roleFilters` em `sumi-web/src/app/features/library/library.component.ts` (depende de T023)
- [X] T057 [US3] Criar `LibraryScreen` em `sumi-mobile/lib/features/library/library_screen.dart`: campo "Buscar personagem…", chips de papel, grade de cartões (retrato ou inicial sobre cor de `accentOf`, papel em maiúsculo, nome, "N anos · altura", resumo, traços, selo "RASCUNHO"), estado vazio "Nenhum personagem encontrado." com "Criar o primeiro personagem", botão "+ Novo personagem"; tocar abre edição; registrar `/library` no router. Fonte: `sumi-web/src/app/features/library/library.component.html` (depende de T056)
- [X] T058 [US3] Criar `CharacterEditScreen` em `sumi-mobile/lib/features/library/character_edit_screen.dart` usando `CharacterForm` (T046) para `/library/new` e `/library/:id`; salvar chama `create`/`update` e volta à lista atualizada; registrar as rotas em `sumi-mobile/lib/core/router/app_router.dart` (depende de T046, T057)

**Checkpoint**: Biblioteca completa

---

## Phase 7: User Story 4 - Gerenciar Séries (Priority: P3)

**Goal**: CRUD de séries e vínculo com projetos

**Independent Test**: criar série, vincular 2 projetos, editar, excluir (quickstart 12)

- [X] T059 [P] [US4] Criar modelo `Series` em `sumi-mobile/lib/features/series/series.dart` (`id`, `name` obrigatório, `description` nullable, `project_ids`, `updated_at`)
- [X] T060 [US4] Criar `SeriesRepository` + `ApiSeriesRepository` em `sumi-mobile/lib/features/series/series_repository.dart` (`list`, `get`, `create`, `update`, `delete`, `setProjects`; payloads de `sumi-web/src/app/core/services/series.service.ts`) (depende de T059)
- [X] T061 [US4] Criar `seriesControllerProvider` em `sumi-mobile/lib/features/series/series_controller.dart` com séries, projetos do usuário (`ProjectsRepository.list`) e estado de edição (`startNew`, `edit`, `toggleProject`, `save`, `remove`, `cancel` como em `sumi-web/src/app/features/series/series.component.ts`) (depende de T022, T060)
- [X] T062 [US4] Criar `SeriesScreen` em `sumi-mobile/lib/features/series/series_screen.dart`: cabeçalho "SUAS SÉRIES / Agrupe seus projetos em séries.", lista de séries com nº de projetos, formulário (bottom sheet) com nome "Ex: Crônicas de Outono", descrição "Do que se trata esta série?" e checklist de projetos, confirmação antes de excluir; registrar `/series` no router. Fonte: `sumi-web/src/app/features/series/series.component.html` (depende de T061)

**Checkpoint**: Séries completas

---

## Phase 8: User Story 5 - Teste de Voz (Priority: P3)

**Goal**: pesquisar voz, gerar e ouvir áudio, salvar configuração

**Independent Test**: escolher voz, gerar áudio ≤ 300 caracteres, ouvir e salvar (quickstart 13)

- [X] T063 [P] [US5] Copiar `MINIMAX_VOICES` de `sumi-web/src/app/core/data/minimax-voices.ts` para `sumi-mobile/lib/features/voice_test/minimax_voices.dart` como lista constante com os mesmos campos
- [X] T064 [P] [US5] Criar modelo `Voice` em `sumi-mobile/lib/features/voice_test/voice.dart` (`id`, `name`, `voice_id`, `age_start`/`age_end` int nullable, `sex` nullable, `details` nullable)
- [X] T065 [US5] Criar `VoicesRepository` + `ApiVoicesRepository` em `sumi-mobile/lib/features/voice_test/voices_repository.dart` (`list`, `create`, `update`, `delete`, `test` → `POST /voice/test` com `ResponseType.bytes`; corpo de `VoiceTestBody` e payloads de `sumi-web/src/app/core/services/voice.service.ts`) (depende de T064)
- [X] T066 [US5] Criar `voiceTestControllerProvider` em `sumi-mobile/lib/features/voice_test/voice_test_controller.dart`: busca no catálogo por nome ou id, voz selecionada, texto, geração (preserva o texto em caso de erro), vozes salvas, `save`, `editSaved`, `resetForm` como em `sumi-web/src/app/features/voice-test/voice-test.component.ts` (depende de T063, T065)
- [X] T067 [US5] Criar `VoiceTestScreen` em `sumi-mobile/lib/features/voice_test/voice_test_screen.dart`: "Pesquisar voz (nome ou id)…", lista do catálogo, campo de texto, botão gerar que toca o áudio via `AudioPlayerService.playBytes`, formulário salvar (nome "Ex.: Menina alegre", descrição "Ex.: menina de 5 a 10 anos, tom doce e animado", idade inicial/final), lista de vozes salvas tocáveis para edição; registrar `/voice-test` no router. Fonte: `sumi-web/src/app/features/voice-test/voice-test.component.html` (depende de T014, T066)

**Checkpoint**: todas as histórias funcionando

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T068 Revisar todas as telas para os estados de loading, vazio e erro com `EmptyState`/`ErrorRetry` e pull-to-refresh nas listas (FR-011) em `sumi-mobile/lib/features/`
- [X] T069 [P] Remover placeholders de rota restantes em `sumi-mobile/lib/core/router/app_router.dart` e conferir a tabela de `contracts/navigation.md`
- [X] T070 [P] Conferir Princípios III/IV: nenhuma tela importa `Api…Repository` nem `Dio` diretamente (`grep -r "Api.*Repository(\|package:dio" sumi-mobile/lib/features` só pode achar os arquivos `*_repository.dart`)
- [X] T071 Rodar `flutter analyze` em `sumi-mobile/` e corrigir todos os avisos
- [ ] T072 Gerar `flutter build apk --debug --dart-define=API_BASE_URL=...` em `sumi-mobile/` e executar os 17 cenários de `specs/001-mobile-app-menus/quickstart.md` num aparelho físico
- [X] T073 [P] Criar `sumi-mobile/README.md` com pré-requisitos, `--dart-define=API_BASE_URL`, comandos de run/build (resumo do quickstart)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)** → **Foundational (2)** → histórias
- **US1 (3)**: depende só de Foundational — MVP
- **US2 (4)**: depende de US1 (reusa `ProjectsRepository`, `ProjectCover`, shell)
- **US2b (5)**: depende de US1 e US2 (abre projetos a partir das listas)
- **US3 (6)**: depende de US1 e de T046 (`CharacterForm`) de US2b
- **US4 (7)**: depende de US1 (lista de projetos)
- **US5 (8)**: depende só de Foundational + shell (T024/T025)
- **Polish (9)**: após as histórias desejadas

### Within US2b

T031–T032 → T033; T034–T038 → T039–T043 → T044 → etapas em ordem T045 → T047 → T048 → T049 →
T050 → T051/T052 → T053 → T054 → T055 (T046 antes de T047).

### Parallel Opportunities

- Setup: T003, T004, T005
- Foundational: T010 (backend), T006, T007, T009, T013, T014, T015, T016 em paralelo; depois T008 → T011 → T012 → T017 → T018
- US1: T020, T021, T026 em paralelo
- US2b: T031, T032, T038 em paralelo; T051 em paralelo com T049/T050
- Após US1, **US4 e US5** podem andar em paralelo a US2/US2b

---

## Parallel Example: User Story 1

```text
Task: "T020 Criar modelo Project em sumi-mobile/lib/features/projects/project.dart"
Task: "T021 Criar modelo Character em sumi-mobile/lib/features/library/character.dart"
Task: "T026 Criar widget ProjectCover em sumi-mobile/lib/shared/project_cover.dart"
```

## Parallel Example: User Story 5

```text
Task: "T063 Copiar MINIMAX_VOICES para sumi-mobile/lib/features/voice_test/minimax_voices.dart"
Task: "T064 Criar modelo Voice em sumi-mobile/lib/features/voice_test/voice.dart"
```

---

## Implementation Strategy

### MVP First (US1)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **Parar e validar** cenários 1–3 e 15 do quickstart

### Incremental Delivery

1. US1 → MVP (login, menu, Início)
2. US2 → Projetos
3. US2b → produção, validando cada etapa contra o web antes da próxima
4. US3 → Biblioteca
5. US4 → Séries
6. US5 → Teste de Voz

## Notes

- [P] = arquivos diferentes, sem dependência pendente
- Commits em português, formato `tipo: descrição`, sem atribuição de IA (constituição)
- Commit ao fim de cada tarefa ou grupo lógico; validar cada checkpoint antes de seguir
