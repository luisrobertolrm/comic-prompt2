# Specs — Sumi (comic-prompt)

Telas mapeadas a partir dos arquivos em `comic-prompt/src/`.

---

## Autenticação (`screens-auth.jsx`)

- **AuthScreen** — Tela de login/cadastro dividida em dois painéis (brand hero à esquerda, formulário à direita). Suporta os modos `login` e `register`, validação de campos, "lembrar de mim", recuperação de senha e login via Google/Convidado.

### Entidades

| Entidade | Tabela | Descrição |
|---|---|---|
| `User` | `users` | Conta de usuário. Suporta senha local e OAuth. |
| `UserOAuth` | `user_oauth` | Vínculo com provedor externo (Google, Convidado). |
| `PasswordResetToken` | `password_reset_tokens` | Token de recuperação gerado via "Esqueceu a senha?". |
| `UserSession` | `user_sessions` | Sessão persistente criada pelo "Lembrar de mim". |

#### `users`

| Coluna | Tipo PG | Restrições | Notas |
|---|---|---|---|
| `id` | `UUID` | PK, `gen_random_uuid()` | |
| `name` | `VARCHAR(120)` | NOT NULL | Obrigatório no cadastro; derivado do e-mail no login |
| `email` | `VARCHAR(255)` | NOT NULL, UNIQUE, INDEX | Sempre em lowercase |
| `password_hash` | `VARCHAR(255)` | NULL | `NULL` para contas OAuth-only |
| `plan` | `VARCHAR(60)` | NOT NULL | default `'Plano criador'` |
| `terms_accepted_at` | `TIMESTAMPTZ` | NULL | Preenchido ao aceitar o checkbox |
| `email_verified` | `BOOLEAN` | NOT NULL | default `false` |
| `is_active` | `BOOLEAN` | NOT NULL | default `true` — soft-delete |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | server default `now()` |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | server default `now()`, atualizado via Python |

#### `user_oauth`

| Coluna | Tipo PG | Restrições | Notas |
|---|---|---|---|
| `id` | `UUID` | PK, `gen_random_uuid()` | |
| `user_id` | `UUID` | FK → `users.id` ON DELETE CASCADE | |
| `provider` | `VARCHAR(30)` | NOT NULL | `'google'` \| `'guest'` |
| `provider_uid` | `VARCHAR(255)` | NOT NULL | UID retornado pelo provedor |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | server default `now()` |
| — | UNIQUE | `(provider, provider_uid)` | Impede vínculo duplicado |

#### `password_reset_tokens`

| Coluna | Tipo PG | Restrições | Notas |
|---|---|---|---|
| `id` | `UUID` | PK, `gen_random_uuid()` | |
| `user_id` | `UUID` | FK → `users.id` ON DELETE CASCADE | |
| `token_hash` | `VARCHAR(255)` | NOT NULL | SHA-256 do token enviado por e-mail |
| `expires_at` | `TIMESTAMPTZ` | NOT NULL | TTL de 1 h a partir da criação |
| `used_at` | `TIMESTAMPTZ` | NULL | Preenchido ao resgatar o token |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | server default `now()` |

#### `user_sessions`

| Coluna | Tipo PG | Restrições | Notas |
|---|---|---|---|
| `id` | `UUID` | PK, `gen_random_uuid()` | Valor armazenado no cookie |
| `user_id` | `UUID` | FK → `users.id` ON DELETE CASCADE | |
| `token_hash` | `VARCHAR(255)` | NOT NULL | SHA-256 do cookie para validação |
| `expires_at` | `TIMESTAMPTZ` | NOT NULL | 30 dias quando "Lembrar de mim" ativo |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | server default `now()` |

---

## Home (`screens-home.jsx`)

- **Home** — Lista de projetos do usuário com filtros por status (Todos, Rascunho, Roteiro, Em revisão, Concluído) e alternância entre visualização em grade e lista. Exibe seção de personagens recentes da biblioteca.
- **ProjectCard** — Card de projeto na visualização em grade, com capa temática, título, gênero, status e avatares do elenco.
- **ProjectList** — Linha de projeto na visualização em lista (tabela compacta).
- **NewProjectTile** — Tile "Começar uma nova história" no grid de projetos.
- **CharacterMiniCard** — Mini-card de personagem na seção da biblioteca na Home.

---

## Criação de projeto (`screens-create.jsx`)

- **NewProject** *(Etapa 1 de 5)* — Formulário de ideia inicial: campo de texto livre com sugestões, seleção de gênero, tom emocional, número de páginas, idioma dos balões e estilo visual.
- **CharactersScreen** *(Etapa 2 de 5)* — Elenco da história. Três abas:
  - **LibraryGrid** — Selecionar personagens existentes da biblioteca.
  - **ManualForm** — Criar personagem manualmente (nome, papel, idade, altura, descrição visual, figurino, traços de personalidade).
  - **AIGenerate** — Gerar personagem com IA via prompt livre ou formulário por atributos; exibe 4 retratos candidatos para escolha e confirmação.

---

## Roteiro e revisão (`screens-story.jsx`)

- **Script** *(Etapa 3 de 5)* — A IA propõe o storyboard (lista de quadros). Exibe sinopse, elenco, grade de cards de storyboard com shimmer de carregamento, opção de regerar tudo.
- **Review** *(Etapa 4 de 5)* — Revisão quadro a quadro. Inclui barra de progresso navegável, visualização ampliada do quadro, direção de cena editável, editor de balões (fala/pensamento/grito), prompt visual editável, aprovação individual e regeração por quadro.

---

## Editor visual e exportação (`screens-editor.jsx`)

- **Editor** *(Editor visual)* — Composição da página. Troca de layout (Mangá vertical / Grade ocidental / Dinâmico mangá), reordenação de quadros, balões arrastáveis (drag & drop) sobre os quadros, painel lateral com lista de quadros e sentido de leitura.
- **Final** *(Etapa 5 de 5)* — Visualização final da HQ completa (capa + páginas compostas). Resumo com contagens e opções de exportação: PDF, PNG por quadro, EPUB, link de compartilhamento e geração de vídeo narrado.
- **LibraryScreen** — Biblioteca completa de personagens com busca por nome e filtros por papel (Protagonistas, Coadjuvantes, Mascotes).

---

## Vídeo narrado (`screens-video.jsx`)

- **VideoScreen** *(Saída em vídeo — Motion Comic)* — Player de motion comic: cada quadro vira uma cena com narração e vozes por personagem. Inclui:
  - **VideoStage** — Palco de exibição do quadro atual com transições (corte, fade, zoom lento/Ken Burns, deslize) e legenda on-screen.
  - **NarrationBar** — Barra de onda de narração ativa/muda.
  - **Transport** — Controles de reprodução: play/pause, cena anterior/próxima, seek bar, velocidade (0.75×–2×).
  - **SceneTimeline** — Filmstrip horizontal de todas as cenas com timestamp.
  - **VoiceRow** — Linha do elenco de voz: seleção de voz sintética e mute por personagem.
