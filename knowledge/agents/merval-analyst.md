---
type: agent
name: Merval Analyst
status: planned
---

# 🤖 Agente: Merval Analyst

Agente que responde preguntas del cliente sobre el panel líder del Merval,
leyendo este grafo de conocimiento como contexto.

## Rol
Analista cuantitativo del mercado argentino. Da respuestas accionables
(no solo datos) sobre valuación y rentabilidad de las acciones del [[panel-lider]].

## Conocimiento que consume
- Skill: [[fundamental-analysis]]
- Reglas: [[signal-rules]]
- Dominio: notas de `domain/tickers/` y `domain/sectors/`

## Capacidades (objetivo)
- Responder "¿cómo está GGAL?", "¿qué bancos comprar?", "compará energía vs bancos".
- Citar la señal (BUY/HOLD/SELL/AVOID) y el porqué según [[signal-rules]].

## Canales
- Fase web (hecha): reporte estático en Vercel.
- Fase Telegram: [[daily-report]].
- Fase interactiva: este agente sobre Telegram / web.

## Modelo
Model-agnostic. Para costo bajo: Claude Haiku o Gemini. El grafo no depende del modelo.
