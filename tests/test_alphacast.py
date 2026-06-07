"""
test_alphacast.py
-----------------
Tests para AlphaCastClient.

Los tests de simulation_mode no requieren credenciales.
Los tests marcados @pytest.mark.live requieren ALPHACAST_API_KEY real
y se saltan en CI si la variable no está presente.
"""

import os
import pytest
from src.alphacast_client import AlphaCastClient, PANEL_LIDER, SECTOR_MAP


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def sim_client():
    """Cliente en modo simulación — sin credenciales."""
    return AlphaCastClient(simulation_mode=True)


@pytest.fixture
def live_client():
    """Cliente real — se salta si no hay API key."""
    key = os.getenv("ALPHACAST_API_KEY", "")
    if not key or key.startswith("alphacast_XXX"):
        pytest.skip("ALPHACAST_API_KEY no configurada — test live omitido")
    return AlphaCastClient(api_key=key)


# ------------------------------------------------------------------
# Modo simulación
# ------------------------------------------------------------------

class TestSimulationMode:

    def test_get_ticker_returns_dict(self, sim_client):
        data = sim_client.get_ticker_data("GGAL")
        assert isinstance(data, dict)

    def test_ticker_field_matches(self, sim_client):
        data = sim_client.get_ticker_data("YPF")
        assert data["ticker"] == "YPF"

    def test_required_fields_present(self, sim_client):
        data = sim_client.get_ticker_data("GGAL")
        for field in ("ticker", "sector", "price_usd", "p_e_forward", "p_bv",
                      "roe", "margen_neto", "ev_ebitda", "market_cap_usd_billions"):
            assert field in data, f"Campo faltante: {field}"

    def test_price_is_positive(self, sim_client):
        data = sim_client.get_ticker_data("PAM")
        assert data["price_usd"] > 0

    def test_panel_returns_all_tickers(self, sim_client):
        results = sim_client.get_panel_data(PANEL_LIDER)
        assert len(results) == len(PANEL_LIDER)

    def test_unknown_ticker_gets_default_sector(self, sim_client):
        data = sim_client.get_ticker_data("UNKNOWN")
        assert data["sector"] == "Otros"

    def test_sector_map_is_consistent(self, sim_client):
        for ticker in ("GGAL", "YPF", "TGS", "CEPU"):
            data = sim_client.get_ticker_data(ticker)
            assert data["sector"] == SECTOR_MAP[ticker]


# ------------------------------------------------------------------
# Validación de datos
# ------------------------------------------------------------------

class TestValidation:

    def test_valid_data_passes(self, sim_client):
        data = sim_client.get_ticker_data("GGAL")
        assert sim_client.validate_data(data)

    def test_negative_price_fails(self, sim_client):
        bad = {"price_usd": -1, "p_e_forward": 5, "p_bv": 1.0, "roe": 0.1}
        assert not sim_client.validate_data(bad)

    def test_extreme_pbv_fails(self, sim_client):
        bad = {"price_usd": 5, "p_e_forward": 5, "p_bv": 25.0, "roe": 0.1}
        assert not sim_client.validate_data(bad)

    def test_extreme_roe_fails(self, sim_client):
        bad = {"price_usd": 5, "p_e_forward": 5, "p_bv": 1.0, "roe": 5.0}
        assert not sim_client.validate_data(bad)

    def test_all_panel_data_is_valid(self, sim_client):
        results = sim_client.get_panel_data(PANEL_LIDER)
        for d in results:
            assert sim_client.validate_data(d), f"Datos inválidos para {d['ticker']}"


# ------------------------------------------------------------------
# Live tests (requieren credencial real)
# ------------------------------------------------------------------

@pytest.mark.live
class TestLiveAlphaCast:

    def test_ggal_pe_is_reasonable(self, live_client):
        data = live_client.get_ticker_data("GGAL")
        assert data is not None
        assert 1 < data["p_e_forward"] < 20, f"P/E inesperado: {data['p_e_forward']}"

    def test_ypf_price_above_10(self, live_client):
        data = live_client.get_ticker_data("YPF")
        assert data is not None
        assert data["price_usd"] > 10, f"Precio YPF inesperadamente bajo: {data['price_usd']}"

    def test_live_panel_minimum_coverage(self, live_client):
        """Al menos 15 de 20 tickers deben retornar datos válidos en live."""
        results = live_client.get_panel_data(PANEL_LIDER)
        assert len(results) >= 15, f"Solo {len(results)} tickers retornados"
