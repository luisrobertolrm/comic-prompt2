# Research: Aplicativo móvel Sumi (Flutter)

Base: skill `flutter-app-skill-cc` (`C:\Git\skills\flutter-app-skill-cc\SKILL.md`), escolhida pelo
dono do projeto. Cada item abaixo registra onde o app segue a skill e onde precisa adaptá-la à
API FastAPI existente (`sumi-api/`), que não segue o contrato `dotnet-api-skill-cc`.

## R1. Tecnologia do app

- **Decision**: Flutter 3.41 (stable, já instalado), estrutura `lib/core` + `lib/features` +
  `lib/shared`, Riverpod, Dio, go_router, flutter_secure_storage — padrão da skill.
- **Rationale**: escolha explícita do usuário; padrão já usado em outros apps dele.
- **Alternatives considered**: Capacitor empacotando `sumi-web` (reuso total, menos trabalho) —
  rejeitado pelo usuário.

## R2. Plataformas

- **Decision**: somente Android (`flutter create --platforms=android`).
- **Rationale**: spec define Android; o padrão Android+Windows da skill não traz valor aqui e
  exigiria testar um segundo alvo.
- **Alternatives considered**: Android + Windows (padrão da skill) — fora do escopo da spec.

## R3. Contrato de resposta da API (desvio da skill)

- **Decision**: o interceptor Dio **não** desembrulha `{ data, messages }` e **não** lê
  ProblemDetails. A API FastAPI devolve o JSON direto no sucesso e, no erro, `{ "detail": str }`
  ou `{ "detail": [ { "loc", "msg", ... } ] }` (validação 422). O interceptor converte `detail`
  em toast via `NotificationService` (mantido da skill) e mostra "Sem conexão com o servidor."
  para falhas de rede. `extra: {'silent': true}` continua suprimindo toasts em polling.
- **Rationale**: a API já está em produção para o web; mudar o contrato do backend está fora do
  escopo (spec: "não há regra de negócio nova").
- **Alternatives considered**: adaptar o backend ao envelope da skill — quebraria o web.

## R4. Autenticação (desvio da skill)

- **Decision**: login por e-mail e senha em `POST /auth/login` com `remember: true` (token de 30
  dias, `JWT_REMEMBER_EXPIRE_MINUTES=43200`). Só o `access_token` e o `user` são guardados no
  secure storage. **Renovação deslizante**: novo endpoint `POST /auth/refresh` no `sumi-api`,
  protegido por `get_current_user`, que devolve um `TokenResponse` novo de 30 dias. No bootstrap
  o app lê o claim `exp`: expirado → login; válido → chama `/auth/refresh` (silent) e salva o
  token novo; se a renovação falhar por rede, segue com o token atual. 401 em qualquer chamada →
  limpa storage e volta ao login. Sem refresh token separado e sem Google Sign-In.
- **Rationale**: atende "renova sem intervenção" (spec, casos-limite) com o menor acréscimo
  possível no backend — uma rota de ~6 linhas que reusa `create_access_token`. Quem abre o app ao
  menos uma vez a cada 30 dias nunca precisa logar de novo.
- **Alternatives considered**: par access/refresh token da skill — exige tabela/rotação de
  refresh tokens, complexidade sem ganho aqui; guardar senha para relogar — inseguro.

## R5. Programar para abstrações (Constituição, Princípio III)

- **Decision**: cada feature declara um repositório como `abstract class` (ex.:
  `ProjectsRepository`) e uma implementação `Api…Repository` com Dio. O provider Riverpod é
  tipado pela abstração: `Provider<ProjectsRepository>((ref) => ApiProjectsRepository(...))`.
  Telas e controllers só conhecem a abstração. Recursos nativos seguem o mesmo padrão
  (`AudioPlayerService`, `FileShareService`).
- **Rationale**: exigido pela constituição; permite testes com implementação falsa por override
  de provider, sem mocks de Dio.
- **Escopo da abstração**: vale para os dados de domínio que já existem no web (projetos,
  quadros, personagens, cenários, séries, vozes, estilos, auth) e para recursos nativos com
  troca plausível (áudio, compartilhamento). O `SecureStorage` local guarda apenas dados de sessão
  (token, usuário, ID do projeto em produção) — dados efêmeros cuja fonte é o servidor — e fica
  como classe concreta, por decisão do dono do projeto (registrado no plan.md).
- **Alternatives considered**: services concretos como na skill (`AuthApi`) — viola o Princípio III.
  Camadas `data/domain/presentation` com casos de uso — rejeitado (Princípio IV): uma abstração
  por repositório basta.

## R6. Etapa em que o projeto parou

- **Decision**: o app só pula para uma etapa se todas as anteriores já foram feitas, inferindo
  o que foi feito a partir dos dados existentes (regra em data-model, ProductionStep). O projeto é
  criado no servidor ao concluir a **Ideia**, como no web (`new-project.component.ts`); o ID do
  projeto em produção fica em memória + secure storage (equivalente ao `sessionStorage` do web).
- **Rationale**: atende "abre na etapa em que parou" sem mudar a API. O web hoje sempre abre em
  Roteiro.
- **Alternatives considered**: campo `current_step` no projeto — mudança de schema e de web.

## R7. Gerações por IA demoradas (FR-007a)

- **Decision**: os jobs assíncronos do backend (`portrait-job`, `scene-job`, `export/video/{job}`)
  são consultados por polling a cada 2 s enquanto a tela está visível; ao voltar ao app
  (`AppLifecycleState.resumed`) ou à tela, o app consulta de novo. As gerações síncronas
  (`synopsis/generate`, `panels/generate`, `panels/generate-images`, `bubbles/generate`) usam
  `receiveTimeout` de 10 min; se o app for fechado no meio, o servidor termina o trabalho e a
  tela recarrega os quadros ao reabrir.
- **Rationale**: sem infraestrutura nova (push, WorkManager); o trabalho já roda no servidor.
- **Alternatives considered**: notificações push ao concluir — fora do escopo; WorkManager —
  complexidade sem ganho, pois o processamento não está no aparelho.

## R8. Editor em tela de toque

- **Decision**: mesma lógica do web (layouts de página, balões com posição `x`/`y` em %), com
  arrasto por `GestureDetector`/`onPanUpdate` e `InteractiveViewer` para zoom da página. O
  salvamento do balão ocorre ao soltar o dedo (`onPanEnd`), como o `mouseup` do web.
- **Rationale**: mantém os dados compatíveis com o web (FR-010).
- **Alternatives considered**: editor simplificado só com lista — não cumpre SC-006.

## R9. Pacotes extras além da skill

| Pacote | Uso |
|---|---|
| `just_audio` | tocar o áudio do Teste de Voz e de narração |
| `video_player` | pré-visualizar o vídeo final |
| `share_plus` | salvar/compartilhar ZIP da HQ e vídeo (a folha de compartilhamento inclui "Salvar em arquivos") |
| `path_provider` | arquivo temporário antes de compartilhar |

- **Alternatives considered**: `cached_network_image` — adiado; `Image.network` basta para o MVP.

## R10. Imagens e arquivos

- **Decision**: imagens vêm de `GET /storage/{key}` (rota pública), carregadas com
  `Image.network`. Downloads binários (ZIP, áudio, vídeo) usam `ResponseType.bytes` com
  `silent: true`.

## R11. Testes

- **Decision**: `flutter_test` com widget tests por feature, sobrescrevendo os providers de
  repositório por implementações falsas (`ProviderScope(overrides: [...])`); `flutter analyze` sem
  avisos; validação manual em aparelho físico via `quickstart.md`.
