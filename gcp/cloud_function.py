"""
cloud_function.py
-----------------
Entry point para GCP Cloud Functions.

Ejecuta el pipeline completo:
  1. Obtener datos del panel Merval vía MCP AlphaCast
  2. Analizar fundamentales
  3. Generar reporte Telegram + HTML
  4. Enviar a Telegram
  5. Guardar en Firestore (histórico)
  6. Notificar errores si los hay

Variables de entorno requeridas en GCP:
  ALPHACAST_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""

import json
import logging
import os
import sys
import tempfile
from datetime import datetime

import functions_framework
import pytz

# ---- Para que GCP encuentre src/ ----
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.alphacast_client import AlphaCastClient, PANEL_LIDER
from src.analyzer import FundamentalAnalyzer
from src.report_generator import ReportGenerator
from src.telegram_notifier import TelegramNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ART = pytz.timezone("America/Argentina/Buenos_Aires")


@functions_framework.http
def merval_analysis(request):
    """
    HTTP Cloud Function.
    Puede invocarse con GET (Cowork scheduler) o POST (manual/CI).

    Responde:
      200 → {"status": "ok", "tickers": N, "timestamp": "..."}
      500 → {"status": "error", "message": "..."}
    """
    logger.info("=== merval_analysis START ===")
    notifier = None

    try:
        # --- Credenciales ---
        alphacast_key  = os.environ["ALPHACAST_API_KEY"]
        telegram_token = os.environ["TELEGRAM_BOT_TOKEN"]
        telegram_chat  = os.environ["TELEGRAM_CHAT_ID"]

        notifier = TelegramNotifier(telegram_token, telegram_chat)

        # --- 1. Obtener datos ---
        logger.info("Fetching data from AlphaCast...")
        client = AlphaCastClient(api_key=alphacast_key)
        raw_data = client.get_panel_data(PANEL_LIDER)

        if not raw_data:
            raise RuntimeError("AlphaCast devolvió datos vacíos — abortando")

        logger.info(f"Datos OK: {len(raw_data)} tickers")

        # --- 2. Analizar ---
        analyzer = FundamentalAnalyzer()
        report   = analyzer.generate_report(raw_data)

        # --- 3. Generar reportes ---
        gen     = ReportGenerator()
        tg_msg  = gen.telegram_message(report)
        html    = gen.html_report(report)

        # --- 4. Enviar a Telegram ---
        sent = notifier.send_message(tg_msg, parse_mode="MarkdownV2")
        if not sent:
            raise RuntimeError("Fallo enviando mensaje a Telegram")

        # Enviar HTML como documento adjunto
        with tempfile.NamedTemporaryFile(
            suffix=".html", mode="w", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write(html)
            tmp_path = tmp.name

        notifier.send_document(
            tmp_path,
            caption=f"Reporte HTML · {report['analysis_date'][:10]}",
        )

        # --- 5. Guardar en Firestore ---
        _save_to_firestore(report)

        logger.info("=== merval_analysis END OK ===")
        return (
            json.dumps({
                "status": "ok",
                "tickers": len(raw_data),
                "timestamp": report["analysis_date"],
                "buy": report["summary"]["buy"],
                "hold": report["summary"]["hold"],
                "sell": report["summary"]["sell"],
                "avoid": report["summary"]["avoid"],
            }),
            200,
            {"Content-Type": "application/json"},
        )

    except KeyError as e:
        msg = f"Variable de entorno faltante: {e}"
        logger.error(msg)
        _safe_notify(notifier, msg)
        return json.dumps({"status": "error", "message": msg}), 500, {"Content-Type": "application/json"}

    except Exception as e:
        msg = str(e)
        logger.exception("Error en merval_analysis")
        _safe_notify(notifier, msg)
        return json.dumps({"status": "error", "message": msg}), 500, {"Content-Type": "application/json"}


# ------------------------------------------------------------------
# Helpers privados
# ------------------------------------------------------------------

def _save_to_firestore(report: dict) -> None:
    """Guarda el reporte en Firestore para histórico."""
    try:
        from google.cloud import firestore
        db  = firestore.Client()
        doc_id = report["analysis_date"].replace(":", "-").replace("+", "p")

        db.collection("merval_reports").document(doc_id).set({
            "timestamp":    report["analysis_date"],
            "summary":      report["summary"],
            "top_3":        report["top_3"],
            "alerts_count": len(report["alerts"]),
            "alerts":       report["alerts"],
        })
        logger.info(f"Firestore: documento {doc_id} guardado")
    except Exception as e:
        logger.warning(f"Firestore write falló (no crítico): {e}")


def _safe_notify(notifier, msg: str) -> None:
    if notifier:
        try:
            notifier.send_error(msg)
        except Exception:
            pass
