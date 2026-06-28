#Requires -Version 5
# Instalacao da aplicacao Sumi no Windows via Docker Desktop.
# Uso: na raiz do projeto, rode  .\install-windows.ps1

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "== Instalacao Sumi (Windows / Docker Desktop) ==" -ForegroundColor Cyan
Write-Host ""

# 1. Docker instalado?
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Docker nao encontrado." -ForegroundColor Red
    Write-Host "Instale o Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
}

# 2. Docker rodando?
& docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Docker Desktop nao esta rodando." -ForegroundColor Red
    Write-Host "Abra o Docker Desktop, espere o icone ficar verde e rode este script de novo."
    exit 1
}

# 3. .env existe?
if (-not (Test-Path ".env")) {
    Copy-Item ".env.production.example" ".env"
    Write-Host "[ATENCAO] Arquivo .env criado a partir do exemplo." -ForegroundColor Yellow
    Write-Host "Edite o .env e preencha pelo menos:" -ForegroundColor Yellow
    Write-Host "  - POSTGRES_PASSWORD  (senha do banco)"
    Write-Host "  - JWT_SECRET_KEY     (string aleatoria)"
    Write-Host "  - OPENAI_API_KEY     (ou outro provider de IA)"
    Write-Host ""
    Write-Host "Sugestao de JWT_SECRET_KEY:"
    Write-Host ("  " + (-join ((1..64) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })))
    Write-Host ""
    Write-Host "Depois de editar, rode .\install-windows.ps1 de novo." -ForegroundColor Yellow
    exit 0
}

# 4. Build + up + migrations (migrations rodam no command do compose)
Write-Host "Buildando e subindo os containers (o primeiro build demora)..." -ForegroundColor Cyan
& docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Falha ao subir os containers. Veja a saida acima." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Pronto!" -ForegroundColor Green
Write-Host "  App:  http://localhost:8000/"
Write-Host "  Docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "Logs:  docker compose logs -f api"
