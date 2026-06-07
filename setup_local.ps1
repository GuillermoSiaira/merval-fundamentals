# ============================================================
# setup_local.ps1
# Setup completo de Merval Fundamentals en Windows
# Ejecutar como: .\setup_local.ps1
# ============================================================

Write-Host "🚀 Merval Fundamentals - Setup Local" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# --- 1. Verificar Python ---
Write-Host "`n[1/6] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python no encontrado. Instalá Python 3.11+ desde https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "✅ $pythonVersion" -ForegroundColor Green

# --- 2. Crear entorno virtual ---
Write-Host "`n[2/6] Creando entorno virtual..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "✅ venv creado" -ForegroundColor Green
} else {
    Write-Host "✅ venv ya existe" -ForegroundColor Green
}

# Activar venv
.\venv\Scripts\Activate.ps1
Write-Host "✅ venv activado" -ForegroundColor Green

# --- 3. Instalar dependencias ---
Write-Host "`n[3/6] Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt -q
Write-Host "✅ Dependencias instaladas" -ForegroundColor Green

# --- 4. Verificar .env ---
Write-Host "`n[4/6] Verificando .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  .env creado desde .env.example" -ForegroundColor Yellow
    Write-Host "   → Editá .env con tus credenciales reales antes de continuar" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env existe" -ForegroundColor Green
}

# Cargar variables del .env
Get-Content .env | ForEach-Object {
    if ($_ -match "^([^#=]+)=(.+)$") {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# --- 5. Verificar credenciales ---
Write-Host "`n[5/6] Verificando credenciales..." -ForegroundColor Yellow

$allOk = $true

if ($env:ALPHACAST_API_KEY -and $env:ALPHACAST_API_KEY -ne "alphacast_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX") {
    Write-Host "✅ ALPHACAST_API_KEY configurada" -ForegroundColor Green
} else {
    Write-Host "❌ ALPHACAST_API_KEY no configurada → editá .env" -ForegroundColor Red
    $allOk = $false
}

if ($env:TELEGRAM_BOT_TOKEN -and $env:TELEGRAM_BOT_TOKEN -ne "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh") {
    Write-Host "✅ TELEGRAM_BOT_TOKEN configurada" -ForegroundColor Green
} else {
    Write-Host "❌ TELEGRAM_BOT_TOKEN no configurada → editá .env" -ForegroundColor Red
    $allOk = $false
}

if ($env:TELEGRAM_CHAT_ID -and $env:TELEGRAM_CHAT_ID -ne "-1001234567890") {
    Write-Host "✅ TELEGRAM_CHAT_ID configurada" -ForegroundColor Green
} else {
    Write-Host "❌ TELEGRAM_CHAT_ID no configurada → editá .env" -ForegroundColor Red
    $allOk = $false
}

# --- 6. Tests ---
Write-Host "`n[6/6] Corriendo tests locales (sin credenciales)..." -ForegroundColor Yellow
pytest tests/test_analyzer.py -v -q 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Tests del analyzer OK" -ForegroundColor Green
} else {
    Write-Host "❌ Tests fallaron - revisá la instalación" -ForegroundColor Red
}

# --- Resumen ---
Write-Host "`n=====================================" -ForegroundColor Cyan
if ($allOk) {
    Write-Host "✅ Setup completo. Listo para correr." -ForegroundColor Green
    Write-Host "`n   Próximos pasos:" -ForegroundColor White
    Write-Host "   1. Instalar MCP AlphaCast en Claude Desktop (ver README)" -ForegroundColor White
    Write-Host "   2. Deploy a GCP: cd gcp && bash deploy.sh" -ForegroundColor White
    Write-Host "   3. Activar scheduler en Cowork" -ForegroundColor White
} else {
    Write-Host "⚠️  Setup incompleto. Completá las credenciales en .env" -ForegroundColor Yellow
    Write-Host "   Volvé a correr este script después de completar .env" -ForegroundColor Yellow
}
Write-Host "=====================================" -ForegroundColor Cyan
