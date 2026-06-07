"""
test_analyzer.py
----------------
Tests unitarios del FundamentalAnalyzer.
No requieren credenciales — usan datos en memoria.
"""

import pytest
from src.analyzer import FundamentalAnalyzer, Signal, Stock


@pytest.fixture
def analyzer():
    return FundamentalAnalyzer()


@pytest.fixture
def sample_data():
    """Conjunto de tickers simulados con perfiles distintos."""
    return [
        # Value + quality → BUY
        {
            "ticker": "TGS", "sector": "Energía", "price_usd": 9.0,
            "p_e_forward": 7.5, "p_bv": 0.75, "roe": 0.19,
            "margen_neto": 0.25, "ev_ebitda": 5.8, "market_cap_usd_billions": 4.5,
        },
        # Quality → BUY
        {
            "ticker": "PAM", "sector": "Energía", "price_usd": 55.0,
            "p_e_forward": 8.0, "p_bv": 1.20, "roe": 0.15,
            "margen_neto": 0.18, "ev_ebitda": 6.0, "market_cap_usd_billions": 11.0,
        },
        # HOLD
        {
            "ticker": "GGAL", "sector": "Bancos", "price_usd": 5.03,
            "p_e_forward": 3.31, "p_bv": 1.29, "roe": 0.009,
            "margen_neto": 0.011, "ev_ebitda": 5.0, "market_cap_usd_billions": 8.1,
        },
        # SELL (caro y poca rentabilidad)
        {
            "ticker": "MIRG", "sector": "Otros", "price_usd": 3.0,
            "p_e_forward": 25.0, "p_bv": 2.0, "roe": 0.03,
            "margen_neto": 0.02, "ev_ebitda": 18.0, "market_cap_usd_billions": 0.5,
        },
        # AVOID (pérdidas)
        {
            "ticker": "TXAR", "sector": "Materiales", "price_usd": 1.5,
            "p_e_forward": 0.0, "p_bv": 0.70, "roe": -0.10,
            "margen_neto": -0.08, "ev_ebitda": 12.0, "market_cap_usd_billions": 1.2,
        },
    ]


# ------------------------------------------------------------------
# Señales
# ------------------------------------------------------------------

class TestSignals:

    def test_value_play_is_buy(self, analyzer):
        """P/BV bajo + ROE sólido → BUY"""
        s = analyzer.from_dict({
            "ticker": "TEST", "sector": "X", "price_usd": 1.0,
            "p_e_forward": 5.0, "p_bv": 0.6, "roe": 0.10,
            "margen_neto": 0.08, "ev_ebitda": 4.0, "market_cap_usd_billions": 1.0,
        })
        assert analyzer.signal(s) == Signal.BUY

    def test_quality_play_is_buy(self, analyzer):
        """ROE > 12% + P/BV < 1.5 → BUY"""
        s = analyzer.from_dict({
            "ticker": "TEST", "sector": "X", "price_usd": 10.0,
            "p_e_forward": 8.0, "p_bv": 1.3, "roe": 0.18,
            "margen_neto": 0.15, "ev_ebitda": 6.0, "market_cap_usd_billions": 5.0,
        })
        assert analyzer.signal(s) == Signal.BUY

    def test_expensive_weak_roe_is_sell(self, analyzer):
        """P/BV alto + ROE bajo → SELL"""
        s = analyzer.from_dict({
            "ticker": "TEST", "sector": "X", "price_usd": 5.0,
            "p_e_forward": 20.0, "p_bv": 2.0, "roe": 0.02,
            "margen_neto": 0.01, "ev_ebitda": 14.0, "market_cap_usd_billions": 2.0,
        })
        assert analyzer.signal(s) == Signal.SELL

    def test_negative_roe_is_avoid(self, analyzer):
        """ROE negativo → AVOID"""
        s = analyzer.from_dict({
            "ticker": "TEST", "sector": "X", "price_usd": 2.0,
            "p_e_forward": 0.0, "p_bv": 0.8, "roe": -0.15,
            "margen_neto": -0.10, "ev_ebitda": 8.0, "market_cap_usd_billions": 0.5,
        })
        assert analyzer.signal(s) == Signal.AVOID

    def test_balanced_is_hold(self, analyzer):
        """Valuación y rentabilidad normales → HOLD"""
        s = analyzer.from_dict({
            "ticker": "TEST", "sector": "X", "price_usd": 5.0,
            "p_e_forward": 10.0, "p_bv": 1.1, "roe": 0.07,
            "margen_neto": 0.06, "ev_ebitda": 7.0, "market_cap_usd_billions": 3.0,
        })
        assert analyzer.signal(s) == Signal.HOLD


