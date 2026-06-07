"""
alphacast_client.py
-------------------
Cliente para obtener datos fundamentales del Merval vía MCP AlphaCast + Claude.

Requiere:
  - ALPHACAST_API_KEY en entorno
  - MCP AlphaCast instalado en Claude Desktop (ver README)
"""

import os
import json
import logging
from typing import Dict, List, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Panel líder S&P Merval - 20 acciones
PANEL_LIDER = [
    # Bancos
    "GGAL", "BMA", "BBAR", "SUPV", "VALO",
    # Energía
    "YPF", "PAM", "TGS", "TGSU", "PAMP",
    # Utilities
    "CEPU", "EDN",
    # Materiales
    "TXAR", "ALUA", "LOMA", "HARG",
    # Telecom
    "TECO2",
    # Agro / Otros
    "CRES", "BYMA", "MIRG",
]

SECTOR_MAP = {
    "GGAL": "Bancos", "BMA": "Bancos", "BBAR": "Bancos",
    "SUPV": "Bancos", "VALO": "Bancos",
    "YPF": "Energía", "PAM": "Energía", "TGS": "Energía",
    "TGSU": "Energía", "PAMP": "Energía",
    "CEPU": "Utilities", "EDN": "Utilities",
    "TXAR": "Materiales", "ALUA": "Materiales",
    "LOMA": "Materiales", "HARG": "Materiales",
    "TECO2": "Telecom",
    "CRES": "Agro", "BYMA": "Financiero", "MIRG": "Otros",
}


