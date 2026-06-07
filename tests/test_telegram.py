"""
test_telegram.py
----------------
Tests para TelegramNotifier y ReportGenerator.

Los tests de formato no necesitan credenciales.
Los tests de envío real se saltan si no hay TELEGRAM_BOT_TOKEN.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from src.report_generator import ReportGenerator
from src.telegram_notifier import TelegramNotifier
from src.analyzer import FundamentalAnalyzer

# Datos hardcoded — no requieren Anthropic SDK ni credenciales
_RAW_DATA = [
    {"ticker": "TGS",  "sector": "Energía",    "price_usd": 9.0,  "p_e_forward": 7.5,  "p_bv": 0.75, "roe": 0.19, "margen_neto": 0.25, "ev_ebitda": 5.8,  "market_cap_usd_billions": 4.5},
    {"ticker": "PAM",  "sector": "Energía",    "price_usd": 55.0, "p_e_forward": 8.0,  "p_bv": 1.20, "roe": 0.15, "margen_neto": 0.18, "ev_ebitda": 6.0,  "market_cap_usd_billions": 11.0},
    {"ticker": "GGAL", "sector": "Bancos",     "price_usd": 5.03, "p_e_forward": 3.31, "p_bv": 1.29, "roe": 0.009,"margen_neto": 0.011,"ev_ebitda": 5.0,  "market_cap_usd_billions": 8.1},
    {"ticker": "YPF",  "sector": "Energía",    "price_usd": 18.0, "p_e_forward": 6.5,  "p_bv": 0.85, "roe": 0.085,"margen_neto": 0.06, "ev_ebitda": 3.2,  "market_cap_usd_billions": 7.0},
    {"ticker": "MIRG", "sector": "Otros",      "price_usd": 3.0,  "p_e_forward": 25.0, "p_bv": 2.0,  "roe": 0.03, "margen_neto": 0.02, "ev_ebitda": 18.0, "market_cap_usd_billions": 0.5},
    {"ticker": "TXAR", "sector": "Materiales", "price_usd": 1.5,  "p_e_forward": 0.0,  "p_bv": 0.70, "roe": -0.10,"margen_neto": -0.08,"ev_ebitda": 12.0, "market_cap_usd_billions": 1.2},
]


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def sample_report():
    """Reporte generado a partir de datos hardcoded — sin credenciales."""
    return FundamentalAnalyzer().generate_report(_RAW_DATA)


@pytest.fixture
def gen():
    return ReportGenerator()


# ------------------------------------------------------------------
# ReportGenerator — Telegram
# ------------------------------------------------------------------

class TestTelegramMessage:

    def test_message_is_string(self, gen, sample_report):
        msg = gen.telegram_message(sample_report)
        assert isinstance(msg, str)

    def test_message_contains_top3(self, gen, sample_report):
        msg = gen.telegram_message(sample_report)
        for opp in sample_report["top_3"]:
            assert opp["ticker"] in msg

    def test_message_contains_signals(self, gen, sample_report):
        msg = gen.telegram_message(sample_report)
        for sig in ("BUY", "HOLD", "SELL", "AVOID"):
            # Al menos uno de los 4 debe aparecer
            pass  # no todos aparecen siempre; chequeamos BUY/HOLD que son comunes
        assert "BUY" in msg or "HOLD" in msg

    def test_message_not_empty(self, gen, sample_report):
        msg = gen.telegram_message(sample_report)
        assert len(msg) > 100

    def test_message_contains_summary(self, gen, sample_report):
        msg = gen.telegram_message(sample_report)
        assert "RESUMEN" in msg or "resumen" in msg.lower()


# ------------------------------------------------------------------
# ReportGenerator — HTML
# ------------------------------------------------------------------

class TestHTMLReport:

    def test_html_is_string(self, gen, sample_report):
        html = gen.html_report(sample_report)
        assert isinstance(html, str)

    def test_html_contains_doctype(self, gen, sample_report):
        html = gen.html_report(sample_report)
        assert "<!DOCTYPE html>" in html

    def test_html_contains_all_tickers(self, gen, sample_report):
        html = gen.html_report(sample_report)
        for stock in sample_report["full_matrix"]:
            assert stock["ticker"] in html

    def test_html_has_table(self, gen, sample_report):
        html = gen.html_report(sample_report)
        assert "<table>" in html


# ------------------------------------------------------------------
# TelegramNotifier — instanciación
# ------------------------------------------------------------------

class TestNotifierInit:

    def test_raises_without_credentials(self):
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            TelegramNotifier(bot_token="", chat_id="")

    def test_ok_with_credentials(self):
        n = TelegramNotifier(bot_token="123:ABC", chat_id="-100123")
        assert n.bot_token == "123:ABC"
        assert n.chat_id == "-100123"


# ------------------------------------------------------------------
# TelegramNotifier — mocked HTTP
# ------------------------------------------------------------------

class TestNotifierMocked:

    @patch("requests.post")
    def test_send_message_calls_api(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        n = TelegramNotifier(bot_token="123:ABC", chat_id="-100")
        result = n.send_message("Hola")
        assert result is True
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_send_message_returns_false_on_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=400, text="Bad Request")
        n = TelegramNotifier(bot_token="123:ABC", chat_id="-100")
        # Fallaría también el retry sin parse_mode
        mock_post.return_value = MagicMock(status_code=400, text="Bad Request")
        result = n.send_message("Hola", parse_mode="")
        assert result is False

    @patch("requests.get")
    def test_connection_test_ok(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"result": {"username": "testbot", "first_name": "Test"}},
        )
        mock_get.return_value.raise_for_status = lambda: None
        n = TelegramNotifier(bot_token="123:ABC", chat_id="-100")
        assert n.test_connection() is True

    @patch("requests.get")
    