# Quickstart: validar o cadastro de IA por tipo

## Pré-requisitos

- Postgres local com o banco do Sumi e o `.env` atual (o mesmo usado hoje).
- Usuário administrador.
- Pelo menos uma chave válida (OpenAI, BytePlus ou MiniMax).

## 1. Migração e conversão (FR-014, SC-003)

```powershell
cd C:\Git\comic-prompt\sumi-api
uv run alembic upgrade head
```

**Esperado**:
- As tabelas `ai_*_config` existem e `app_settings` não existe mais.
- Em cada tabela, uma linha por fornecedor que tinha chave, e a ativa corresponde ao provider que
  estava em uso.

Verificar com SQL:

```sql
select 'text' t, name, kind, model, active from ai_text_config
union all select 'image', name, kind, model, active from ai_image_config
union all select 'stt', name, kind, model, active from ai_transcription_config
union all select 'voice', name, kind, model, active from ai_voice_config
union all select 'video', name, kind, model, active from ai_video_config;
```

## 2. Subir API e web

```powershell
cd C:\Git\comic-prompt\sumi-api; uv run uvicorn prompt_clinica.main:app --reload
cd C:\Git\comic-prompt\sumi-web; npm start
```

Abrir `http://localhost:4200/app-settings` logado como admin.

## 3. Cenários

| # | Ação | Esperado |
|---|---|---|
| 1 | Aba Texto: Nova configuração, Tipo OpenAI-compatível, URL BytePlus, chave, modelo `seed-…`, Salvar | Nova linha inativa no grid |
| 2 | Testar na nova linha | Resposta "ok", modelo e ms, ou o erro da BytePlus |
| 3 | Ligar o interruptor da nova linha | Ela fica ativa e a anterior desliga sem recarregar a página |
| 4 | Gerar uma sinopse num projeto | O texto vem do modelo ByteDance (log da API mostra o modelo) |
| 5 | Editar a linha sem preencher a chave e trocar o modelo | A chave continua (mesmo `…xxxx`) e o modelo muda |
| 6 | Tentar excluir a linha ativa | Botão desabilitado com a dica |
| 7 | Desligar a ativa e gerar uma sinopse | Mensagem "Nenhuma IA de texto ativa…" |
| 8 | Popup: marcar "Ativa" ao criar uma configuração Anthropic | Ela vira a ativa; a sinopse sai do Claude |
| 9 | Aba Imagem: testar Seedream | A imagem de amostra aparece |
| 10 | Gerar o retrato de um personagem com Seedream ativo | Retrato gerado (as referências continuam funcionando) |
| 11 | Aba Transcrição: Testar, falar e parar | O texto transcrito aparece |
| 12 | Aba Voz: Testar | O áudio toca |
| 13 | Aba Vídeo: Testar | "Conexão OK" ou erro de autenticação |

## 4. Varredura de configuração específica (SC-006)

```powershell
cd C:\Git\comic-prompt\sumi-api
rg -n "OPENAI_API_KEY|MINIMAX_(API_KEY|BASE_URL|GROUP_ID|\w+_MODEL)|BYTEPLUS_|SEEDREAM_MODEL|STT_(MODEL|LANGUAGE)|AI_(TEXT|IMAGE)_|AI_PROVIDER" src
```

**Esperado**: nenhum resultado. A migração em `alembic/versions/` é a única exceção, e
`*_PAYLOAD_LOG` não aparece nesse padrão.

## 5. Testes automatizados

```powershell
cd C:\Git\comic-prompt\sumi-api; uv run pytest tests/test_ai_config.py -q
```

Cobrem: no máximo uma ativa por tabela, ativar pelo PATCH desativa a anterior, excluir a ativa
→ 409, `api_key: null` mantém a chave, e `kind` inválido → 422.
