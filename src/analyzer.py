"""
analyzer.py
-----------
Lógica de análisis fundamental del panel Merval.

Genera:
  - Señales BUY / HOLD / SELL / AVOID por ticker
  - Ranking por score ROE/P·BV
  - Matriz P/BV vs ROE
  - Alertas de sobrevaluación o pérdidas
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pytz

logger = logging.getLogger(__name__)

ART = pytz.timezone("America/Argentina/Buenos_Aires")


class Signal(str, Enum):
    BUY  = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    AVOID = "AVOID"


@dataclass
class Stock:
    ticker: str
    sector: str
    price_usd: float
    p_e: float
    p_bv: float
    roe: float
    margen_neto: float
    ev_ebitda: float
    market_cap_usd_billions: float
    timestamp: str = ""


class FundamentalAnalyzer:
    """
    Analiza stocks fundamentalmente y genera señales + ranking.

    Lógica de señales
    -----------------
    BUY:
      - Value play: P/BV < 0.8  y ROE > 5%
      - Quality play: ROE > 12% y P/BV < 1.5
    SELL:
      - P/BV > 1.5  y ROE < 5%   (caro y rentabilidad débil)
    AVOID:
      - ROE < -5%  (pérdidas)
      - EV/EBITDA > 15  (valuación extrema sin sustento)
    HOLD:
      - Todo lo demás
    """

    # ---- Thresholds configurables ----
    P_BV_VALUE_MAX   = 0.8
    P_BV_SELL_MIN    = 1.5
    P_BV_QUALITY_MAX = 1.5
    ROE_WEAK_MAX     = 0.05   # < 5%  → señal negativa
    ROE_GOOD_MIN     = 0.12   # > 12% → quality play
    ROE_VALUE_MIN    = 0.05   # > 5%  → value play
    ROE_AVOID_MAX    = -0.05  # < -5% → pérdidas
    EV_EBITDA_MAX    = 15.0

    def from_dict(self, data: Dict) -> Stock:
        return Stock(
            ticker=data["ticker"],
            sector=data.get("sector", "Otros"),
            price_usd=data["price_usd"],
            p_e=data.get("p_e_forward", 0.0),
            p_bv=data.get("p_bv", 0.0),
            roe=data.get("roe", 0.0),
            margen_neto=data.get("margen_neto", 0.0),
            ev_ebitda=data.get("ev_ebitda", 0.0),
            market_cap_usd_billions=data.get("market_cap_usd_billions", 0.0),
            timestamp=data.get("timestamp", ""),
        )

    def signal(self, s: Stock) -> Signal:
        if s.roe < self.ROE_AVOID_MAX:
            return Signal.AVOID
        if s.ev_ebitda > self.EV_EBITDA_MAX and s.roe < self.ROE_GOOD_MIN:
            return Signal.AVOID
        if s.p_bv < self.P_BV_VALUE_MAX and s.roe > self.ROE_VALUE_MIN:
            return Signal.BUY
        if s.roe > self.ROE_GOOD_MIN and s.p_bv < self.P_BV_QUALITY_MAX:
            return Signal.BUY
        if s.p_bv > self.P_BV_SELL_MIN and s.roe < self.ROE_WEAK_MAX:
            return Signal.SELL
        return Signal.HOLD

    def score(self, s: Stock) -> float:
        """ROE / P·BV — mayor = mejor relación calidad/precio."""
        if s.p_bv <= 0:
            return 0.0
        return round(s.roe / s.p_bv, 6)

    def rank(self, stocks: List[Stock]) -> List[Tuple[Stock, Signal, float]]:
        """Devuelve lista ordenada por score descendente."""
        return sorted(
            [(s, self.signal(s), self.score(s)) for s in stocks],
            key=lambda x: x[2],
            reverse=True,
        )

    def rationale(self, s: Stock, sig: Signal) -> str:
        roe_pct = f"{s.roe * 100:.1f}%"
        p_bv    = f"{s.p_bv:.2f}x"
        if sig == Signal.BUY:
            if s.p_bv < self.P_BV_VALUE_MAX:
                return f"Value play: P/BV bajo ({p_bv}) + ROE sólido ({roe_pct})"
            return f"Quality play: ROE alto ({roe_pct}) a valuación razonable ({p_bv})"
        if sig == Signal.SELL:
            return f"Caro ({p_bv}) con rentabilidad débil (ROE {roe_pct})"
        if sig == Signal.AVOID:
            return f"ROE negativo/muy bajo ({roe_pct}) — evitar hasta recuperación"
        return f"Valuación y rentabilidad equilibradas (P/BV {p_bv}, ROE {roe_pct})"

    # ------------------------------------------------------------------
    # Reporte completo
    # ------------------------------------------------------------------

    def generate_report(self, raw_data: List[Dict]) -> Dict:
        """
        Acepta lista de dicts de AlphaCastClient y devuelve el reporte completo.
        """
        stocks = [self.from_dict(d) for d in raw_data]
        ranked = self.rank(stocks)

        now_art = datetime.now(ART).isoformat()

        # Top 3
        top_3 = []
        for i, (s, sig, sc) in enumerate(ranked[:3]):
            top_3.append({
                "rank": i + 1,
                "ticker": s.ticker,
                "sector": s.sector,
                "price_usd": round(s.price_usd, 2),
                "p_e": round(s.p_e, 2),
                "p_bv": round(s.p_bv, 2),
                "roe": f"{s.roe * 100:.1f}%",
                "ev_ebitda": round(s.ev_ebitda, 1),
                "market_cap_b": round(s.market_cap_usd_billions, 2),
                "signal": sig.value,
                "score": sc,
                "rationale": self.rationale(s, sig),
            })

        # Matriz completa
        matrix = [
            {
                "ticker": s.ticker,
                "sector": s.sector,
                "p_bv": round(s.p_bv, 2),
                "roe_pct": round(s.roe * 100, 1),
                "p_e": round(s.p_e, 2),
                "ev_ebitda": round(s.ev_ebitda, 1),
                "price_usd": round(s.price_usd, 2),
                "market_cap_b": round(s.market_cap_usd_billions, 2),
                "signal": sig.value,
                "score": sc,
            }
            for s, sig, sc in ranked
        ]

        # Alertas
        alerts = []
        for s, sig, _ in ranked:
            if sig == Signal.AVOID:
                alerts.append(
                    f"🔴 {s.ticker}: ROE {s.roe*100:.1f}% — pérdidas o rentabilidad mínima"
                )
            elif sig == Signal.SELL:
                alerts.append(
                    f"🟡 {s.ticker}: Sobrevalorada P/BV {s.p_bv:.2f}x con ROE {s.roe*100:.1f}%"
                )

        # Conteos por sector
        sector_stats: Dict[str, Dict] = {}
        for s, sig, _ in ranked:
            sec = sector_stats.setdefault(s.sector, {"BUY": 0, "HOLD": 0, "SELL": 0, "AVOID": 0})
            sec[sig.value] += 1

        summary = {
            "total": len(stocks),
            "buy":   sum(1 for _, sg, _ in ranked if sg == Signal.BUY),
            "hold":  sum(1 for _, sg, _ in ranked if sg == Signal.HOLD),
            "sell":  sum(1 for _, sg, _ in ranked if sg == Signal.SELL),
            "avoid": sum(1 for _, sg, _ in ranked if sg == Signal.AVOID),
        }

        return {
            "analysis_date": now_art,
            "top_3": top_3,
            "full_matrix": matrix,
            "alerts": alerts,
            "sector_stats": sector_stats,
            "summary": summary,
        }


# --- CLI rápido ---
if __name__ == "__main__":
    from src.alphacast_client import AlphaCastClient, PANEL_LIDER

    client   = AlphaCastClient(simulation_mode=True)
    raw_data = client.get_panel_data()

    analyzer = FundamentalAnalyzer()
    report   = analyzer.generate_report(raw_data)

    print(json.dumps(report, indent=2, ensure_ascii=False))
