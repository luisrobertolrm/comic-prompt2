# Implementation Plan: Aplicativo móvel com os menus do Sumi

**Branch**: `android` | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-mobile-app-menus/spec.md`

## Summary

App Android em Flutter (padrão `flutter-app-skill-cc`) com os menus Início, Projetos, Biblioteca,
Séries e Teste de Voz, além do fluxo completo de produção do web (Ideia → Vídeo). O app consome a
API FastAPI existente, acrescida apenas de `POST /auth/refresh` (renovação deslizante da sessão);
as diferenças entre a API e a skill (sem envelope, erros `detail`, login e-mail/senha) são
absorvidas no `core/api` do app
([research.md](research.md) R3–R4). Toda dependência de dados passa por repositórios abstratos
(Princípio III).

## Technical Context

**Language/Version**: Dart 3 / Flutter 3.41 (stable)

**Primary Dependencies**: flutter_riverpod, dio, go_router, flutter_secure_storage, intl (skill);
just_audio, video_player, share_plus, path_provider (R9)

**Storage**: nenhum banco local; `flutter_secure_storage` para token, usuário e ID do projeto em
criação

**Testing**: flutter_test (widget tests com override de providers), `flutter analyze`

**Target Platform**: Android (minSdk padrão do Flutter 3.41)

**Project Type**: mobile-app consumindo API existente

**Performance Goals**: Início em ≤ 3 s com sessão salva (SC-002); áudio de teste em ≤ 15 s (SC-005)

**Constraints**: somente online; nenhuma alteração em `sumi-web/`; em `sumi-api/` só a rota
`POST /auth/refresh`; gerações
longas sobrevivem a minimizar o app (R7)

**Scale/Scope**: ~15 telas (5 menus + login + 8 etapas + edição de personagem); 8 repositórios

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Verificação | Status |
|---|---|---|
| I. Planejamento antes de código | Este plano + tasks precedem qualquer código; implementação só após aprovação | ✅ |
| II. Caminho mais simples | Backend ganha só uma rota de renovação (R4); etapa derivada dos dados (R6); polling em vez de push (R7); `share_plus` cobre salvar e compartilhar | ✅ (ver Complexity Tracking) |
| III. Programar para abstrações | Repositórios `abstract class` + `Api…Repository` para todos os dados de domínio vindos do web; providers tipados pela abstração; `AudioPlayerService` e `FileShareService` abstratos (R5). `SecureStorage` concreto — exceção justificada abaixo | ✅ (com exceção registrada) |
| IV. Legibilidade | Uma abstração por repositório, sem camadas `domain/usecases`, sem classe base genérica de repositório; widgets por tela | ✅ |
| V. Sem comentários óbvios | Regra de revisão | ✅ |
| Fluxo de Trabalho | Commits em português, sem atribuição de IA | ✅ |

**Re-check pós-design**: contratos e data model não introduzem camadas além das listadas. ✅

## Project Structure

### Documentation (this feature)

```text
specs/001-mobile-app-menus/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-consumed.md
│   └── navigation.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
sumi-api/src/prompt_clinica/routers/auth.py   # + POST /auth/refresh

sumi-mobile/                         # novo — flutter create --platforms=android
├── lib/
│   ├── main.dart
│   ├── core/
│   │   ├── api/api_client.dart       # Dio + interceptor (token, detail → toast, 401 → logout)
│   │   ├── auth/                     # auth_repository.dart (abstrata + Api), auth_provider.dart
│   │   ├── router/app_router.dart    # rotas de contracts/navigation.md
│   │   ├── services/                 # notification_service, audio_player_service, file_share_service
│   │   ├── storage/secure_storage.dart
│   │   └── theme/                    # identidade visual do Sumi
│   ├── features/
│   │   ├── shell/                    # drawer com os 5 menus + barra de etapas da produção
│   │   ├── auth/login_screen.dart
│   │   ├── home/                     # Início
│   │   ├── projects/                 # lista + projects_repository.dart
│   │   ├── library/                  # lista + form de personagem + characters_repository.dart
│   │   ├── series/                   # series_repository.dart
│   │   ├── voice_test/               # voices_repository.dart + minimax_voices.dart
│   │   └── production/
│   │       ├── production_step.dart  # enum + regra de derivação (data-model)
│   │       ├── idea/  characters/  scenarios/  script/
│   │       ├── review/  editor/  finalize/  video/
│   │       ├── panels_repository.dart
│   │       └── scenarios_repository.dart
│   └── shared/                       # widgets reutilizados de verdade (capa, chip de filtro, estado vazio)
└── test/
    ├── core/
    └── features/
```

**Structure Decision**: novo projeto `sumi-mobile/` ao lado de `sumi-api/` e `sumi-web/`, com a
estrutura `lib/core` + `lib/features` + `lib/shared` da skill. Cada pasta de feature contém sua
tela, seu controller Riverpod e o arquivo do repositório (abstração + implementação Dio no mesmo
arquivo, por serem pequenos). Repositórios usados por mais de uma feature (`characters`,
`projects`) ficam na feature dona e são importados pelas outras.

## Entrega por fatias (ordem da spec)

1. **P1 — US1**: projeto base, login, shell com drawer, Início.
2. **P2 — US2**: Projetos (lista).
3. **P2 — US2b**: produção, em sub-fatias: Ideia → Personagens → Cenários → Roteiro → Revisão →
   Editor → Finalizar → Vídeo; exclusão de projeto.
4. **P2 — US3**: Biblioteca com criação/edição (reusa a tela de personagem da produção).
5. **P3 — US4**: Séries.
6. **P3 — US5**: Teste de Voz.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Reescrever as telas do web em Flutter (vs. Capacitor) | Escolha explícita do dono do projeto | Capacitor reaproveitaria o Angular, mas foi recusado |
| 4 pacotes além da skill (R9) | Áudio, vídeo e compartilhamento são requisitos (US5, FR-007b) | Não há equivalente no SDK Flutter |
| `SecureStorage` sem abstração (Princípio III cita "armazenamento") | Decisão do dono do projeto: a abstração vale para os dados de domínio que existiam no web; o storage local só guarda sessão (token, usuário, ID do projeto em produção), dados efêmeros cuja fonte é o servidor | Interface `SessionStorage` — sem segunda implementação nem ganho de teste que justifique; recomenda-se registrar essa interpretação na constituição (PATCH) |
| Rota nova no `sumi-api` (`POST /auth/refresh`) | Spec exige renovar a sessão sem intervenção | Par access/refresh token da skill — tabela e rotação desnecessárias |