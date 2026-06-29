#!/usr/bin/env bash
# Instalacao da aplicacao Sumi no Debian / CasaOS via Docker.
# Uso (na raiz do projeto):  bash install-debian.sh
# Se o Docker exigir privilegio:  sudo bash install-debian.sh
set -euo pipefail
cd "$(dirname "$0")"

echo
echo "== Instalacao Sumi (Debian / Docker) =="
echo

# 1. Docker instalado?
if ! command -v docker >/dev/null 2>&1; then
  echo "[ERRO] Docker nao encontrado."
  echo "Instale com o script oficial e rode este de novo:"
  echo "  curl -fsSL https://get.docker.com | sudo sh"
  exit 1
fi

# 2. docker compose v2 disponivel?
if ! docker compose version >/dev/null 2>&1; then
  echo "[ERRO] 'docker compose' (v2) nao disponivel."
  echo "Instale o plugin:  sudo apt-get install -y docker-compose-plugin"
  exit 1
fi

# 3. Consigo falar com o daemon?
if ! docker info >/dev/null 2>&1; then
  echo "[ERRO] Nao consigo acessar o Docker (rodando? permissao?)."
  echo "Tente:  sudo bash install-debian.sh"
  exit 1
fi

# 4. Rede compartilhada (uma vez)
if ! docker network inspect shared-db >/dev/null 2>&1; then
  echo "Criando rede compartilhada 'shared-db'..."
  docker network create shared-db >/dev/null
fi

# 5. Arquivos .env (Postgres e Sumi)
NEED_EDIT=0

if [ ! -f postgres/.env ]; then
  cp postgres/.env.example postgres/.env
  echo "[ATENCAO] postgres/.env criado. Defina POSTGRES_PASSWORD (senha forte)."
  NEED_EDIT=1
fi

if [ ! -f .env ]; then
  cp .env.production.example .env
  echo "[ATENCAO] .env criado. Preencha (use a MESMA senha do postgres/.env):"
  echo "  - POSTGRES_PASSWORD  (igual a postgres/.env)"
  echo "  - JWT_SECRET_KEY"
  echo "  - OPENAI_API_KEY     (ou outro provider de IA)"
  echo
  echo "Sugestao de JWT_SECRET_KEY:"
  echo "  $(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  NEED_EDIT=1
fi

if [ "$NEED_EDIT" -eq 1 ]; then
  echo
  echo "Edite os .env e rode de novo:  bash install-debian.sh"
  exit 0
fi

# 6. Sobe o Postgres (stack separada)
echo "Subindo o Postgres..."
docker compose -f postgres/docker-compose.yml up -d

# 7. Build + up da sumi (migrations rodam no command do compose)
echo "Buildando e subindo a sumi (o primeiro build demora)..."
docker compose up -d --build

echo
echo "Pronto!"
echo "  App:      http://localhost:8000/"
echo "  Docs:     http://localhost:8000/docs"
echo "  Postgres: localhost:5432"
echo
echo "Logs:  docker compose logs -f api"