class AlphaCastClient:
    """
    Obtiene datos fundamentales del Merval vía MCP AlphaCast.

    Usa Claude como intermediario para consultar el servidor MCP.
    Si el MCP no está disponible, cae a modo simulación (útil para testing).
    """

    MCP_URL = "https://mcp.alphacast.io"

    def __init__(
        self,
        api_key: Optional[str] = None,
        simulation_mode: bool = False,
        csv_path: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("ALPHACAST_API_KEY", "")
        self.simulation_mode = simulation_mode
        # Fuente CSV (export de Alphacast). Si está seteada, get_panel_data lee de ahí.
        self.csv_path = csv_path or os.getenv("ALPHACAST_CSV_PATH")
        # Solo instanciar Anthropic cuando se va a usar (no en simulación)
        self._client: Optional[Anthropic] = None

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def get_ticker_data(self, ticker: str) -> Optional[Dict]:
        """
        Devuelve datos fundamentales de un ticker.

        Returns:
            {
                "ticker": "GGAL",
                "sector": "Bancos",
                "price_usd": 5.03,
                "p_e_forward": 3.31,
                "p_bv": 1.29,
                "roe": 0.009,
                "margen_neto": 0.011,
                "ev_ebitda": 5.0,
                "market_cap_usd_billions": 8.1,
                "timestamp": "2026-06-07"
            }
        """
        if self.simulation_mode:
            return self._simulate(ticker)

        try:
            return self._fetch_via_mcp(ticker)
        except Exception as e:
            logger.error(f"Error fetching {ticker}: {e}")
            return None

    def get_panel_data(self, tickers: Optional[List[str]] = None) -> List[Dict]:
        """
        Obtiene datos de múltiples tickers. Por defecto usa PANEL_LIDER completo.

        Orden de fuentes:
          1. simulation_mode  → datos simulados
          2. csv_path seteado → CSV (export de Alphacast)
          3. caso contrario   → MCP AlphaCast vía Claude
        """
        if not self.simulation_mode and self.csv_path:
            return self._load_from_csv(tickers)

        tickers = tickers or PANEL_LIDER
        results = []
        for ticker in tickers:
            data = self.get_ticker_data(ticker)
            if data:
                data.setdefault("sector", SECTOR_MAP.get(ticker, "Otros"))
                if self.validate_data(data):
                    results.append(data)
                else:
                    logger.warning(f"Datos inválidos para {ticker}, descartado")
            else:
                logger.warning(f"Sin datos para {ticker}")
        logger.info(f"Panel: {len(results)}/{len(tickers)} tickers recuperados")
        return results

    def validate_data(self, data: Dict) -> bool:
        """
        Valida coherencia básica de los datos.
        """
        try:
            checks = [
                data.get("price_usd", 0) > 0,
                data.get("p_e_forward", -1) >= 0,
                0.05 <= data.get("p_bv", 0) <= 20,
                -2.0 <= data.get("roe", 0) <= 2.0,
            ]
            return all(checks)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Fuente CSV (export de Alphacast)
    # ------------------------------------------------------------------

    def _load_from_csv(self, tickers: Optional[List[str]] = None) -> List[Dict]:
        """
        Carga el panel desde un CSV exportado de Alphacast.

        Columnas esperadas: ticker, sector, price_usd, p_e_forward, p_bv,
        roe, margen_neto, ev_ebitda, market_cap_usd_billions.

        roe y margen_neto vienen como porcentaje (12.10 = 12.10%) y se
        convierten a decimal (0.121). Los valores 'NA'/''/None → 0.0.
        """
        import csv
        from datetime import date

        wanted = {t.upper() for t in tickers} if tickers else None
        results: List[Dict] = []

        with open(self.csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ticker = (row.get("ticker") or "").strip().upper()
                if not ticker or (wanted and ticker not in wanted):
                    continue

                data = {
                    "ticker": ticker,
                    "sector": (row.get("sector") or "").strip()
                    or SECTOR_MAP.get(ticker, "Otros"),
                    "price_usd": self._num(row.get("price_usd")),
                    "p_e_forward": self._num(row.get("p_e_forward")),
                    "p_bv": self._num(row.get("p_bv")),
                    "roe": self._num(row.get("roe")) / 100.0,
                    "margen_neto": self._num(row.get("margen_neto")) / 100.0,
                    "ev_ebitda": self._num(row.get("ev_ebitda")),
                    "market_cap_usd_billions": self._num(row.get("market_cap_usd_billions")),
                    "timestamp": str(date.today()),
                }

                if self.validate_data(data):
                    results.append(data)
                else:
                    logger.warning(f"Datos inválidos para {ticker} en CSV, descartado")

        logger.info(f"CSV: {len(results)} tickers cargados desde {self.csv_path}")
        return results

    @staticmethod
    def _num(value, default: float = 0.0) -> float:
        """Convierte un valor de celda a float; 'NA'/''/None → default."""
        if value is None:
            return default
        s = str(value).strip().replace("%", "").replace(",", "")
        if s == "" or s.upper() == "NA":
            return default
        try:
            return float(s)
        except ValueError:
            return default

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    @property
    def client(self) -> Anthropic:
        """Lazy init del cliente Anthropic."""
        if self._client is None:
            self._client = Anthropic()
        return self._client

    def _fetch_via_mcp(self, ticker: str) -> Optional[Dict]:
        """Llama a Claude con MCP AlphaCast para obtener datos del ticker."""

        prompt = f"""Usá MCP AlphaCast para obtener los siguientes datos fundamentales \
del ticker {ticker} que cotiza en el mercado argentino (Merval/BYMA).

Necesito exactamente estos campos:
- Precio actual en USD (tipo CCL o ADR)
- P/E Forward (price to earnings proyectado)
- P/BV (price to book value)
- ROE (return on equity, como decimal: 19.3% = 0.193)
- Margen neto (como decimal)
- EV/EBITDA
- Market Cap en miles de millones USD

Respondé ÚNICAMENTE con un JSON válido con estas keys exactas (sin texto adicional, sin markdown):
{{
  "ticker": "{ticker}",
  "price_usd": 0.0,
  "p_e_forward": 0.0,
  "p_bv": 0.0,
  "roe": 0.0,
  "margen_neto": 0.0,
  "ev_ebitda": 0.0,
  "market_cap_usd_billions": 0.0,
  "timestamp": "YYYY-MM-DD"
}}"""

        response = self.client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
            mcp_servers=[
                {
                    "type": "url",
                    "url": self.MCP_URL,
                    "name": "alphacast",
                    "authorization_token": self.api_key,
                }
            ],
        )

        raw = next(
            (b.text for b in response.content if hasattr(b, "text")), None
        )
        if not raw:
            return None

        # Limpiar posible markdown
        raw = raw.strip()
        for fence in ("```json", "```"):
            if raw.startswith(fence):
                raw = raw[len(fence):]
        if raw.endswith("```"):
            raw = raw[:-3]

        data = json.loads(raw.strip())
        data["sector"] = SECTOR_MAP.get(ticker, "Otros")
        return data

    def _simulate(self, ticker: str) -> Dict:
        """
        Devuelve datos simulados para testing sin credenciales.
        Basado en valores aproximados de junio 2026.
        """
        import random
        from datetime import date

        base = {
            "GGAL": {"price_usd": 5.03, "p_e_forward": 3.31, "p_bv": 1.29, "roe": 0.009, "margen_neto": 0.011, "ev_ebitda": 5.0, "market_cap_usd_billions": 8.1},
            "BMA":  {"price_usd": 4.80, "p_e_forward": 4.10, "p_bv": 1.45, "roe": 0.015, "margen_neto": 0.020, "ev_ebitda": 4.5, "market_cap_usd_billions": 3.2},
            "BBAR": {"price_usd": 3.50, "p_e_forward": 5.20, "p_bv": 1.10, "roe": 0.012, "margen_neto": 0.018, "ev_ebitda": 5.5, "market_cap_usd_billions": 2.1},
            "YPF":  {"price_usd": 18.00, "p_e_forward": 6.50, "p_bv": 0.85, "roe": 0.085, "margen_neto": 0.060, "ev_ebitda": 3.2, "market_cap_usd_billions": 7.0},
            "PAM":  {"price_usd": 55.00, "p_e_forward": 8.00, "p_bv": 1.20, "roe": 0.120, "margen_neto": 0.180, "ev_ebitda": 6.0, "market_cap_usd_billions": 11.0},
            "TGS":  {"price_usd": 9.00, "p_e_forward": 7.50, "p_bv": 1.80, "roe": 0.190, "margen_neto": 0.250, "ev_ebitda": 5.8, "market_cap_usd_billions": 4.5},
            "CEPU": {"price_usd": 4.20, "p_e_forward": 6.00, "p_bv": 1.00, "roe": 0.080, "margen_neto": 0.100, "ev_ebitda": 4.2, "market_cap_usd_billions": 1.8},
            "EDN":  {"price_usd": 1.80, "p_e_forward": 9.00, "p_bv": 0.90, "roe": 0.060, "margen_neto": 0.070, "ev_ebitda": 5.0, "market_cap_usd_billions": 0.9},
            "TXAR": {"price_usd": 1.50, "p_e_forward": 11.0, "p_bv": 0.70, "roe": 0.040, "margen_neto": 0.050, "ev_ebitda": 7.0, "market_cap_usd_billions": 1.2},
            "ALUA": {"price_usd": 1.10, "p_e_forward": 8.00, "p_bv": 0.95, "roe": 0.070, "margen_neto": 0.080, "ev_ebitda": 4.8, "market_cap_usd_billions": 1.5},
        }

        defaults = {"price_usd": 2.50, "p_e_forward": 7.0, "p_bv": 1.0, "roe": 0.08, "margen_neto": 0.10, "ev_ebitda": 5.0, "market_cap_usd_billions": 1.0}
        d = base.get(ticker, defaults).copy()

        # Pequeño ruido para simular variación diaria
        for k in ("price_usd", "p_e_forward", "p_bv", "roe"):
            d[k] = round(d[k] * random.uniform(0.97, 1.03), 4)

        return {
            "ticker": ticker,
            "sector": SECTOR_MAP.get(ticker, "Otros"),
            "timestamp": str(date.today()),
            **d,
        }
