import time
import threading

import requests

from utils.config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID
from utils.logger import logger


TELEGRAM_API = "https://api.telegram.org/bot{token}"


class TelegramBot:
    def __init__(self, agent):
        self.agent = agent
        self.token = TELEGRAM_BOT_TOKEN
        self.allowed_user_id = TELEGRAM_USER_ID
        self._running = False
        self._thread = None
        self._last_update_id = 0

    def start(self):
        if not self.token or not self.allowed_user_id:
            logger.info(
                "Telegram bot no configurado: faltan TELEGRAM_BOT_TOKEN o "
                "TELEGRAM_USER_ID en .env"
            )
            return False

        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop, daemon=True, name="TelegramBot"
        )
        self._thread.start()
        logger.info(
            f"Telegram bot iniciado (user_id permitido: {self.allowed_user_id})"
        )
        return True

    def stop(self):
        self._running = False
        logger.info("Telegram bot detenido")

    def _poll_loop(self):
        while self._running:
            try:
                updates = self._get_updates()
                for update in updates:
                    self._handle_update(update)
            except requests.exceptions.Timeout:
                pass
            except Exception as e:
                logger.error(f"Error en bot Telegram: {e}")
                time.sleep(5)

    def _get_updates(self):
        url = f"{TELEGRAM_API.format(token=self.token)}/getUpdates"
        params = {
            "offset": self._last_update_id + 1,
            "timeout": 30,
            "allowed_updates": ["message"],
        }
        resp = requests.get(url, params=params, timeout=35)
        if resp.status_code == 200:
            return resp.json().get("result", [])
        logger.warning(
            f"Telegram API error {resp.status_code}: {resp.text[:200]}"
        )
        return []

    def _handle_update(self, update):
        update_id = update.get("update_id")
        if update_id is None:
            return
        if update_id <= self._last_update_id:
            return
        self._last_update_id = update_id

        message = update.get("message")
        if not message:
            return

        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")

        if not chat_id or not user_id:
            return

        if user_id != self.allowed_user_id:
            logger.security(
                f"Intento de acceso no autorizado: user_id={user_id}, "
                f"chat_id={chat_id}"
            )
            self._send_message(chat_id, "No tienes permiso para usar este bot.")
            return

        text = message.get("text", "")
        if not text:
            return

        logger.info(f"Telegram << {text[:100]}")
        response = self.agent.process(text)
        logger.info(f"Telegram >> {response[:100]}")
        self._send_message(chat_id, response)

    def _send_message(self, chat_id, text):
        MAX_LEN = 4000
        if len(text) > MAX_LEN:
            text = text[:MAX_LEN] + "\n\n[respuesta truncada por longitud]"

        url = f"{TELEGRAM_API.format(token=self.token)}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        try:
            resp = requests.post(url, json=data, timeout=10)
            if resp.status_code != 200:
                logger.error(
                    f"Error enviando mensaje: {resp.status_code} {resp.text[:200]}"
                )
        except Exception as e:
            logger.error(f"Error enviando mensaje Telegram: {e}")
