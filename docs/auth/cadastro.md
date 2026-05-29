# Tela — Cadastro (`AuthScreen` modo `register`)

## Visão geral

Mesmo componente `AuthScreen` do login, alternado para o modo `register`. O painel esquerdo (brand hero) é idêntico. O painel direito exibe o formulário de criação de conta com quatro campos e aceite de termos.

---

## Layout

```
┌──────────────────────────────┬────────────────────────────┐
│  Painel Esquerdo  (1.05fr)   │  Painel Direito  (0.95fr)  │
│  brand / hero (estático)     │  formulário de cadastro     │
└──────────────────────────────┴────────────────────────────┘
```

`minHeight: 100vh` · `display: grid` · `grid-template-columns: 1.05fr 0.95fr`

---

## Painel esquerdo — Brand Hero

Idêntico ao da tela de login. Ver [`login.md → Painel esquerdo`](./login.md#painel-esquerdo--brand-hero).

---

## Painel direito — Formulário de Cadastro

### Seletor de modo (tabs)

| Botão | `id` | Estado |
|---|---|---|
| Entrar | `login` | inativo |
| **Criar conta** | `register` | selecionado (fundo `--paper-3`, borda `--ink`, peso 600) |

Trocar de tab limpa todos os erros.

### Cabeçalho

| Elemento | Texto |
|---|---|
| `<h2>` (28 px) | "Crie sua conta." |
| Subtexto muted | "Leva menos de um minuto — e o primeiro projeto é grátis." |

### Campos do formulário

| # | Label | Tipo HTML | `autocomplete` | Placeholder | Estado inicial |
|---|---|---|---|---|---|
| 1 | **Nome** | `text` | `name` | "Seu nome ou pseudônimo" | vazio |
| 2 | **E-mail** | `email` | `email` | `voce@exemplo.com` | vazio |
| 3 | **Senha** | `password` | `new-password` | `••••••••` | vazio |
| 4 | **Confirmar senha** | `password` | `new-password` | `••••••••` | vazio |

> O campo **Nome** é exclusivo do modo `register`; não aparece no login.

### Aceite de Termos

```
[ ] Li e aceito os [Termos] e a [Política de Privacidade].
```

| Elemento | Comportamento |
|---|---|
| Checkbox "Termos" | Desmarcado por padrão (`terms: false`). **Obrigatório** para envio. |
| Link "Termos" | `href="#"` com `preventDefault` (destino a definir). |
| Link "Política de Privacidade" | `href="#"` com `preventDefault` (destino a definir). |
| Erro de termos | Exibido abaixo do checkbox em vermelho quando não marcado: "Aceite os termos para continuar." |

### Botão de envio

> **Criar conta e começar** — `type="submit"`, kind `primary`, tamanho `lg`, largura 100%.

### Divisor OAuth

```
────────────  ou continue com  ────────────
```

### Botões OAuth

Idênticos ao login — o cadastro via Google/Convidado não exige formulário.

| Botão | Provedor | Comportamento |
|---|---|---|
| **Google** | `google` | Inicia fluxo OAuth; cria conta se não existir |
| **Convidado** | `guest` | Cria conta anônima sem e-mail |

### Rodapé do formulário

> "Já tem conta? **Entrar**"
>
> Clique em "Entrar" muda o modo para `login` e limpa os erros.

---

## Validação

Todos os erros são verificados de uma vez no `submit`. O envio é bloqueado enquanto houver qualquer erro. Mensagens em vermelho (`#b3503f`, 11.5 px) aparecem abaixo de cada campo.

| Campo | Regra | Mensagem de erro |
|---|---|---|
| Nome | `name.trim()` não vazio | "Como devemos te chamar?" |
| E-mail | `/^\S+@\S+\.\S+$/` | "E-mail inválido." |
| Senha | `length >= 6` | "Mínimo de 6 caracteres." |
| Confirmar senha | `confirm === password` | "As senhas não conferem." |
| Termos | `terms === true` | "Aceite os termos para continuar." |

### Ordem de verificação

```
1. Nome vazio?
2. E-mail inválido?
3. Senha < 6 caracteres?
4. Confirmar senha ≠ Senha?
5. Termos não aceitos?
```

Todos os erros são coletados antes de exibir — o usuário vê todas as pendências de uma vez.

### Comportamento pós-validação bem-sucedida

1. Nenhum erro → chama `onAuth(payload)`.
2. `name` vem diretamente de `form.name.trim()` (não é derivado do e-mail, ao contrário do login).
3. `plan` fixo: `"Plano criador"`.
4. `terms_accepted_at` deve ser registrado com o timestamp do envio.

---

## Estados do formulário

| Estado | Descrição |
|---|---|
| Inicial | Todos os campos vazios; `terms: false`; sem erros |
| Parcialmente preenchido | Campos em edição; sem erros ainda |
| Erro de validação | Mensagens vermelhas abaixo dos campos inválidos; envio bloqueado |
| Aguardando resposta | Botão desabilitado / loading (a implementar) |
| Conta criada | `onAuth` chamado → redireciona para `Home` |
| E-mail já cadastrado | Exibir erro inline no campo e-mail (vindo da API) |

---

## API — Endpoints esperados

### `POST /auth/register`

**Request body**
```json
{
  "name": "Maya Tanaka",
  "email": "voce@exemplo.com",
  "password": "••••••••",
  "terms_accepted": true
}
```

**Response 201**
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

**Response 409** — e-mail já cadastrado
```json
{ "detail": "Este e-mail já está em uso." }
```

**Lógica no backend:**
1. Verificar unicidade do `email` (case-insensitive, salvar em lowercase).
2. Gerar `password_hash` com bcrypt (custo mínimo 12).
3. Criar `User` com `terms_accepted_at = now()`, `email_verified = false`, `is_active = true`.
4. Retornar JWT de acesso + (opcional) cookie de sessão.

---

### `POST /auth/oauth/google`

Mesmo endpoint do login. Se o e-mail Google ainda não existir em `users`, cria a conta automaticamente (sem exigir aceitação de termos — `terms_accepted_at = null` para OAuth).

---

### `POST /auth/oauth/guest`

Mesmo endpoint do login. Conta anônima: `email = null`, sem senha, `provider = "guest"`.

---

## Regras de negócio

| Regra | Detalhe |
|---|---|
| E-mail único | Comparação case-insensitive; salvo em lowercase no banco. |
| Senha mínima | 6 caracteres no cliente. Backend deve exigir no mínimo bcrypt custo 12. |
| Hash de senha | Nunca armazenar texto puro. Usar `bcrypt` ou `argon2`. |
| Aceitação de termos | Registrar timestamp (`terms_accepted_at`) para fins legais. Obrigatório no cadastro por formulário; opcional em OAuth. |
| Verificação de e-mail | `email_verified = false` ao criar. Enviar e-mail de confirmação (fluxo a detalhar). |
| Plano inicial | Sempre `"Plano criador"` ao criar conta. |

---

## Referências

- Entidades: [`specs.md` → Autenticação → Entidades](../../specs.md)
- Tela de login: [`login.md`](./login.md)
- Componente: `comic-prompt/src/screens-auth.jsx`
