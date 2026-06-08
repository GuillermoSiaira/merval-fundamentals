"""
build_kg.py
-----------
Genera el grafo de conocimiento (vault de Obsidian) del Merval.

Lee data/merval_panel.csv, calcula la señal de cada acción con el analyzer y
escribe notas markdown interconectadas (wikilinks [[...]]) en knowledge/domain/.
Es "model-agnostic": markdown legible por humanos y estructurado para IA.

Uso:
    python tools/build_kg.py
"""

import sys
import unicodedata
from pathlib import Path

# Permitir importar src/ al correr desde la raíz del repo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.alphacast_client import AlphaCastClient, PANEL_LIDER
from src.analyzer import FundamentalAnalyzer

KN = Path("knowledge")
CSV = "data/merval_panel.csv"


def slug(s: str) -> str:
    """'Energía' -> 'energia'; 'Comm Services' -> 'comm-services'."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.lower().strip().replace(" ", "-")


def main() -> int:
    raw = AlphaCastClient(csv_path=CSV).get_panel_data(PANEL_LIDER)
    analyzer = FundamentalAnalyzer()

    tickers_dir = KN / "domain" / "tickers"
    sectors_dir = KN / "domain" / "sectors"
    tickers_dir.mkdir(parents=True, exist_ok=True)
    sectors_dir.mkdir(parents=True, exist_ok=True)

    sectors: dict[str, list[str]] = {}

    for d in raw:
        stock = analyzer.from_dict(d)
        sig = analyzer.signal(stock)
        sec = d["sector"]
        sectors.setdefault(sec, []).append(d["ticker"])

        note = f"""---
type: ticker
ticker: {d['ticker']}
sector: {sec}
signal: {sig.value}
price_usd: {d['price_usd']}
p_bv: {d['p_bv']}
roe: {d['roe']:.4f}
p_e_forward: {d['p_e_forward']}
ev_ebitda: {d['ev_ebitda']}
market_cap_usd_billions: {d['market_cap_usd_billions']}
---

# {d['ticker']}

- Sector: [[{slug(sec)}]]
- Señal actual: **{sig.value}** — {analyzer.rationale(stock, sig)}
- Analizada con la skill [[fundamental-analysis]] (ver [[signal-rules]])
- Parte del [[panel-lider]]

## Métricas
| Métrica | Valor |
|---|---|
| Precio USD | {d['price_usd']} |
| P/BV | {d['p_bv']} |
| ROE | {d['roe']*100:.1f}% |
| P/E forward | {d['p_e_forward']} |
| EV/EBITDA | {d['ev_ebitda']} |
| Market Cap (B USD) | {d['market_cap_usd_billions']} |
"""
        (tickers_dir / f"{d['ticker']}.md").write_text(note, encoding="utf-8")

    # Notas de sector
    for sec, tks in sectors.items():
        links = "\n".join(f"- [[{t}]]" for t in tks)
        note = f"""---
type: sector
sector: {sec}
---

# Sector: {sec}

Parte del [[panel-lider]]. Acciones analizadas con [[fundamental-analysis]].

## Acciones
{links}
"""
        (sectors_dir / f"{slug(sec)}.md").write_text(note, encoding="utf-8")

    # Nota índice del panel
    sec_links = "\n".join(
        f"- [[{slug(s)}]] ({len(t)})" for s, t in sorted(sectors.items())
    )
    panel = f"""---
type: domain
name: Panel Líder Merval
count: {len(raw)}
---

# Panel Líder Merval

{len(raw)} acciones analizadas fundamentalmente. Entrada del dominio.
Volver al [[index]].

## Sectores
{sec_links}
"""
    (KN / "domain" / "panel-lider.md").write_text(panel, encoding="utf-8")

    print(f"OK: {len(raw)} tickers, {len(sectors)} sectores -> {KN}/domain/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