# ------------------------------------------------------------------
# Ranking
# ------------------------------------------------------------------

class TestRanking:

    def test_rank_returns_all_stocks(self, analyzer, sample_data):
        stocks = [analyzer.from_dict(d) for d in sample_data]
        ranked = analyzer.rank(stocks)
        assert len(ranked) == len(sample_data)

    def test_rank_sorted_descending(self, analyzer, sample_data):
        stocks = [analyzer.from_dict(d) for d in sample_data]
        ranked = analyzer.rank(stocks)
        scores = [sc for _, _, sc in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_top_is_buy_signal(self, analyzer, sample_data):
        """El top rankeado debe ser BUY en estos datos."""
        stocks = [analyzer.from_dict(d) for d in sample_data]
        ranked = analyzer.rank(stocks)
        top_stock, top_signal, _ = ranked[0]
        assert top_signal == Signal.BUY

    def test_avoid_at_bottom(self, analyzer, sample_data):
        """AVOID debe estar al final del ranking."""
        stocks = [analyzer.from_dict(d) for d in sample_data]
        ranked = analyzer.rank(stocks)
        last_signal = ranked[-1][1]
        assert last_signal == Signal.AVOID


# ------------------------------------------------------------------
# Reporte completo
# ------------------------------------------------------------------

class TestReport:

    def test_report_has_required_keys(self, analyzer, sample_data):
        report = analyzer.generate_report(sample_data)
        for key in ("analysis_date", "top_3", "full_matrix", "alerts", "summary"):
            assert key in report

    def test_top_3_length(self, analyzer, sample_data):
        report = analyzer.generate_report(sample_data)
        assert len(report["top_3"]) == 3

    def test_summary_totals(self, analyzer, sample_data):
        report = analyzer.generate_report(sample_data)
        s = report["summary"]
        assert s["total"] == len(sample_data)
        assert s["buy"] + s["hold"] + s["sell"] + s["avoid"] == s["total"]

    def test_alerts_contain_avoid_or_sell(self, analyzer, sample_data):
        """Si hay AVOID/SELL en los datos, deben aparecer en las alertas."""
        report = analyzer.generate_report(sample_data)
        # Hay 1 AVOID (TXAR) y 1 SELL (MIRG) en sample_data
        assert len(report["alerts"]) >= 2

    def test_matrix_all_tickers(self, analyzer, sample_data):
        report = analyzer.generate_report(sample_data)
        tickers_in_matrix = {s["ticker"] for s in report["full_matrix"]}
        tickers_in_data   = {d["ticker"] for d in sample_data}
        assert tickers_in_matrix == tickers_in_data


# ------------------------------------------------------------------
# Score
# ------------------------------------------------------------------

class TestScore:

    def test_score_zero_pbv(self, analyzer):
        """P/BV = 0 no rompe."""
        s = analyzer.from_dict({
            "ticker": "X", "sector": "X", "price_usd": 1.0,
            "p_e_forward": 0.0, "p_bv": 0.0, "roe": 0.1,
            "margen_neto": 0.0, "ev_ebitda": 0.0, "market_cap_usd_billions": 0.0,
        })
        assert analyzer.score(s) == 0.0

    def test_score_higher_for_better_stock(self, analyzer):
        """Un stock con mayor ROE y menor P/BV debe tener mayor score."""
        better = analyzer.from_dict({
            "ticker": "A", "sector": "X", "price_usd": 1.0,
            "p_e_forward": 5.0, "p_bv": 0.5, "roe": 0.20,
            "margen_neto": 0.15, "ev_ebitda": 4.0, "market_cap_usd_billions": 2.0,
        })
        worse = analyzer.from_dict({
            "ticker": "B", "sector": "X", "price_usd": 1.0,
            "p_e_forward": 15.0, "p_bv": 2.0, "roe": 0.04,
            "margen_neto": 0.03, "ev_ebitda": 12.0, "market_cap_usd_billions": 0.5,
        })
        assert analyzer.score(better) > analyzer.score(worse)
