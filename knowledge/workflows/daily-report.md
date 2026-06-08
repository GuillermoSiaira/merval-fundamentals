---
type: workflow
name: Daily Report
schedule: "Lun/Mié/Vie 08:00 ART"
status: parcial
---

# ⚙️ Workflow: Reporte Diario

Genera y distribuye el análisis del [[panel-lider]].

## Pasos
1. Obtener datos del panel (hoy: `data/merval_panel.csv`; futuro: API REST de Alphacast).
2. Aplicar [[fundamental-analysis]] → señales + ranking + alertas.
3. Formatear reporte (Markdown para Telegram + HTML para web).
4. Distribuir: web ([[publish-web]]) y Telegram (pendiente: falta `TELEGRAM_CHAT_ID`).

## Implementación
`run_analysis.py`. Orquestación futura con n8n (Capa 2 del [[index|AI OS]]).
