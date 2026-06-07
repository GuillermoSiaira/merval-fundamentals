# 📊 Merval Fundamentals

Análisis fundamental automático del **panel líder S&P Merval (20 acciones)** → reporte diario vía Telegram.

**Stack:** Claude (MCP AlphaCast) · GCP Cloud Functions · GitHub Actions · Telegram  
**Frecuencia:** Lunes, Miércoles y Viernes a las 08:00 ART  
**Repo:** https://github.com/GuillermoSiaira/merval-fundamentals

---

## ⚡ Setup rápido (3 pasos)

### 1. Clonar y configurar entorno

```powershell
git clone https://github.com/GuillermoSiaira/merval-fundamentals.git
cd merval-fundamentals

# Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Copiar y completar variables de entorno
copy .env.example .env
# → Editá .env con tus credenciales reales
```

### 2. Instalar MCP AlphaCast en Claude Desktop

Agregá esto a tu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "alphacast": {
      "type": "url",
      "url": "https://mcp.alphacast.io",
      "headers": {
        "Authorization": "Bearer TU_ALPHACAST_API_KEY"
      }
    }
  }
}
```

📍 Ubicación del config en Windows:
`%APPDATA%\Claude\claude_desktop_config.json`

### 3. Ejecutar setup completo

```powershell
# Configura variables de entorno del sistema y valida credenciales
.\setup_local.ps1
```

---

## 🏗️ Arquitectura

```
Cowork Scheduler (Lun/Mié/Vie 08:00 ART)
        │
        ▼
Claude + MCP AlphaCast
        │  obtiene datos fundamentales (20 tickers)
        ▼
GCP Cloud Function
        │  analiza, genera reporte, guarda en Firestore
        ▼
Telegram Bot → Grupo/Chat del cliente
```

---

## 📁 Estructura

```
merval-fundamentals/
├── src/
│   ├── alphacast_client.py   # Cliente MCP AlphaCast
│   ├── analyzer.py           # Lógica análisis fundamental
│   ├── report_generator.py   # Genera mensajes Telegram + HTML
│   └── telegram_notifier.py  # Envía a Telegram
├── gcp/
│   ├── cloud_function.py     # Entry point GCP
│   ├── requirements.txt      # Deps para Cloud Function
│   └── deploy.sh             # Script de deploy
├── cowork/
│   ├── prompt.md             # Prompt maestro para Cowork
│   └── config.json           # Config del scheduler
├── tests/
│   ├── test_alphacast.py
│   ├── test_analyzer.py
│   └── test_telegram.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── TROUBLESHOOTING.md
├── .github/workflows/
│   ├── tests.yml             # CI en cada PR
│   └── deploy.yml            # Deploy a GCP en merge a main
├── .env.example
├── setup_local.ps1           # Setup Windows automatizado
└── requirements.txt
```

---

## 🎯 Panel Merval (20 acciones)

| Sector | Tickers |
|--------|---------|
| Bancos | GGAL, BMA, BBAR, SUPV, VALO |
| Energía | YPF, PAM, TGS, TGSU, PAMP |
| Utilities | CEPU, EDN |
| Materiales | TXAR, ALUA, LOMA, HARG |
| Telecom | TECO2 |
| Agro/Otros | CRES, BYMA, MIRG |

---

## 🔑 Credenciales necesarias

| Servicio | Cómo obtenerla |
|----------|---------------|
| `ALPHACAST_API_KEY` | https://www.alphacast.io/settings/api-keys |
| `TELEGRAM_BOT_TOKEN` | @BotFather en Telegram → `/newbot` |
| `TELEGRAM_CHAT_ID` | `https://api.telegram.org/bot{TOKEN}/getUpdates` |
| GCP Service Account | https://console.cloud.google.com/iam-admin/serviceaccounts |

---

## 🧪 Tests

```powershell
# Correr todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ -v --cov=src --cov-report=html
```

---

## 🚀 Deploy a GCP

```bash
cd gcp
chmod +x deploy.sh
./deploy.sh
```

---

## 📋 Checklist pre-producción

- [ ] `.env` completado con credenciales reales
- [ ] MCP AlphaCast instalado en Claude Desktop
- [ ] `pytest tests/ -v` → todos en verde
- [ ] Cloud Function deployada (`./gcp/deploy.sh`)
- [ ] Telegram bot responde al test de conexión
- [ ] Cowork scheduler activo (Lun/Mié/Vie 08:00 ART)
- [ ] Primer reporte recibido en Telegram ✅

---

*Generado automáticamente · GuillermoSiaira · Junio 2026*
