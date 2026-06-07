#!/usr/bin/env python
"""
run_analysis.py
---------------
Runner standalone del pipeline Merval Fundamentals (sin GCP Cloud Function).

Ejecuta:
  1. Obtener datos del panel vía AlphaCast (MCP + Claude)  — o simulación
  2. Analizar fundamentales → señales BUY/HOLD/SELL/AVOID
  3. Generar reporte Telegram (Markdown) + HTML
  4. Enviar a Telegram (salvo --no-send)

Uso:
  python run_analysis.py                      # real: requiere credenciales en .env
  python run_analysis.py --simulate           # datos simulados, sin credenciales
  python run_analysis.py --simulate --no-send # smoke test: imprime por stdout
  python run_analysis.py --html report.html   # además guarda el HTML

Variables de entorno (desde .env o el entorno del runner):
  ANTHROPIC_API_KEY   — para el cliente Anthropic que consulta el MCP AlphaCast
  ALPHACAST_API_KEY   — token del MCP AlphaCast
  TELEGRAM_BOT_TOKEN  — bot de Telegram
  TELEGRAM_CHAT_ID    — chat/grupo destino
"""

import argparse
import logging
import sys

from dotenv import load_dotenv

from src.alphacast_client import AlphaCastClient, PANEL_LIDER
from src.analyzer import FundamentalAnalyzer
from src.report_generator import ReportGenerator
from src.telegram_notifier import TelegramNotifier

# La consola de Windows usa cp1252 por defecto y rompe con emojis del reporte.
# Forzamos UTF-8 en stdout/stderr (no-op en Linux/CI, que ya es UTF-8).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("run_analysis")

# Mínimo de tickers con datos para considerar el reporte válido.
MIN_TICKERS = 10


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Runner del pipeline Merval Fundamentals"
    )
    p.add_argument(
        "--simulate", action="store_true",
        help="Usa datos simulados (no requiere credenciales de AlphaCast)",
    )
    p.add_argument(
        "--csv", metavar="PATH", default="data/merval_panel.csv",
        help="CSV con los datos del panel (export de Alphacast). Default: data/merval_panel.csv",
    )
    p.add_argument(
        "--no-send", action="store_true",
        help="No envía a Telegram; imprime el mensaje por stdout",
    )
    p.add_argument(
        "--html", metavar="PATH", default=None,
        help="Guarda el reporte HTML en PATH",
    )
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    load_dotenv()

    notifier = None
    try:
        # Falla temprano si faltan credenciales de Telegram (salvo --no-send).
        if not args.no_send:
            notifier = TelegramNotifier()

        # --- 1. Datos ---
        if args.simulate:
            logger.info("Obteniendo datos del panel (simulación)...")
            client = AlphaCastClient(simulation_mode=True)
        else:
            logger.info("Obteniendo datos del panel (CSV: %s)...", args.csv)
            client = AlphaCastClient(csv_path=args.csv)
        raw_data = client.get_panel_data(PANEL_LIDER)

        if len(raw_data) < MIN_TICKERS:
            raise RuntimeError(
                f"Solo {len(raw_data)}/{len(PANEL_LIDER)} tickers con datos "
                f"(mínimo {MIN_TICKERS}) — abortando"
            )
        logger.info("Datos OK: %d tickers", len(raw_data))

        # --- 2. Analizar ---
        report = FundamentalAnalyzer().generate_report(raw_data)

        # --- 3. Reportes ---
        gen = ReportGenerator()
        tg_msg = gen.telegram_message(report)
        if args.html:
            with open(args.html, "w", encoding="utf-8") as f:
                f.write(gen.html_report(report))
            logger.info("HTML guardado en %s", args.html)

        # --- 4. Enviar ---
        if args.no_send:
            print(tg_msg)
            logger.info("--no-send activo: mensaje no enviado a Telegram")
        else:
            if not notifier.send_message(tg_msg, parse_mode="MarkdownV2"):
                raise RuntimeError("Fallo enviando mensaje a Telegram")
            logger.info("Reporte enviado a Telegram")

        s = report["summary"]
        logger.info(
            "Resumen: total=%d BUY=%d HOLD=%d SELL=%d AVOID=%d",
            s["total"], s["buy"], s["hold"], s["sell"], s["avoid"],
        )
        return 0

    except Exception as e:
        logger.exception("Pipeline falló: %s", e)
        if notifier is not None:
            notifier.send_error(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
