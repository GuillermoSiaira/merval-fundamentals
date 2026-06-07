# Arquitectura — Merval Fundamentals

## Diagrama de flujo

```
┌─────────────────────────────────────────────────────────┐
│                   COWORK SCHEDULER                       │
│         Lun / Mié / Vie  08:00 ART                       │
└───────────────────────┬─────────────────────────────────┘
                        │  trigger
                        ▼
┌─────────────────────────────────────────────────────────┐
│              CLAUDE + MCP ALPHACAST                      │
│                                                          │
│  • Consulta 20 tickers del panel Merval                  │
│  • MCP AlphaCast → datos fundamentales en tiempo real    │
│    (P/E, P/BV, ROE, EV/EBITDA, Market Cap, Precio USD)   │
└───────────────────────┬─────────────────────────────────┘
                        │  raw_data (JSON)
                        ▼
┌─────────────────────────────────────────────────────────┐
│              GCP CLOUD FUNCTION                          │
│           merval-analysis (Python 3.11)                  │
│                                                          │
│  src/analyzer.py                                         │
│    • Genera señales BUY / HOLD / SELL / AVOID            │
│    • Score = ROE / P·BV (ranking)                        │
│    • Top 3 oportunidades                                 │
│    • Alertas de sobrevaluación / pérdidas                │
│                                                          │
│  src/report_generator.py                                 │
│    • Mensaje Markdown para Telegram                      │
│    • Reporte HTML completo                               │
└──────────┬────────────────────────┬─────────────────────┘
           │                        │
           ▼                        ▼
┌─────────────────┐      ┌──────────────────────┐
│  TELEGRAM BOT   │      │  GOOGLE FIRESTORE    │
│                 │      │                      │
│  • Mensaje con  │      │  Collection:         │
│    Top 3 +      │      │  merval_reports      │
│    alertas      │      │                      │
│  • Adjunto HTML │      │  • Histórico diario  │
└─────────────────┘      │  • top_3, summary,   │
                         │    alerts, timestamp │
                         └──────────────────────┘
```

## Componentes

### AlphaCast MCP
- URL: `https://mcp.alphacast.io`
- Autenticación: Bearer token (API key)
- Claude actúa como intermediario: recibe instrucciones de Cowork, llama al MCP, devuelve JSON

### GCP Cloud Function
- Runtime: Python 3.11
- Región: `southamerica-east1` (Buenos Aires)
- Memoria: 512 MB
- Timeout: 300 segundos
- Trigger: HTTP (llamado por Cowork/Claude)
- Variables de entorno almacenadas en GCP Secrets

### Firestore
- Mode: Native
- Región: `southamerica-east1`
- Colección: `merval_reports`
- Retención: indefinida (ideal limpiar > 1 año)

### GitHub Actions
- `tests.yml`: corre en cada PR — tests sin credenciales
- `deploy.yml`: auto-deploy a GCP en cada merge a `main`

## Flujo de datos detallado

```
AlphaCast MCP
  └── Por ticker devuelve:
      { ticker, price_usd, p_e_forward, p_bv, roe,
        margen_neto, ev_ebitda, market_cap_usd_billions }

FundamentalAnalyzer
  └── Por ticker calcula:
      signal  = f(p_bv, roe, ev_ebitda)
      score   = roe / p_bv
  └── Genera:
      top_3, full_matrix, alerts, summary, sector_stats

ReportGenerator
  └── telegram_message → MarkdownV2 (≈ 800 chars)
  └── html_report → archivo HTML completo

TelegramNotifier
  └── sendMessage (texto)
  └── sendDocument (HTML adjunto)
```

## Seguridad

- Credenciales NUNCA en código — siempre en `.env` (local) o GCP Secrets (producción)
- `.gitignore` excluye `.env`, `*.key`, `service-account.json`
- GitHub Secrets para CI/CD: `GCP_SA_KEY`, `ALPHACAST_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- Cloud Function permite invocaciones no autenticadas (HTTP público) — considerar agregar auth en producción si es necesario
