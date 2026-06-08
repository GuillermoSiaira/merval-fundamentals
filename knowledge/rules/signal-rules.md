---
type: rules
name: Signal Rules
implemented_in: src/analyzer.py
---

# 📏 Reglas de Señales

Reglas que aplica la skill [[fundamental-analysis]]. Orden de evaluación:

1. **AVOID** si `ROE < -5%` (pérdidas).
2. **AVOID** si `EV/EBITDA > 15` **y** `ROE < 12%` (valuación extrema sin sustento).
3. **BUY (value)** si `P/BV < 0.8` **y** `ROE > 5%`.
4. **BUY (quality)** si `ROE > 12%` **y** `P/BV < 1.5`.
5. **SELL** si `P/BV > 1.5` **y** `ROE < 5%` (caro y poco rentable).
6. **HOLD** en cualquier otro caso.

## Score
`score = ROE / P·BV` — ordena el ranking de mayor a menor.

## Umbrales (configurables en `src/analyzer.py`)
| Constante | Valor |
|---|---|
| P_BV_VALUE_MAX | 0.8 |
| P_BV_SELL_MIN / P_BV_QUALITY_MAX | 1.5 |
| ROE_VALUE_MIN / ROE_WEAK_MAX | 5% |
| ROE_GOOD_MIN | 12% |
| ROE_AVOID_MAX | -5% |
| EV_EBITDA_MAX | 15 |
