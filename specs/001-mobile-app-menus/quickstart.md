# Quickstart: validar o app Sumi Android

## Pré-requisitos

- Flutter 3.41+ (`flutter doctor` sem erros para Android).
- Aparelho Android (ou emulador) com depuração USB.
- `sumi-api` rodando e acessível pelo aparelho (IP da LAN, não `localhost`; no emulador,
  `10.0.2.2`).
- Uma conta aprovada no Sumi com pelo menos 1 projeto, 1 personagem e 1 série criados pelo web.

## Rodar

```powershell
cd sumi-mobile
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://<IP-DA-API>:<PORTA>
```

APK de teste: `flutter build apk --debug --dart-define=API_BASE_URL=...`

## Cenários de validação (mapeados à spec)

| # | Passos | Resultado esperado | Spec |
|---|---|---|---|
| 1 | Abrir o app, logar | Início mostra os mesmos projetos e personagens recentes do web em < 30 s | US1, SC-001, SC-003 |
| 2 | Fechar e reabrir o app | Volta logado ao Início em ≤ 3 s | FR-001, SC-002 |
| 3 | Abrir o menu em qualquer tela | Itens Início, Projetos, Biblioteca, Séries, Teste de Voz; atual destacado | FR-002, SC-004 |
| 4 | Projetos: alternar grade/lista e filtrar status | Lista muda mantendo o filtro | US2 |
| 5 | Nova HQ → Ideia … Finalizar | Cada etapa marca concluída e abre a próxima; HQ final igual no web | US2b, SC-006 |
| 6 | Na etapa Revisão, minimizar o app durante a geração de imagens e voltar | Imagens aparecem sem recarregar manualmente | FR-007a |
| 7 | Fechar o app no meio do Roteiro, reabrir e abrir o projeto | Volta ao Roteiro com os dados salvos | SC-007 |
| 8 | Editor: arrastar um balão e abrir no web | Posição igual no web | R8, FR-010 |
| 9 | Finalizar/Vídeo: compartilhar | Folha de compartilhamento do Android com o ZIP/vídeo | FR-007b |
| 10 | Excluir projeto digitando o código | Projeto some do app e do web | US2b |
| 11 | Biblioteca: buscar, filtrar, criar personagem com retrato e aprovar | Aparece no web como aprovado | US3, FR-008 |
| 12 | Séries: criar, vincular 2 projetos, editar, excluir | Reflete no web; projetos continuam existindo | US4 |
| 13 | Teste de Voz: pesquisar voz, gerar texto ≤ 300 caracteres, salvar | Áudio toca em ≤ 15 s; voz salva listada | US5, SC-005 |
| 14 | Modo avião em qualquer tela | Mensagem "Sem conexão com o servidor." e opção de tentar de novo | Edge cases |
| 15 | Login com conta admin | Nenhum menu de administração aparece | Edge cases |
| 16 | Criar HQ, parar em Personagens sem salvar seleção, reabrir pelo Início | Abre em Personagens; Roteiro e seguintes não são tocáveis | R6, data-model |
| 17 | Abrir o app com token válido e conferir `exp` do token salvo | `exp` renovado para ~30 dias à frente | R4, casos-limite |

Contratos de referência: [contracts/api-consumed.md](contracts/api-consumed.md),
[contracts/navigation.md](contracts/navigation.md), [data-model.md](data-model.md).
