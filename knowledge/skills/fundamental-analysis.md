---
type: skill
name: Fundamental Analysis
implemented_in: src/analyzer.py
---

# 🧠 Skill: Análisis Fundamental

Convierte métricas de una acción en una **señal accionable** y un ranking.
Usada por el [[merval-analyst]] sobre las acciones del [[panel-lider]].

## Entradas (por acción)
`price_usd`, `p_e_forward`, `p_bv`, `roe`, `margen_neto`, `ev_ebitda`,
`market_cap_usd_billions`.

## Salidas
- **Señal**: BUY / HOLD / SELL / AVOID (según [[signal-rules]]).
- **Score**: `ROE / P·BV` (mayor = mejor relación calidad/precio).
- **Rationale**: explicación en texto.

## Implementación
Código en `src/analyzer.py` (clase `FundamentalAnalyzer`). El grafo y el código
comparten la misma lógica: las notas de `domain/tickers/` se generan con
`python tools/build_kg.py`, que aplica esta skill.
