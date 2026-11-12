param(
    [string]$ApiBaseUrl = 'http://10.0.2.2:8000',
    [ValidateSet('debug', 'release')]
    [string]$Mode = 'debug'
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$freeGb = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
if ($freeGb -lt 2) {
    Write-Error "Só $freeGb GB livres em C:. O build precisa de pelo menos 2 GB."
}

flutter pub get
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

flutter build apk "--$Mode" "--dart-define=API_BASE_URL=$ApiBaseUrl"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$apk = Join-Path $PSScriptRoot "build\app\outputs\flutter-apk\app-$Mode.apk"
Write-Host ''
Write-Host "APK gerado: $apk"
Write-Host "API: $ApiBaseUrl"
