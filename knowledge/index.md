---
type: index
name: Merval AI OS
---

# Merval AI OS — Mapa de Contenido

Base de conocimiento **estructurada para consumo por IA** (model-agnostic):
markdown legible por humanos, interconectado con enlaces `[[...]]`.

> Abrí **esta carpeta** (`knowledge/`) como *vault* en Obsidian para ver el grafo.

## Entidades (entity types)
- 🤖 Agente: [[merval-analyst]]
- 🧠 Skill: [[fundamental-analysis]]
- 📏 Reglas: [[signal-rules]]
- ⚙️ Workflows: [[daily-report]] · [[publish-web]]

## Dominio
- 📊 [[panel-lider]] — las 20 acciones
- Sectores y tickers: ver carpeta `domain/` (se generan con `python tools/build_kg.py`)

## Capas del AI OS
1. **Conocimiento** (esto) — el grafo en `knowledge/`.
2. **Automatización** — n8n (refresh datos → web → Telegram).
3. **Agentes** — orquestación del [[merval-analyst]] sobre este grafo.
