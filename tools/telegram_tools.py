import re
import os
from pathlib import Path
from typing import Optional

from telethon.sync import TelegramClient
from telethon.tl.types import Message

from utils.config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_PASSWORD
from utils.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent

_client: Optional[TelegramClient] = None
_connected = False


def _session_path() -> str:
    safe = re.sub(r"[^a-zA-Z0-9]", "_", TELEGRAM_PHONE)
    return str(BASE_DIR / f"telegram_{safe}.session")


def _get_client() -> TelegramClient:
    global _client
    if _client is None:
        _client = TelegramClient(_session_path(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    return _client


def _code_callback() -> str:
    import sys
    logger.info("📲 Telegram necesita verificación")
    if not sys.stdin or not sys.stdin.isatty():
        raise RuntimeError(
            "Telegram requiere código de verificación pero no hay terminal interactiva.\n"
            "Ejecuta desde una terminal o borra el archivo .session y usa run.sh"
        )
    print("\n=== 📲 Telegram: Código de verificación ===")
    code = input(f"Código enviado a {TELEGRAM_PHONE}: ").strip()
    return code


def _ensure_connected():
    global _connected
    if _connected:
        return
    client = _get_client()
    if not client.is_connected():
        logger.info(f"Conectando a Telegram como {TELEGRAM_PHONE} ...")
        client.start(
            phone=TELEGRAM_PHONE,
            password=TELEGRAM_PASSWORD or None,
            code_callback=_code_callback,
        )
    _connected = True
    logger.info("Telegram conectado")


def _resolve(entity: str) -> str:
    """Convert a fuzzy name to a resolvable entity string."""
    e = entity.strip()
    if e.startswith("@"):
        return e
    if re.match(r"^\+?\d{6,15}$", e):
        return e
    return e


def telegram_get_me() -> str:
    _ensure_connected()
    me = _get_client().get_me()
    return f"Usuario: {me.first_name} {me.last_name or ''} (@{me.username or 'sin username'}) ID: {me.id}"


def telegram_get_dialogs(limit: int = 20) -> str:
    _ensure_connected()
    dialogs = _get_client().get_dialogs(limit=limit)
    lines = []
    for d in dialogs:
        name = d.name or "(sin nombre)"
        unread = d.unread_count
        lines.append(f"- {name} (ID: {d.id}) — {unread} no leídos")
    return "\n".join(lines) if lines else "No hay diálogos."


def telegram_get_messages(entity: str, limit: int = 10) -> str:
    _ensure_connected()
    resolved = _get_client().get_entity(_resolve(entity))
    messages = _get_client().get_messages(resolved, limit=limit)
    if not messages:
        return f"No hay mensajes en {entity}."
    lines = []
    for m in messages:
        sender = m.sender_id or "?"
        date = m.date.strftime("%d/%m %H:%M") if m.date else ""
        text = (m.text or "[media]")[:200]
        lines.append(f"[{date}] {sender}: {text}")
    return "\n".join(lines)


def telegram_send_message(entity: str, message: str) -> str:
    _ensure_connected()
    resolved = _get_client().get_entity(_resolve(entity))
    sent = _get_client().send_message(resolved, message)
    return f"Mensaje enviado a {entity} (ID: {sent.id})"


def telegram_send_file(entity: str, file_path: str, caption: str = "") -> str:
    _ensure_connected()
    if not os.path.exists(file_path):
        return f"Error: archivo {file_path} no existe"
    resolved = _get_client().get_entity(_resolve(entity))
    sent = _get_client().send_file(resolved, file_path, caption=caption or None)
    return f"Archivo enviado a {entity} (ID: {sent.id})"


def telegram_search_messages(entity: str, query: str, limit: int = 20) -> str:
    _ensure_connected()
    resolved = _get_client().get_entity(_resolve(entity))
    messages = _get_client().get_messages(resolved, search=query, limit=limit)
    if not messages:
        return f"No se encontraron mensajes con '{query}' en {entity}."
    lines = []
    for m in messages:
        date = m.date.strftime("%d/%m %H:%M") if m.date else ""
        sender = m.sender_id or "?"
        text = (m.text or "[media]")[:200]
        lines.append(f"[{date}] {sender}: {text}")
    return "\n".join(lines)


def telegram_read_all(entity: str) -> str:
    _ensure_connected()
    resolved = _get_client().get_entity(_resolve(entity))
    _get_client().send_read_acknowledge(resolved)
    return f"Mensajes marcados como leídos en {entity}."


def telegram_download_media(entity: str, message_id: int, out_dir: str = "/tmp") -> str:
    _ensure_connected()
    resolved = _get_client().get_entity(_resolve(entity))
    msg: Message = _get_client().get_messages(resolved, ids=message_id)
    if not msg or not msg.media:
        return f"El mensaje {message_id} no tiene media."
    path = _get_client().download_media(msg, file=out_dir)
    return f"Media descargado en: {path}"


def telegram_export_chat(entity: str, limit: int = 50, outfile: str = "") -> str:
    _ensure_connected()
    if not outfile:
        safe = re.sub(r"[^a-zA-Z0-9]", "_", entity)
        outfile = str(BASE_DIR / f"telegram_export_{safe}.txt")
    resolved = _get_client().get_entity(_resolve(entity))
    messages = _get_client().get_messages(resolved, limit=limit)
    with open(outfile, "w", encoding="utf-8") as f:
        for m in reversed(messages):
            date = m.date.strftime("%Y-%m-%d %H:%M:%S") if m.date else "?"
            sender = m.sender_id or "?"
            text = m.text or "[media]"
            f.write(f"[{date}] {sender}: {text}\n")
    return f"Chat exportado a {outfile} ({len(messages)} mensajes)"
