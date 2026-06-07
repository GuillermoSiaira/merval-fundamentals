"""
telegram_notifier.py
--------------------
Envía mensajes y archivos a Telegram.

Requiere:
  TELEGRAM_BOT_TOKEN  → token del bot de BotFather
  TELEGRAM_CHAT_ID    → ID del grupo o chat destino
"""

import logging
import os
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}"


class TelegramNotifier:

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id   = chat_id   or os.getenv("TELEGRAM_CHAT_ID", "")

        if not self.bot_token or not self.chat_id:
            raise ValueError(
                "Falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID. "
                "Completá el .env o pasalos como argumentos."
            )

        self._base = f"https://api.telegram.org/bot{self.bot_token}"

    # ------------------------------------------------------------------
    # Públicos
    # ------------------------------------------------------------------

    def test_connection(self) -> bool:
        """Verifica que el bot esté activo."""
        try:
            r = requests.get(f"{self._base}/getMe", timeout=10)
            r.raise_for_status()
            info = r.json()["result"]
            logger.info(f"Bot OK: @{info.get('username')} ({info.get('first_name')})")
            return True
        except Exception as e:
            logger.error(f"Error conectando bot: {e}")
            return False

    def send_message(
        self,
        text: str,
        parse_mode: str = "MarkdownV2",
        disable_preview: bool = True,
    ) -> bool:
        """
        Envía mensaje de texto.

        Usa MarkdownV2 por defecto (compatible con caracteres especiales).
        Pasá parse_mode="Markdown" para Markdown clásico.
        """
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview,
        }
        try:
            r = requests.post(f"{self._base}/sendMessage", json=payload, timeout=15)
            if r.status_code != 200:
                logger.error(f"Telegram error {r.status_code}: {r.text[:200]}")
                # Reintentar sin parse_mode si falla por formato
                if parse_mode != "":
                    return self.send_message(text, parse_mode="", disable_preview=disable_preview)
                return False
            logger.info("Mensaje enviado a Telegram OK")
            return True
        except requests.RequestException as e:
            logger.error(f"Error enviando mensaje: {e}")
            return False

    def send_document(self, file_path: str, caption: str = "") -> bool:
        """Envía un archivo (HTML, PDF, etc.)."""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Archivo no encontrado: {file_path}")
            return False
        try:
            with open(path, "rb") as f:
                r = requests.post(
                    f"{self._base}/sendDocument",
                    data={"chat_id": self.chat_id, "caption": caption[:1024]},
                    files={"document": (path.name, f)},
                    timeout=30,
                )
            if r.status_code != 200:
                logger.error(f"Telegram document error {r.status_code}: {r.text[:200]}")
                return False
            logger.info(f"Documento '{path.name}' enviado OK")
            return True
        except Exception as e:
            logger.error(f"Error enviando documento: {e}")
            return False

    def send_error(self, error_msg: str) -> None:
        """Notifica un error al chat (sin excepciones)."""
        try:
            self.send_message(
                f"❌ *Error en análisis Merval*\n\n`{error_msg[:500]}`",
                parse_mode="Markdown",
            )
        except Exception:
            pass  # Silenciar errores en el handler de errores


# --- CLI rápido ---
if __name__ == "__main__":
    notifier = TelegramNotifier()
    if notifier.test_connection():
        notifier.send_message(
            "✅ *Merval Fundamentals* — sistema operativo\\. Prueba exitosa\\.",
            parse_mode="MarkdownV2",
        )
        print("✅ Mensaje de prueba enviado")
    else:
        print("❌ Falló la conexión — revisá TELEGRAM_BOT_TOKEN")
