<#
.SYNOPSIS
  Sube los secretos del .env a GitHub Secrets del repo.

.DESCRIPTION
  Lee el .env local y crea/actualiza los secrets que necesita el workflow
  .github/workflows/merval-daily.yml usando la CLI de GitHub (gh).

  Requiere:
    - gh CLI instalada y autenticada:  winget install GitHub.cli ; gh auth login
    - Ejecutarse desde la raíz del repo (donde está .env)

  Salta automáticamente valores placeholder ("required_in_cowork", "*XXX*").

.EXAMPLE
  .\setup_secrets.ps1
#>

$ErrorActionPreference = "Stop"

# Secrets que consume el workflow merval-daily.yml
$required = @(
    "ANTHROPIC_API_KEY",
    "ALPHACAST_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID"
)

# --- Validaciones ---
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "No se encontró 'gh'. Instalá con: winget install GitHub.cli ; gh auth login"
    exit 1
}

$envPath = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envPath)) {
    Write-Error "No se encontró .env en $envPath"
    exit 1
}

# --- Parsear .env (KEY=VALUE, ignora comentarios y líneas vacías) ---
$vars = @{}
foreach ($line in Get-Content $envPath) {
    $trimmed = $line.Trim()
    if ($trimmed -eq "" -or $trimmed.StartsWith("#")) { continue }
    $idx = $trimmed.IndexOf("=")
    if ($idx -lt 1) { continue }
    $key = $trimmed.Substring(0, $idx).Trim()
    $val = $trimmed.Substring($idx + 1).Trim()
    $vars[$key] = $val
}

# --- Subir secrets ---
$placeholders = @("required_in_cowork", "")
$uploaded = 0
foreach ($name in $required) {
    if (-not $vars.ContainsKey($name)) {
        Write-Warning "[$name] no está en .env — omitido"
        continue
    }
    $value = $vars[$name]
    if (($placeholders -contains $value) -or ($value -like "*XXX*")) {
        Write-Warning "[$name] tiene valor placeholder ('$value') — completá .env primero. Omitido."
        continue
    }
    Write-Host "Subiendo secret: $name ..." -NoNewline
    gh secret set $name --body $value
    if ($?) {
        Write-Host " OK" -ForegroundColor Green
        $uploaded++
    } else {
        Write-Host " FALLO" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "$uploaded secret(s) subidos. Verificá con: gh secret list" -ForegroundColor Cyan
