# Tela — Login (`AuthScreen` modo `login`)

## Visão geral

Tela de entrada no estúdio. Divide o viewport em dois painéis lado a lado. O painel esquerdo é a vitrine da marca (estático, igual em login e cadastro). O painel direito contém o formulário, que alterna entre os modos `login` e `register` sem recarregar a página.

---

## Layout

```
┌──────────────────────────────┬────────────────────────────┐
│  Painel Esquerdo  (1.05fr)   │  Painel Direito  (0.95fr)  │
│  brand / hero                │  formulário                 │
└──────────────────────────────┴────────────────────────────┘
```

`minHeight: 100vh` · `display: grid` · `grid-template-columns: 1.05fr 0.95fr`

---

## Painel esquerdo — Brand Hero

Compartilhado entre login e cadastro; nunca muda.

| Elemento | Conteúdo |
|---|---|
| Fundo | `--accent-soft` + padrão de pontos radial (opacidade 0.5) |
| Logotipo | Ícone `墨` (38 × 38 px) + wordmark **Sumi** (24 px) |
| Eyebrow | `ESTÚDIO DE HQ COM IA` |
| Headline | "Da primeira faísca à página pronta." (46 px, line-height 1.05) |
| Subtexto | "Dê uma ideia, crie seus personagens…" (16 px, max 42 ch) |
| Decoração | 3 mini-cards de quadrinhos sobrepostos, rotacionados −3°/0°/+3° |
| Rodapé | `© 2026 Sumi Studio · feito para criadores de mangá` |

### Mini-cards decorativos

| Índice | Padrão de tela | Avatar |
|---|---|---|
| 0 | `dots` (radial, 6 px) | Inicial "Y" (Yumi) |
| 1 | `diag` (diagonal 45°, 6 px) | Inicial "R" (Ren) |
| 2 | `dense` (radial, 4 px) | — |

---

## Painel direito — Formulário de Login

### Seletor de modo (tabs)

Pill container com dois botões de largura igual (`flex: 1`):

| Botão | `id` | Estado ativo |
|---|---|---|
| **Entrar** | `login` | selecionado (fundo `--paper-3`, borda `--ink`, peso 600) |
| Criar conta | `register` | inativo (fundo transparente, peso 400) |

Trocar de tab limpa todos os erros.

### Cabeçalho

| Elemento | Texto |
|---|---|
| `<h2>` (28 px) | "Bem-vinda de volta." |
| Subtexto muted | "Continue de onde parou no seu estúdio." |

### Campos do formulário

| # | Label | Tipo HTML | `autocomplete` | Placeholder | Estado inicial |
|---|---|---|---|---|---|
| 1 | **E-mail** | `email` | `email` | `voce@exemplo.com` | vazio |
| 2 | **Senha** | `password` | `current-password` | `••••••••` | vazio |

### Opções abaixo dos campos

```
[ ✓ ] Lembrar de mim          Esqueceu a senha? →
```

| Elemento | Comportamento |
|---|---|
| Checkbox "Lembrar de mim" | Marcado por padrão (`remember: true`). Quando ativo, gera `UserSession` com TTL de 30 dias. |
| Link "Esqueceu a senha?" | Clique previne navegação (`preventDefault`). Deve abrir fluxo de recuperação (tela/modal a definir). |

### Botão de envio

> **Entrar no estúdio** — `type="submit"`, kind `primary`, tamanho `lg`, largura 100%.

### Divisor OAuth

```
────────────  ou continue com  ────────────
```

### Botões OAuth

| Botão | Ícone | Provedor | payload simulado |
|---|---|---|---|
| **Google** | SVG Google multicolor (15 px) | `google` | `{ name: "Maya Tanaka", email: "maya@gmail.com", plan: "Plano criador" }` |
| **Convidado** | ícone `users` (15 px) | `guest` | `{ name: "Maya Tanaka", email: "maya@exemplo.com", plan: "Plano criador" }` |

### Rodapé do formulário

> "Ainda não tem conta? **Crie agora**"
>
> Clique em "Crie agora" muda o modo para `register` e limpa os erros.

---

## Validação

A validação ocorre no cliente antes de qualquer chamada de rede. Erros são exibidos abaixo de cada campo em vermelho (`#b3503f`, 11.5 px). O envio é bloqueado enquanto houver erros.

| Campo | Regra | Mensagem de erro |
|---|---|---|
| E-mail | `/^\S+@\S+\.\S+$/` | "E-mail inválido." |
| Senha | `length >= 6` | "Mínimo de 6 caracteres." |

### Comportamento pós-validação bem-sucedida

1. Nenhum erro → chama `onAuth(payload)`.
2. `name` é derivado do e-mail: `email.split("@")[0]` com pontos/hifens/underscores trocados por espaços e cada palavra capitalizada.
   - Exemplo: `maya.tanaka@x.com` → `"Maya Tanaka"`
3. `plan` fixo: `"Plano criador"`.

---

## Estados do formulário

| Estado | Descrição |
|---|---|
| Inicial | Campos vazios, `remember: true`, sem erros |
| Erro de validação | Mensagens vermelhas abaixo dos campos inválidos; envio bloqueado |
| Aguardando resposta | Botão desabilitado / loading (a implementar) |
| Autenticado | `onAuth` chamado → redireciona para `Home` |

---

## API — Endpoints esperados

### `POST /auth/login`

**Request body**
```json
{
  "email": "voce@exemplo.com",
  "password": "••••••••",
  "remember": true
}
```

**Response 200**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "<uuid>",
    "name": "Maya Tanaka",
    "email": "voce@exemplo.com",
    "plan": "Plano criador"
  }
}
```

**Response 401**
```json
{ "detail": "Credenciais inválidas." }
```

**Efeito colateral:** Se `remember: true`, cria registro em `user_sessions` com `expires_at = now() + 30 days` e envia cookie `HttpOnly; Secure; SameSite=Strict`.

---

### `POST /auth/oauth/google`

**Request body**
```json
{ "id_token": "<google-id-token>" }
```

**Response 200** — mesmo schema de `/auth/login`.

**Lógica:** Valida o `id_token` com Google, faz upsert em `users` + `user_oauth` (`provider = "google"`).

---

### `POST /auth/oauth/guest`

**Request body** — vazio.

**Response 200**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "<uuid>",
    "name": "Convidado",
    "email": null,
    "plan": "Plano criador"
  }
}
```

**Lógica:** Cria `User` com `email = null`, `password_hash = null`, insere `UserOAuth(provider="guest", provider_uid=<uuid gerado>)`.

---

### `POST /auth/password-reset/request`

**Request body**
```json
{ "email": "voce@exemplo.com" }
```

**Response 200** — sempre `{ "detail": "Se o e-mail existir, enviaremos as instruções." }` (sem revelar existência da conta).

**Lógica:** Gera `PasswordResetToken(token_hash=sha256(token), expires_at=now()+1h)`, envia e-mail com link.

---

## Referências

- Entidades: [`specs.md` → Autenticação → Entidades](../../specs.md)
- Tela de cadastro: [`cadastro.md`](./cadastro.md)
- Componente: `comic-prompt/src/screens-auth.jsx`
